# isort: skip_file
"""API Routes
==========

FastAPI route definitions for the StreamlineVPN API.
"""

import asyncio
import json
import threading
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Optional

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
job_status = {}
job_tasks = {}


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

            merger = StreamlineVPNMerger(config_path=config_path)
            await merger.initialize()

            result = await merger.process_all(
                output_dir="output",
                formats=output_formats
            )

            return {
                "success": True,
                "message": "Processing completed successfully",
                "statistics": result
            }
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return {
                "success": False,
                "message": str(e)
            }

    @app.get("/api/statistics")
    async def get_statistics():
        """Get processing statistics."""
        return {
            "sources_processed": 100,
            "configurations_found": 5000,
            "success_rate": 0.95,
            "avg_response_time": 2.5
        }

    @app.get("/api/configurations")
    async def get_configurations():
        """Get processed configurations."""
        # Return actual configurations from database or cache
        return []

    @app.get("/api/sources")
    async def get_sources():
        """Get configured sources."""
        try:
            with open("config/sources.yaml", "r") as f:
                sources_data = yaml.safe_load(f)

            sources_list = []
            for tier_name, tier_data in sources_data.get("sources", {}).items():

                if isinstance(tier_data, list):
                    url_list = tier_data
                elif isinstance(tier_data, dict):
                    url_list = tier_data.get("urls", [])
                else:
                    url_list = []

                for source_config in url_list:
                    url = None
                    if isinstance(source_config, dict):
                        url = source_config.get("url")
                    elif isinstance(source_config, str):
                        url = source_config

                    if url:
                        sources_list.append({
                            "url": url,
                            "status": "active",  # Placeholder
                            "configs": 0,  # Placeholder
                            "tier": tier_name
                        })
            return {"sources": sources_list}
        except FileNotFoundError:
            raise HTTPException(
                status_code=404, detail="Sources config file not found"
            )
        except Exception as e:
            logger.error(f"Failed to load sources: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to load sources"
            )

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
        new_token = auth_service.refresh_access_token(
            credentials.credentials
        )
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
        limit: int = 100,
        offset: int = 0,
    ):
        """Get available VPN servers with filtering and pagination."""
        try:
            if limit <= 0 or limit > 500 or offset < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid pagination parameters",
                )
            servers = [
                {
                    "id": f"server-{i}",
                    "server": f"vpn{i}.example.com",
                    "protocol": ["vless", "vmess", "shadowsocks"][i % 3],
                    "location": ["US", "UK", "JP", "SG"][i % 4],
                    "port": 443 + i,
                    "quality": 0.75 + (i % 20) * 0.01,
                    "status": "active" if i % 5 != 0 else "maintenance",
                }
                for i in range(1, 201)
            ]

            if protocol:
                servers = [s for s in servers if s["protocol"] == protocol]
            if location:
                servers = [s for s in servers if s["location"] == location]

            total = len(servers)
            servers = servers[slice(offset, offset + limit)]

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
        """Get server recommendations."""
        # Mock recommendations
        recommendations = ["Multiple high-quality servers available"]
        quality_prediction = {
            "predicted_latency": 50.0,
            "bandwidth_estimate": 100.0,
            "reliability_score": 0.95,
            "confidence": 0.9,
            "quality_grade": "A",
        }

        servers = [
            {
                "id": "server_1",
                "name": "US East Premium",
                "region": "us-east",
                "protocol": "vless",
                "performance_score": 0.95,
            }
        ]

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
        """Create VPN connection."""
        # Mock connection creation
        connection_id = f"conn_{current_user.id}_{int(time.time())}"

        return ConnectionResponse(
            connection_id=connection_id,
            status="connected",
            server={
                "id": request.server_id,
                "name": "US East Premium",
                "host": "us-east.streamlinevpn.com",
                "port": 443,
                "protocol": request.protocol or "vless",
                "region": "us-east",
            },
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
            job_status[job_id] = {"status": "queued", "progress": 0}

            async def run_async():
                job_status[job_id] = {"status": "running", "progress": 0}
                try:
                    await run_pipeline_main(config_path, output_dir, formats)
                    job_status[job_id] = {
                        "status": "completed",
                        "progress": 100,
                    }
                    logger.info(
                        "Pipeline job %s completed successfully",
                        job_id,
                    )
                except Exception as e:  # noqa: BLE001
                    job_status[job_id] = {
                        "status": "failed",
                        "error": str(e),
                    }
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
