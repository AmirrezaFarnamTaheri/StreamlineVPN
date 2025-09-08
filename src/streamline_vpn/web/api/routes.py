# isort: skip_file
"""API Routes
==========

FastAPI route definitions for the StreamlineVPN API.
"""

import asyncio
import json
import os
import threading
import time
import yaml
import ipaddress
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urlsplit, urlunsplit

from fastapi import (
    Body,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...__main__ import main as run_pipeline_main
from ...core.source_manager import SourceManager
from ...core.merger import StreamlineVPNMerger
from ...utils.logging import get_logger
from .auth import AuthenticationService
from .models import (
    ConnectionRequest,
    ConnectionResponse,
    LoginRequest,
    LoginResponse,
    ServerRecommendationRequest,
    ServerRecommendationResponse,
    User,
    VPNStatusResponse,
    WebSocketMessage,
)
from .websocket import WebSocketManager

logger = get_logger(__name__)

# Global instances (would be injected in production)
_auth_service: Optional[AuthenticationService] = None
_websocket_manager: Optional[WebSocketManager] = None

# Simple cache for VPN status
_vpn_status_cache: Optional[VPNStatusResponse] = None
_vpn_status_cache_time: float = 0.0
_vpn_status_cache_lock = threading.Lock()

# Store job status and tasks
job_status: Dict[str, Dict[str, Any]] = {}
job_tasks: Dict[str, Any] = {}

# Lazy-initialized managers
_source_manager: Optional[SourceManager] = None
_merger_for_stats: Optional[StreamlineVPNMerger] = None


def find_config_path() -> Path | None:
    """Locate the sources configuration file using common strategies."""
    if config_env := os.getenv("APP_CONFIG_PATH"):
        path = Path(config_env)
        if path.is_file():
            return path

    cwd_path = Path.cwd() / "config" / "sources.yaml"
    if cwd_path.is_file():
        return cwd_path

    package_path = (
        Path(__file__).parent.parent.parent / "config" / "sources.yaml"
    )
    if package_path.is_file():
        return package_path
    return None


def _get_source_manager() -> SourceManager:
    global _source_manager
    if _source_manager is None:
        cfg = find_config_path() or Path("config/sources.yaml")
        _source_manager = SourceManager(str(cfg))
    return _source_manager


def _get_merger_for_stats() -> StreamlineVPNMerger:
    global _merger_for_stats
    if _merger_for_stats is None:
        cfg = find_config_path() or Path("config/sources.yaml")
        _merger_for_stats = StreamlineVPNMerger(config_path=str(cfg))
    return _merger_for_stats


def is_ipv6_address(host: str) -> bool:
    """Return True if *host* is a valid IPv6 address."""
    try:
        ipaddress.IPv6Address(host)
        return True
    except ipaddress.AddressValueError:
        return False


def set_auth_service(auth_service: AuthenticationService) -> None:
    """Set global authentication service."""
    global _auth_service
    _auth_service = auth_service


def set_websocket_manager(websocket_manager: WebSocketManager) -> None:
    """Set global WebSocket manager."""
    global _websocket_manager
    _websocket_manager = websocket_manager


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> User:
    """Get current authenticated user."""
    if not _auth_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not initialized",
        )

    user = _auth_service.verify_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return user


