"""
Static Control Server with Auto-Update
=====================================

Static control-center server with auto-update and backend proxying.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from ..utils.logging import get_logger
from .settings import Settings

logger = get_logger(__name__)


class StaticControlServer:
    """Static control-center with auto-update and monitoring."""

    def __init__(
        self,
        settings: Settings,
    ):
        """Initialize enhanced static server.

        Args:
            settings: Configuration settings object.
        """
        self.settings = settings
        self.static_dir = Path(self.settings.STATIC_DIR)
        self.api_base = self.settings.API_BASE
        self.update_interval = self.settings.UPDATE_INTERVAL
        self.app = self._create_app()
        self.last_update: Optional[datetime] = None
        self.cached_data: Dict[str, Any] = {}
        self.update_task: Optional[asyncio.Task] = None
        self.backend_client: Optional[aiohttp.ClientSession] = None

    def _create_app(self) -> FastAPI:
        """Create FastAPI application for the control center."""
        app = FastAPI(
            title="StreamlineVPN Control Center",
            description="Enterprise VPN Configuration Platform",
            version="2.0.0",
        )

        # If api_base is injected by the launcher, prefer it
        try:  # pragma: no cover - runtime wiring
            injected = getattr(app.state, "api_base", None)
            if isinstance(injected, str) and injected.startswith("http"):
                self.api_base = injected
                logger.info("Using injected API base: %s", self.api_base)
        except Exception:
            pass

        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.settings.ALLOWED_ORIGINS,
            allow_credentials=self.settings.ALLOW_CREDENTIALS,
            allow_methods=self.settings.ALLOWED_METHODS,
            allow_headers=self.settings.ALLOWED_HEADERS,
        )

        self.static_dir.mkdir(parents=True, exist_ok=True)

        # Descriptive error handlers
        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(
            request: Request, exc: RequestValidationError
        ):
            logger.warning(
                "Request validation failed: %s %s - Client: %s - Errors: %s",
                request.method,
                request.url.path,
                request.client.host if request.client else "unknown",
                exc.errors(),
            )
            return JSONResponse(
                status_code=422,
                content={
                    "error": "Request validation failed",
                    "message": "The request data does not match the expected format",
                    "path": request.url.path,
                    "method": request.method,
                    "timestamp": datetime.now().isoformat(),
                    "details": exc.errors(),
                    "request_id": getattr(request.state, "request_id", None),
                },
            )

        @app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            logger.info(
                "HTTP error %s on %s %s - Client: %s - Detail: %s",
                exc.status_code,
                request.method,
                request.url.path,
                request.client.host if request.client else "unknown",
                exc.detail,
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": "Request failed",
                    "message": exc.detail,
                    "path": request.url.path,
                    "method": request.method,
                    "timestamp": datetime.now().isoformat(),
                    "detail": exc.detail,
                    "request_id": getattr(request.state, "request_id", None),
                },
            )

        @app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            logger.error(
                "Unhandled exception on %s %s - Client: %s - Exception: %s",
                request.method,
                request.url.path,
                request.client.host if request.client else "unknown",
                exc,
                exc_info=True,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred while processing your request",
                    "path": request.url.path,
                    "method": request.method,
                    "timestamp": datetime.now().isoformat(),
                    "request_id": getattr(request.state, "request_id", None),
                },
            )

        @app.on_event("startup")
        async def startup_event() -> None:
            """Initialize backend connection and start auto-update."""
            logger.info(
                "Starting static control server - API Base: %s - Static Dir: %s - Update Interval: %s",
                self.api_base,
                self.static_dir,
                self.update_interval,
            )

            # Initialize backend client with proper configuration
            timeout = aiohttp.ClientTimeout(total=30.0)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self.backend_client = aiohttp.ClientSession(
                timeout=timeout, connector=connector
            )
            logger.info(
                "Backend HTTP client initialized with timeout=30s, connection_limit=10"
            )

            # Wait a moment for API server to be fully ready
            await asyncio.sleep(2)

            # Try to connect to API with retries
            max_retries = 3
            connection_successful = False

            for attempt in range(max_retries):
                try:
                    logger.info(
                        "Attempting to connect to API at %s (attempt %d/%d)",
                        self.api_base,
                        attempt + 1,
                        max_retries,
                    )
                    async with self.backend_client.get(
                        f"{self.api_base}/health"
                    ) as resp:
                        if resp.status == 200:
                            logger.info(
                                "Backend connection successful - API is healthy"
                            )
                            connection_successful = True
                            break
                        else:
                            logger.warning(
                                "Backend health check failed with status %s - Response: %s",
                                resp.status,
                                (
                                    await resp.text()
                                    if resp.content_length
                                    else "No content"
                                ),
                            )
                            if attempt < max_retries - 1:
                                await asyncio.sleep(2)
                except aiohttp.ClientError as exc:
                    logger.warning(
                        "Backend connection failed (attempt %d/%d) - Client Error: %s",
                        attempt + 1,
                        max_retries,
                        exc,
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
                except Exception as exc:  # pragma: no cover
                    logger.warning(
                        "Backend connection failed (attempt %d/%d) - Unexpected Error: %s",
                        attempt + 1,
                        max_retries,
                        exc,
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)

            if not connection_successful:
                logger.error(
                    "Failed to connect to backend after %d attempts - API may not be available",
                    max_retries,
                )

            self.update_task = asyncio.create_task(self._auto_update_loop())
            await self._perform_update()

        @app.get("/health")
        async def health() -> JSONResponse:
            """Basic health endpoint for web container monitoring."""
            status = "ok"
            backend = "unknown"
            try:
                if self.backend_client:
                    async with self.backend_client.get(
                        f"{self.api_base}/health"
                    ) as resp:
                        backend = (
                            "healthy" if resp.status == 200 else f"http_{resp.status}"
                        )
                else:
                    backend = "client_uninitialized"
            except Exception:
                backend = "unreachable"
            return JSONResponse(
                {
                    "status": status,
                    "service": "streamline-web",
                    "backend": backend,
                    "api_base": self.api_base,
                }
            )

        @app.on_event("shutdown")
        async def shutdown_event() -> None:
            """Clean shutdown."""
            logger.info("Shutting down static control server...")

            # Cancel update task gracefully
            if self.update_task:
                logger.info("Cancelling auto-update task...")
                self.update_task.cancel()
                try:
                    await asyncio.wait_for(asyncio.shield(self.update_task), timeout=2)
                    logger.info("Auto-update task cancelled successfully")
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    logger.warning("Auto-update task cancellation timed out")
                except Exception as exc:
                    logger.error("Error cancelling auto-update task: %s", exc)

            # Close backend client
            if self.backend_client:
                logger.info("Closing backend HTTP client...")
                try:
                    await self.backend_client.close()
                    logger.info("Backend HTTP client closed successfully")
                except Exception as exc:
                    logger.error("Error closing backend HTTP client: %s", exc)

            logger.info("Static control server shutdown complete")

        @app.get("/api/status")
        async def get_status() -> JSONResponse:
            if not self.backend_client:
                return JSONResponse(
                    status_code=503, content={"error": "Backend client not initialized"}
                )

            # Backend statistics
            async with self.backend_client.get(
                f"{self.api_base}/api/v1/statistics"
            ) as stats_response:
                stats = (
                    await stats_response.json() if stats_response.status == 200 else {}
                )
            # Backend health
            health_status = "unknown"
            try:
                async with self.backend_client.get(
                    f"{self.api_base}/health"
                ) as health_resp:
                    if health_resp.status == 200:
                        h = await health_resp.json()
                        health_status = h.get("status", "unknown")
            except Exception:  # pragma: no cover - non-critical
                pass
            return JSONResponse(
                {
                    "status": "online",
                    "backend_status": ("connected" if stats else "disconnected"),
                    "backend_health": health_status,
                    "last_update": self.cached_data.get("last_update"),
                    "next_update": (
                        datetime.now() + timedelta(seconds=self.update_interval)
                    ).isoformat(),
                    "statistics": stats,
                    "cached_configs": len(self.cached_data.get("configurations", [])),
                    "auto_update_enabled": self.update_task is not None,
                }
            )

        @app.get("/api/configurations")
        async def get_configurations() -> JSONResponse:
            """Get configurations with proper JSON response."""
            try:
                configs = self.cached_data.get("configurations", [])
                return JSONResponse(
                    content={
                        "success": True,
                        "total": len(configs),
                        "configurations": configs[:100],  # Limit for performance
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Cache-Control": "max-age=30",
                    },
                )
            except Exception as e:
                logger.error("Error getting configurations: %s", e)
                return JSONResponse(
                    content={
                        "success": False,
                        "error": str(e),
                        "hint": "Try refreshing the cache via /api/refresh and check backend availability.",
                    },
                    status_code=500,
                )

        @app.get("/api/statistics")
        async def get_statistics() -> JSONResponse:
            return JSONResponse(self.cached_data.get("statistics", {}))

        @app.post("/api/process")
        async def trigger_process(
            background_tasks: BackgroundTasks,
        ) -> JSONResponse:
            background_tasks.add_task(self._perform_update)
            return JSONResponse({"message": "Processing started", "status": "running"})

        @app.post("/api/refresh")
        async def force_refresh() -> JSONResponse:
            await self._perform_update()
            return JSONResponse(
                {
                    "message": "Data refreshed",
                    "last_update": (
                        self.last_update.isoformat() if self.last_update else None
                    ),
                }
            )

        @app.get("/api/export/{format}")
        async def export_configurations(format: str):
            configs = self.cached_data.get("configurations", [])
            if format == "json":
                return JSONResponse(
                    {
                        "configurations": configs,
                        "exported_at": datetime.now().isoformat(),
                        "total": len(configs),
                    }
                )
            if format == "text":
                text_output = "\n".join(
                    [
                        (
                            f"{c.get('protocol', 'unknown')}://"
                            f"{c.get('server', 'unknown')}:"
                            f"{c.get('port', 0)}"
                        )
                        for c in configs
                    ]
                )
                return HTMLResponse(
                    content=f"<pre>{text_output}</pre>",
                    media_type="text/plain",
                )
            if format == "download":
                file_content = json.dumps(configs, indent=2)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return HTMLResponse(
                    content=file_content,
                    media_type="application/json",
                    headers={
                        "Content-Disposition": (
                            "attachment; filename=" f"vpn_configs_{timestamp}.json"
                        ),
                    },
                )
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format '{format}'. Supported: json, text, download",
            )

        @app.get("/api-base.js")
        async def api_base_script() -> Response:
            """Expose backend API base URL for frontend pages."""
            js = (
                "// Injected by StaticControlServer\n"
                f"window.__API_BASE__ = '{self.api_base}';\n"
            )
            return Response(
                content=js,
                media_type="application/javascript",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )

        @app.api_route(
            "/api/{path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        )
        async def proxy_api(path: str, request: Request):
            """Proxy unknown API requests to the backend service."""
            if not self.backend_client:
                logger.error("Proxy request failed - Backend client not initialized")
                raise HTTPException(
                    status_code=503, detail="Backend client not initialized"
                )

            try:
                backend_url = f"{self.api_base}/api/{path}"
                logger.info(
                    "Proxying %s request to %s - Client: %s - Query: %s",
                    request.method,
                    backend_url,
                    request.client.host if request.client else "unknown",
                    dict(request.query_params) if request.query_params else {},
                )
                body = (
                    await request.body()
                    if request.method in {"POST", "PUT", "PATCH"}
                    else None
                )
                hop_by_hop = {
                    "connection",
                    "keep-alive",
                    "proxy-authenticate",
                    "proxy-authorization",
                    "te",
                    "trailers",
                    "transfer-encoding",
                    "upgrade",
                    "content-length",
                }
                fwd_headers = {
                    k: v
                    for k, v in request.headers.items()
                    if k.lower() not in hop_by_hop and k.lower() != "host"
                }
                # Add forwarding headers
                client_host = request.client.host if request.client else ""
                if client_host:
                    existing_xff = fwd_headers.get("x-forwarded-for", "")
                    fwd_headers["x-forwarded-for"] = (
                        f"{existing_xff}, {client_host}"
                        if existing_xff
                        else client_host
                    )
                fwd_headers.setdefault("x-forwarded-proto", request.url.scheme)
                orig_host = request.headers.get("host", "")
                fwd_headers.setdefault("x-forwarded-host", orig_host)

                async with self.backend_client.request(
                    method=request.method,
                    url=backend_url,
                    headers=fwd_headers,
                    params=dict(request.query_params),
                    data=body,
                ) as response:
                    hop_by_hop_resp = hop_by_hop
                    resp_headers = {
                        k: v
                        for k, v in response.headers.items()
                        if k.lower() not in hop_by_hop_resp
                    }
                    content = await response.read()
                    logger.debug(
                        "Proxy response received - Status: %s - Content-Length: %d - Content-Type: %s",
                        response.status,
                        len(content),
                        response.headers.get("content-type", "unknown"),
                    )
                    return Response(
                        content=content,
                        status_code=response.status,
                        headers=resp_headers,
                        media_type=response.headers.get("content-type"),
                    )
            except aiohttp.ClientError as exc:  # pragma: no cover - network
                logger.error(
                    "Proxy request failed - Client Error: %s - URL: %s - Method: %s",
                    exc,
                    backend_url,
                    request.method,
                )
                raise HTTPException(
                    status_code=503, detail=f"Backend service unavailable: {str(exc)}"
                )
            except Exception as exc:  # pragma: no cover
                logger.error(
                    "Unexpected proxy error: %s - URL: %s - Method: %s",
                    exc,
                    backend_url,
                    request.method,
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500, detail=f"Internal proxy error: {str(exc)}"
                )

        app.mount(
            "/",
            StaticFiles(directory=str(self.static_dir), html=True),
            name="static",
        )
        return app

    async def _perform_update(self) -> None:
        """Perform actual update from sources with proper error handling."""
        try:
            logger.info("Starting auto-update cycle...")

            if not self.backend_client:
                logger.warning("Backend client not initialized, skipping update")
                return

            # Check if backend is available
            try:
                async with self.backend_client.get(
                    f"{self.api_base}/health"
                ) as health_response:
                    if health_response.status != 200:
                        logger.warning(
                            "Backend health check failed: %s", health_response.status
                        )
                        return
            except Exception as e:
                logger.error("Backend not available for auto-update: %s", e)
                return

            # Trigger pipeline run
            logger.info("Triggering pipeline run...")
            async with self.backend_client.post(
                f"{self.api_base}/api/v1/pipeline/run",
                json={
                    "config_path": "config/sources.yaml",
                    "output_dir": "output",
                    "formats": ["json", "clash", "singbox", "base64", "raw", "csv"],
                },
            ) as response:
                if response.status not in (200, 202):
                    logger.error("Failed to start pipeline: %s", response.status)
                    return

                result = await response.json()
                job_id = result.get("job_id")

            if not job_id:
                logger.error("No job ID returned from pipeline run")
                return

            logger.info("Pipeline job started: %s", job_id)

            # Poll for completion with exponential backoff
            max_attempts = 120  # 10 minutes max
            attempt = 0
            base_delay = 2  # Start with 2 seconds

            while attempt < max_attempts:
                attempt += 1
                try:
                    async with self.backend_client.get(
                        f"{self.api_base}/api/v1/pipeline/status/{job_id}"
                    ) as status_resp:
                        if status_resp.status == 200:
                            status_data = await status_resp.json()
                            state = status_data.get("status") or status_data.get(
                                "state"
                            )
                            if state in {"completed", "failed"}:
                                logger.info("Pipeline finished with state: %s", state)
                                # On success, refresh cached data immediately
                                if state == "completed":
                                    try:
                                        await self._refresh_cached_data()
                                        self.last_update = datetime.now()
                                        self.cached_data["last_update"] = (
                                            self.last_update.isoformat()
                                        )
                                        logger.info(
                                            "Refreshed cache after pipeline completion"
                                        )
                                    except Exception as e:
                                        logger.warning(
                                            "Cache refresh after pipeline failed: %s", e
                                        )
                                break
                        else:
                            logger.warning(
                                "Status check returned %s", status_resp.status
                            )
                except Exception as e:
                    logger.warning("Status check error: %s", e)
                # backoff
                await asyncio.sleep(min(30, base_delay * (2 ** (attempt // 5))))
        except Exception as e:
            logger.error("Auto-update failed: %s", e)

    async def _auto_update_loop(self) -> None:
        """Auto-update loop that runs every update interval."""
        while True:
            try:
                await asyncio.sleep(self.update_interval)
                await self._perform_update()
                logger.info("Auto-update completed")
            except asyncio.CancelledError:  # pragma: no cover
                break
            except Exception as exc:
                logger.error("Auto-update error: %s", exc)

    async def _refresh_cached_data(self) -> None:
        """Refresh cached data from backend."""
        if not self.backend_client:
            logger.warning("Backend client not initialized, skipping cache refresh")
            return

        try:
            # Fetch configurations
            async with self.backend_client.get(
                f"{self.api_base}/api/v1/configurations?limit=1000"
            ) as configs_response:
                if configs_response.status == 200:
                    data = await configs_response.json()
                    self.cached_data["configurations"] = data.get("configurations", [])
                    logger.info(
                        "Cached %d configurations",
                        len(self.cached_data["configurations"]),
                    )

            # Fetch statistics
            async with self.backend_client.get(
                f"{self.api_base}/api/v1/statistics"
            ) as stats_response:
                if stats_response.status == 200:
                    self.cached_data["statistics"] = await stats_response.json()
                    logger.info("Updated statistics cache")

            # Fetch sources
            async with self.backend_client.get(
                f"{self.api_base}/api/v1/sources"
            ) as sources_response:
                if sources_response.status == 200:
                    data = await sources_response.json()
                    self.cached_data["sources"] = data.get("sources", [])
                    logger.info("Cached %d sources", len(self.cached_data["sources"]))

        except Exception as e:
            logger.error("Error refreshing cached data: %s", e, exc_info=True)


if __name__ == "__main__":  # pragma: no cover - manual run only
    import uvicorn

    from .settings import settings

    server = StaticControlServer(settings)
    logger.info("Starting server on %s:%d", settings.HOST, settings.PORT)
    uvicorn.run(
        server.app,
        host=server.settings.HOST,
        port=server.settings.PORT,
        log_level="info",
    )

# Backward compatibility alias for older entrypoints/imports
EnhancedStaticServer = StaticControlServer
