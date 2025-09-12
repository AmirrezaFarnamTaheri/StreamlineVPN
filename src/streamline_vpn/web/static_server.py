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

import aiofiles
import httpx
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
        self.backend_client = httpx.AsyncClient(timeout=30.0)

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
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc)
            return JSONResponse(
                status_code=422,
                content={
                    "error": "Request validation failed",
                    "path": request.url.path,
                    "method": request.method,
                    "timestamp": datetime.now().isoformat(),
                    "details": exc.errors(),
                },
            )

        @app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            logger.info("HTTP error %s on %s %s: %s", exc.status_code, request.method, request.url.path, exc.detail)
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": "Request failed",
                    "path": request.url.path,
                    "method": request.method,
                    "timestamp": datetime.now().isoformat(),
                    "detail": exc.detail,
                },
            )

        @app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "path": request.url.path,
                    "method": request.method,
                    "timestamp": datetime.now().isoformat(),
                    "detail": str(exc),
                },
            )

        @app.on_event("startup")
        async def startup_event() -> None:
            """Initialize backend connection and start auto-update."""
            logger.info("Starting static control server...")
            try:
                resp = await self.backend_client.get(f"{self.api_base}/health")
                if resp.status_code == 200:
                    logger.info("Backend connection successful")
                else:
                    logger.warning(
                        "Backend health returned status %s", resp.status_code
                    )
            except Exception as exc:  # pragma: no cover
                logger.warning("Backend not available: %s", exc)

            self.update_task = asyncio.create_task(self._auto_update_loop())
            await self._perform_update()

        @app.on_event("shutdown")
        async def shutdown_event() -> None:
            if self.update_task:
                self.update_task.cancel()
                try:
                    await asyncio.wait_for(
                        asyncio.shield(self.update_task), timeout=2
                    )
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass
            await self.backend_client.aclose()

        @app.get("/api/status")
        async def get_status() -> JSONResponse:
            # Backend statistics
            stats_response = await self.backend_client.get(
                f"{self.api_base}/api/v1/statistics"
            )
            stats = (
                stats_response.json()
                if stats_response.status_code == 200
                else {}
            )
            # Backend health
            health_status = "unknown"
            try:
                health_resp = await self.backend_client.get(
                    f"{self.api_base}/health"
                )
                if health_resp.status_code == 200:
                    h = health_resp.json()
                    health_status = h.get("status", "unknown")
            except Exception:  # pragma: no cover - non-critical
                pass
            return JSONResponse(
                {
                    "status": "online",
                    "backend_status": (
                        "connected" if stats else "disconnected"
                    ),
                    "backend_health": health_status,
                    "last_update": self.cached_data.get("last_update"),
                    "next_update": (
                        datetime.now()
                        + timedelta(seconds=self.update_interval)
                    ).isoformat(),
                    "statistics": stats,
                    "cached_configs": len(
                        self.cached_data.get("configurations", [])
                    ),
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
                        "configurations": configs[:100]  # Limit for performance
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Cache-Control": "max-age=30"
                    }
                )
            except Exception as e:
                logger.error(f"Error getting configurations: {e}")
                return JSONResponse(
                    content={
                        "success": False,
                        "error": str(e),
                        "hint": "Try refreshing the cache via /api/refresh and check backend availability.",
                    },
                    status_code=500
                )

        @app.get("/api/statistics")
        async def get_statistics() -> JSONResponse:
            return JSONResponse(self.cached_data.get("statistics", {}))

        @app.post("/api/process")
        async def trigger_process(
            background_tasks: BackgroundTasks,
        ) -> JSONResponse:
            background_tasks.add_task(self._perform_update)
            return JSONResponse(
                {"message": "Processing started", "status": "running"}
            )

        @app.post("/api/refresh")
        async def force_refresh() -> JSONResponse:
            await self._perform_update()
            return JSONResponse(
                {
                    "message": "Data refreshed",
                    "last_update": (
                        self.last_update.isoformat()
                        if self.last_update
                        else None
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
                            "attachment; filename="
                            f"vpn_configs_{timestamp}.json"
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
            try:
                backend_url = f"{self.api_base}/api/{path}"
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

                response = await self.backend_client.request(
                    method=request.method,
                    url=backend_url,
                    headers=fwd_headers,
                    params=dict(request.query_params),
                    content=body,
                )
                hop_by_hop_resp = hop_by_hop
                resp_headers = {
                    k: v
                    for k, v in response.headers.items()
                    if k.lower() not in hop_by_hop_resp
                }
                content = await response.aread()
                return Response(
                    content=content,
                    status_code=response.status_code,
                    headers=resp_headers,
                    media_type=response.headers.get("content-type"),
                )
            except httpx.RequestError as exc:  # pragma: no cover - network
                logger.error("Proxy request failed: %s", exc)
                raise HTTPException(
                    status_code=503, detail="Backend service unavailable"
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
            
            # Check if backend is available
            try:
                health_response = await self.backend_client.get(
                    f"{self.api_base}/health",
                    timeout=5.0
                )
                if health_response.status_code != 200:
                    logger.warning(f"Backend health check failed: {health_response.status_code}")
                    return
            except Exception as e:
                logger.error(f"Backend not available for auto-update: {e}")
                return
            
            # Trigger pipeline run
            logger.info("Triggering pipeline run...")
            response = await self.backend_client.post(
                f"{self.api_base}/api/v1/pipeline/run",
                json={
                    "config_path": "config/sources.unified.yaml",
                    "output_dir": "output",
                    "formats": ["json", "clash", "singbox", "base64", "raw", "csv"]
                },
                timeout=30.0
            )
            
            if response.status_code not in (200, 202):
                logger.error(f"Failed to start pipeline: {response.status_code}")
                return
            
            result = response.json()
            job_id = result.get("job_id")
            
            if not job_id:
                logger.error("No job ID returned from pipeline run")
                return
            
            logger.info(f"Pipeline job started: {job_id}")
            
            # Poll for completion with exponential backoff
            max_attempts = 120  # 10 minutes max
            attempt = 0
            base_delay = 2  # Start with 2 seconds
            
            while attempt < max_attempts:
                attempt += 1
                try:
                    status_resp = await self.backend_client.get(
                        f"{self.api_base}/api/v1/pipeline/status/{job_id}",
                        timeout=10.0,
                    )
                    if status_resp.status_code == 200:
                        status_data = status_resp.json()
                        state = status_data.get("status") or status_data.get("state")
                        if state in {"completed", "failed"}:
                            logger.info("Pipeline finished with state: %s", state)
                            # On success, refresh cached data immediately
                            if state == "completed":
                                try:
                                    await self._refresh_cached_data()
                                    self.last_update = datetime.now()
                                    self.cached_data["last_update"] = self.last_update.isoformat()
                                    logger.info("Refreshed cache after pipeline completion")
                                except Exception as e:
                                    logger.warning("Cache refresh after pipeline failed: %s", e)
                            break
                    else:
                        logger.warning("Status check returned %s", status_resp.status_code)
                except Exception as e:
                    logger.warning("Status check error: %s", e)
                # backoff
                await asyncio.sleep(min(30, base_delay * (2 ** (attempt // 5))))
        except Exception as e:
            logger.error(f"Auto-update failed: {e}")

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
        try:
            # Fetch configurations
            configs_response = await self.backend_client.get(
                f"{self.api_base}/api/v1/configurations?limit=1000",
                timeout=30.0
            )
            if configs_response.status_code == 200:
                self.cached_data["configurations"] = configs_response.json().get("configurations", [])
                logger.info(f"Cached {len(self.cached_data['configurations'])} configurations")
            
            # Fetch statistics
            stats_response = await self.backend_client.get(
                f"{self.api_base}/api/v1/statistics",
                timeout=10.0
            )
            if stats_response.status_code == 200:
                self.cached_data["statistics"] = stats_response.json()
                logger.info("Updated statistics cache")
            
            # Fetch sources
            sources_response = await self.backend_client.get(
                f"{self.api_base}/api/v1/sources",
                timeout=10.0
            )
            if sources_response.status_code == 200:
                self.cached_data["sources"] = sources_response.json().get("sources", [])
                logger.info(f"Cached {len(self.cached_data['sources'])} sources")
                
        except Exception as e:
            logger.error(f"Error refreshing cached data: {e}", exc_info=True)


if __name__ == "__main__":  # pragma: no cover - manual run only
    import uvicorn

    from .settings import settings

    server = StaticControlServer(settings)
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        server.app,
        host=server.settings.HOST,
        port=server.settings.PORT,
        log_level="info",
    )

# Backward compatibility alias for older entrypoints/imports
EnhancedStaticServer = StaticControlServer