def setup_routes(
    app,
    auth_service: AuthenticationService,
    websocket_manager: WebSocketManager,
) -> None:
    """Setup API routes.

    Args:
        app: FastAPI application instance
        auth_service: Authentication service
        websocket_manager: WebSocket manager
    """
    set_auth_service(auth_service)
    set_websocket_manager(websocket_manager)

    async def _broadcast_job_update(job_id: str) -> None:
        """Broadcast current job status to all connected clients."""
        try:
            status_info = job_status.get(job_id)
            if not status_info:
                return
            if websocket_manager is None:
                return
            await websocket_manager.broadcast_message(
                WebSocketMessage(
                    type="job_update",
                    data={"job_id": job_id, **status_info},
                    timestamp=datetime.utcnow().isoformat(),
                )
            )
        except Exception:
            # Best-effort; do not fail the request path on WS errors
            pass

    # Processing routes for control panel
    @app.post("/api/process")
    async def process_configurations(request: dict = Body(...)):
        """Process VPN configurations from control panel."""
        try:
            from streamline_vpn.core.merger import StreamlineVPNMerger

            config_path = request.get("config_path", "config/sources.yaml")
            output_formats = request.get(
                "formats", ["json", "clash", "singbox"]
            )
            allowed_formats = {"json", "clash", "singbox"}
            if not isinstance(output_formats, list) or not all(
                isinstance(f, str) for f in output_formats
            ):
                raise HTTPException(
                    status_code=400,
                    detail="'formats' must be a list of strings",
                )
            normalized_formats = [
                fmt.strip().lower() for fmt in output_formats
            ]
            unknown = [
                f for f in normalized_formats if f not in allowed_formats
            ]
            output_formats = [
                f for f in normalized_formats if f in allowed_formats
            ]
            if unknown:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Unknown formats: "
                        f"{', '.join(sorted(set(unknown)))}. "
                        f"Allowed: {', '.join(sorted(allowed_formats))}"
                    ),
                )
            if not output_formats:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "'formats' must include at least one of: "
                        f"{', '.join(sorted(allowed_formats))}"
                    ),
                )

            merger = StreamlineVPNMerger(config_path=config_path)
            await merger.initialize()

            result = await merger.process_all(
                output_dir="output", formats=output_formats
            )

            return {
                "success": True,
                "message": "Processing completed successfully",
                "statistics": result,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Processing failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Processing failed",
            )

    @app.get("/api/statistics")
    async def get_statistics():
        """Get processing statistics."""
        try:
            sm = _get_source_manager()
            source_stats = sm.get_source_statistics()
            return {
                "total_configs": 0,
                "successful_sources": source_stats.get("active_sources", 0),
                "success_rate": min(
                    1.0,
                    max(0.0, source_stats.get("average_reputation", 0.0)),
                ),
                "avg_quality": source_stats.get("average_reputation", 0.0),
            }
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to provide statistics: %s", e)
            return {
                "total_configs": 0,
                "successful_sources": 0,
                "success_rate": 0.0,
                "avg_quality": 0.0,
            }

    # Mirror statistics on v1 namespace
    @app.get("/api/v1/statistics")
    async def get_statistics_v1():
        return await get_statistics()

    @app.get("/api/configurations")
    async def get_configurations():
        """Get processed configurations."""
        # Return actual configurations from database or cache
        return []

    # v1 configurations endpoint with simple pagination contract
    @app.get("/api/v1/configurations")
    async def get_configurations_v1(limit: int = 100, offset: int = 0):
        if limit < 1 or limit > 1000 or offset < 0:
            raise HTTPException(status_code=400, detail="Invalid pagination")
        # TODO: integrate with storage when available
        return {"total": 0, "limit": limit, "offset": offset, "configurations": []}

    @app.get("/api/sources")
    async def get_sources():
        """Get configured sources."""
        try:
            config_path = find_config_path()
            if config_path is None or not config_path.is_file():
                logger.warning("Sources config file not found")
                raise HTTPException(
                    status_code=404, detail="Sources config file not found"
                )

            with config_path.open("r", encoding="utf-8") as f:
                try:
                    loaded = yaml.safe_load(f)
                except yaml.YAMLError:
                    logger.exception("Failed to parse sources.yaml")
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid YAML format in sources configuration",
                    )
                if loaded is None:
                    raise HTTPException(
                        status_code=400, detail="Sources config is empty"
                    )
                if not isinstance(loaded, dict):
                    raise HTTPException(
                        status_code=400,
                        detail="Sources config must be a mapping",
                    )
                sources_data = loaded

            tiers = sources_data.get("sources") or {}
            if not isinstance(tiers, dict):
                tiers = {}

            sources_list = []
            seen_urls = set()
            for tier_name, tier_data in tiers.items():
                tier_str = str(tier_name)

                if isinstance(tier_data, list):
                    url_list = [
                        u for u in tier_data if isinstance(u, (str, dict))
                    ]
                elif isinstance(tier_data, dict):
                    urls = tier_data.get("urls")
                    url_list = (
                        urls
                        if isinstance(urls, list)
                        else ([urls] if urls else [])
                    )
                    url_list = [
                        u for u in url_list if isinstance(u, (str, dict))
                    ]
                else:
                    url_list = []

                for source_config in url_list or []:
                    url = None
                    if isinstance(source_config, dict):
                        url = source_config.get("url")
                    elif isinstance(source_config, str):
                        url = source_config

                    if isinstance(url, str):
                        url = url.strip()

                    if (
                        not url
                        or not isinstance(url, str)
                        or not (
                            url.lower().startswith("http://")
                            or url.lower().startswith("https://")
                        )
                    ):
                        continue

                    try:
                        parts = urlsplit(url)
                    except ValueError as e:
                        logger.warning(
                            "Skipping invalid URL in sources: %s (%s)", url, e
                        )
                        continue
                    if parts.username or parts.password:
                        logger.warning(
                            "Skipping URL with credentials in sources: %s", url
                        )
                        continue

                    norm_url = url.strip()
                    # Normalize scheme and host for deduplication
                    try:
                        parts = urlsplit(norm_url)
                        norm_host = (
                            parts.hostname.lower() if parts.hostname else ""
                        )
                        norm_scheme = (parts.scheme or "").lower()
                        is_ipv6 = is_ipv6_address(norm_host)
                        host_for_netloc = (
                            f"[{norm_host}]" if is_ipv6 else norm_host
                        )
                        norm_netloc = host_for_netloc
                        if parts.port:
                            norm_netloc = f"{host_for_netloc}:{parts.port}"
                        normalized = urlunsplit(
                            (
                                norm_scheme,
                                norm_netloc,
                                parts.path or "",
                                parts.query or "",
                                parts.fragment or "",
                            )
                        )
                    except Exception:
                        normalized = norm_url
                    if normalized in seen_urls:
                        continue
                    seen_urls.add(normalized)

                    sources_list.append(
                        {
                            "url": normalized,
                            "status": "active",  # Placeholder
                            "configs": 0,  # Placeholder
                            "tier": tier_str,
                        }
                    )
            return {"sources": sources_list}
        except HTTPException:
            raise
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse sources: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to load sources"
            )
        except Exception as e:
            logger.error(f"Failed to load sources: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to load sources"
            )

    # v1 alias for sources endpoint used by frontend
    @app.get("/api/v1/sources")
    async def get_sources_v1():
        return await get_sources()

    # Authentication routes
    @app.post("/api/v1/auth/login", response_model=LoginResponse)
    async def login(request: LoginRequest):
        """Handle user login."""
        user = await auth_service.authenticate_user(
            request.username, request.password
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        access_token = auth_service.generate_access_token(user)
        refresh_token = auth_service.generate_refresh_token(user)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "tier": user.tier.value,
            },
        )

    @app.post("/api/v1/auth/refresh")
    async def refresh_token(
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    ):
        """Handle token refresh."""
        new_token = auth_service.refresh_access_token(credentials.credentials)
        if not new_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_in": 3600,
        }

    # Server routes
    @app.get("/api/v1/servers")
    async def get_servers(
        current_user: User = Depends(get_current_user),
        protocol: Optional[str] = None,
        location: Optional[str] = None,
        min_quality: float = 0.0,
        limit: int = 100,
        offset: int = 0,
    ):
        """Get available VPN servers with filtering and pagination from processed configs."""
        try:
            if limit <= 0 or limit > 500 or offset < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid pagination parameters",
                )

            merger = get_merger()
            configs = await merger.get_configurations()

            def to_server_dict(c) -> Dict[str, Any]:
                return {
                    "id": getattr(c, "id", None) or f"{c.protocol.value}-{c.server}-{c.port}",
                    "server": c.server,
                    "protocol": c.protocol.value,
                    "location": c.metadata.get("location", "unknown"),
                    "port": c.port,
                    "quality": getattr(c, "quality_score", 0.0),
                    "status": "active",
                }

            servers: List[Dict[str, Any]] = [to_server_dict(c) for c in configs]

            if protocol:
                servers = [s for s in servers if s["protocol"] == protocol]
            if location:
                servers = [s for s in servers if s["location"] == location]
            if min_quality > 0:
                servers = [s for s in servers if float(s.get("quality", 0.0)) >= float(min_quality)]

            total = len(servers)
            servers = servers[offset:offset + limit]

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "servers": servers,
            }
        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error fetching servers: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch servers",
            )

    @app.post(
        "/api/v1/servers/recommendations",
        response_model=ServerRecommendationResponse,
    )
    async def get_server_recommendations(
        request: ServerRecommendationRequest,
        current_user: User = Depends(get_current_user),
    ):
        """Get server recommendations based on filters and quality."""
        merger = get_merger()
        configs = await merger.get_configurations()

        region = (request.region or "").strip() or None
        proto = (request.protocol or "").strip() or None
        max_latency = request.max_latency if request.max_latency is not None else None

        candidates = []
        for c in configs:
            if proto and c.protocol.value != proto:
                continue
            if region and c.metadata.get("region") != region and c.metadata.get("location") != region:
                continue
            candidates.append(c)

        candidates.sort(key=lambda x: getattr(x, "quality_score", 0.0), reverse=True)
        top = candidates[:10]

        servers = [
            {
                "id": getattr(c, "id", None) or f"{c.protocol.value}-{c.server}-{c.port}",
                "name": c.metadata.get("name") or c.server,
                "region": c.metadata.get("region") or c.metadata.get("location") or "unknown",
                "protocol": c.protocol.value,
                "performance_score": getattr(c, "quality_score", 0.0),
            }
            for c in top
        ]

        # Simple quality-based summary
        quality_prediction = {
            "predicted_latency": 50.0 if max_latency is None else min(50.0, max_latency),
            "bandwidth_estimate": 100.0,
            "reliability_score": 0.9,
            "confidence": 0.8,
            "quality_grade": "A" if servers and servers[0]["performance_score"] >= 0.8 else "B",
        }

        recommendations = ["Choose highest performance_score", "Prefer nearby region if available"]

        return ServerRecommendationResponse(
            servers=servers,
            recommendations=recommendations,
            quality_prediction=quality_prediction,
        )

    # Connection routes
    @app.post("/api/v1/connections", response_model=ConnectionResponse)
    async def create_connection(
        request: ConnectionRequest,
        current_user: User = Depends(get_current_user),
    ):
        """Create VPN connection (placeholder integrates with external connector in production)."""
        connection_id = f"conn_{current_user.id}_{int(time.time())}"

        # Lookup config details for the requested server id
        merger = get_merger()
        configs = await merger.get_configurations()
        found = None
        for c in configs:
            cid = getattr(c, "id", None) or f"{c.protocol.value}-{c.server}-{c.port}"
            if cid == request.server_id:
                found = c
                break

        server_info = {
            "id": request.server_id,
            "name": getattr(found, "server", None) or "unknown",
            "host": getattr(found, "server", None) or "unknown",
            "port": getattr(found, "port", None) or 0,
            "protocol": request.protocol or (found.protocol.value if found else None),
            "region": (found.metadata.get("region") if found else None) or (found.metadata.get("location") if found else None) if found else None,
        }

        return ConnectionResponse(
            connection_id=connection_id,
            status="connected",
            server=server_info,
            estimated_latency=50.0,
        )

    @app.get("/api/v1/connections/{connection_id}")
    async def get_connection(
        connection_id: str, current_user: User = Depends(get_current_user)
    ):
        """Get connection details."""
        # Mock connection data
        return {
            "id": connection_id,
            "status": "connected",
            "server": {
                "id": "server_1",
                "name": "US East Premium",
                "region": "us-east",
                "protocol": "vless",
            },
            "connected_at": "2024-01-01T10:00:00Z",
            "session_duration": 3600,
            "bytes_uploaded": 1024000,
            "bytes_downloaded": 2048000,
        }

    @app.delete("/api/v1/connections/{connection_id}")
    async def disconnect_connection(
        connection_id: str, current_user: User = Depends(get_current_user)
    ):
        """Disconnect VPN connection."""
        return {"status": "disconnected"}

    # Status routes
    @app.get("/api/v1/status", response_model=VPNStatusResponse)
    async def get_vpn_status():
        """Get VPN status without authentication."""
        global _vpn_status_cache, _vpn_status_cache_time

        now = time.time()
        with _vpn_status_cache_lock:
            if _vpn_status_cache and now - _vpn_status_cache_time < 5:
                return _vpn_status_cache

        result = VPNStatusResponse(
            connected=True,
            server={
                "id": "server",
                "name": "Generic Server",
                "region": "us-east",
                "protocol": "vless",
            },
            bandwidth={"upload": 10.0, "download": 50.0},
            latency=50.0,
            session_duration=3600,
            bytes_transferred={"upload": 1024000, "download": 2048000},
        )

        with _vpn_status_cache_lock:
            _vpn_status_cache = result
            _vpn_status_cache_time = now
        return result

    # WebSocket route
    @app.websocket("/ws/{user_id}")
    async def websocket_endpoint(websocket: WebSocket, user_id: str):
        """WebSocket endpoint for real-time updates."""
        await websocket_manager.connect(websocket, user_id)

        MAX_MSG_BYTES = 256 * 1024  # 256 KiB limit

        try:
            while True:
                data = await websocket.receive_text()
                if len(data.encode("utf-8", "ignore")) > MAX_MSG_BYTES:
                    await websocket.send_text('{"error":"message_too_large"}')
                    await websocket.close(code=1009)  # Message too big
                    break
                try:
                    message_data = json.loads(data)
                except Exception:
                    await websocket.send_text('{"error":"invalid_json"}')
                    continue
                await websocket_manager.handle_message(
                    websocket, user_id, message_data
                )
        except WebSocketDisconnect:
            await websocket_manager.disconnect(user_id)
        except Exception as e:
            logger.error(f"WebSocket error for {user_id}: {e}", exc_info=True)
            await websocket_manager.disconnect(user_id)

    # Health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
        }

    # Metrics endpoint
    @app.get("/metrics")
    async def get_metrics():
        """Get Prometheus metrics."""
        body = (
            "# StreamlineVPN Metrics\n# (metrics would be implemented here)\n"
        )
        return PlainTextResponse(
            content=body,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    # Pipeline routes
    @app.post("/api/v1/pipeline/run")
    async def run_pipeline(
        config_path: str = Body("config/sources.yaml"),
        output_dir: str = Body("output"),
        formats: List[str] = Body(["json", "clash"]),
    ):
        """Run the VPN configuration pipeline."""
        try:
            allowed_formats = {"json", "clash", "singbox"}
            if not formats or any(f not in allowed_formats for f in formats):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Invalid formats. Allowed: "
                        f"{', '.join(sorted(allowed_formats))}"
                    ),
                )
            if not Path(config_path).exists():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Configuration file not found: {config_path}",
                )

            Path(output_dir).mkdir(parents=True, exist_ok=True)

            import uuid

            job_id = str(uuid.uuid4())
            job_status[job_id] = {"status": "queued", "progress": 0, "message": "Queued"}
            asyncio.create_task(_broadcast_job_update(job_id))

            async def run_async():
                job_status[job_id] = {"status": "running", "progress": 0, "message": "Running"}
                await _broadcast_job_update(job_id)
                try:
                    await run_pipeline_main(config_path, output_dir, formats)
                    job_status[job_id] = {
                        "status": "completed",
                        "progress": 100,
                        "message": "Completed",
                    }
                    await _broadcast_job_update(job_id)
                    logger.info(
                        "Pipeline job %s completed successfully",
                        job_id,
                    )
                except Exception as e:  # noqa: BLE001
                    job_status[job_id] = {
                        "status": "failed",
                        "error": str(e),
                        "message": "Failed",
                    }
                    await _broadcast_job_update(job_id)
                    logger.error("Pipeline job %s failed: %s", job_id, e)

            task = asyncio.create_task(run_async())
            job_tasks[job_id] = task

            return {
                "status": "success",
                "message": "Pipeline started successfully",
                "job_id": job_id,
            }
        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error running pipeline: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to run pipeline: {e}",
            )

    @app.get("/api/v1/pipeline/status/{job_id}")
    async def get_pipeline_status(job_id: str):
        """Get pipeline job status."""
        status_info = job_status.get(job_id)
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )
        return {"job_id": job_id, **status_info}

    # Expanded pipeline.run to support more formats and job progress messages
    @app.post("/api/v1/pipeline/run")
    async def run_pipeline_v1(
        config_path: str = Body("config/sources.yaml"),
        output_dir: str = Body("output"),
        formats: List[str] = Body(["json", "clash", "singbox", "base64", "raw", "csv"]),
    ):
        """Run the VPN configuration pipeline (v1)."""
        try:
            allowed_formats = {"json", "clash", "singbox", "base64", "raw", "csv"}
            norm_formats = [str(f).strip().lower() for f in formats or []]
            invalid = [f for f in norm_formats if f not in allowed_formats]
            if not norm_formats or invalid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        ("Invalid formats: " + ", ".join(sorted(set(invalid))) + ". ") if invalid else ""
                    )
                    + "Allowed: "
                    + ", ".join(sorted(allowed_formats)),
                )
            if not Path(config_path).exists():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Configuration file not found: {config_path}",
                )

            Path(output_dir).mkdir(parents=True, exist_ok=True)

            import uuid

            job_id = str(uuid.uuid4())
            job_status[job_id] = {"status": "queued", "progress": 0, "message": "Job queued"}
            asyncio.create_task(_broadcast_job_update(job_id))

            async def run_async():
                job_status[job_id] = {"status": "running", "progress": 5, "message": "Starting pipeline"}
                await _broadcast_job_update(job_id)
                try:
                    # Delegate to main pipeline entry
                    await run_pipeline_main(config_path, output_dir, norm_formats)
                    job_status[job_id] = {
                        "status": "completed",
                        "progress": 100,
                        "message": "Pipeline completed",
                    }
                    await _broadcast_job_update(job_id)
                    logger.info("Pipeline job %s completed successfully", job_id)
                except Exception as e:  # noqa: BLE001
                    job_status[job_id] = {
                        "status": "failed",
                        "error": str(e),
                        "message": "Pipeline failed",
                    }
                    await _broadcast_job_update(job_id)
                    logger.error("Pipeline job %s failed: %s", job_id, e)

            task = asyncio.create_task(run_async())
            job_tasks[job_id] = task

            return {
                "status": "success",
                "message": "Pipeline started successfully",
                "job_id": job_id,
            }
        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error running pipeline (v1): {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to run pipeline: {e}",
            )

    # Sources v1 endpoints
    @app.post("/api/v1/sources/add")
    async def add_source(request: Dict[str, Any] = Body(...)):
        try:
            url = (request.get("url") or "").strip()
            if not url:
                raise HTTPException(status_code=400, detail="'url' is required")
            sm = _get_source_manager()
            metadata = await sm.add_source(url)
            return {
                "message": "Source added",
                "url": metadata.url,
                "tier": metadata.tier.value,
            }
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to add source: %s", e)
            raise HTTPException(status_code=500, detail="Failed to add source")
