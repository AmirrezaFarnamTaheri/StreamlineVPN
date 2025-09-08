"""
Enhanced Static File Server with Auto-Update
============================================

Static file server with auto-update capability for StreamlineVPN.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles
import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..models import OutputFormat
from ..utils.logging import get_logger
from .settings import Settings

logger = get_logger(__name__)


class EnhancedStaticServer:
    """Enhanced static file server with auto-update and monitoring."""

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
        """Create enhanced FastAPI application."""
        app = FastAPI(
            title="StreamlineVPN Control Center",
            description="Enterprise VPN Configuration Platform",
            version="2.0.0",
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.settings.ALLOWED_ORIGINS,
            allow_credentials=self.settings.ALLOW_CREDENTIALS,
            allow_methods=self.settings.ALLOWED_METHODS,
            allow_headers=self.settings.ALLOWED_HEADERS,
        )

        self.static_dir.mkdir(parents=True, exist_ok=True)

        @app.on_event("startup")
        async def startup_event() -> None:
            """Initialize backend connection and start auto-update."""
            logger.info("Starting enhanced static server...")
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
            try:
                stats_response = await self.backend_client.get(
                    f"{self.api_base}/api/v1/statistics"
                )
                stats = (
                    stats_response.json()
                    if stats_response.status_code == 200
                    else {}
                )
                return JSONResponse(
                    {
                        "status": "online",
                        "backend_status": (
                            "connected" if stats else "disconnected"
                        ),
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
            except Exception as exc:  # pragma: no cover
                logger.error("Error getting status: %s", exc)
                return JSONResponse(
                    {"status": "error", "error": str(exc)}, status_code=503
                )

        @app.get("/api/configurations")
        async def get_configurations() -> JSONResponse:
            return JSONResponse(self.cached_data.get("configurations", []))

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
            raise HTTPException(status_code=400, detail="Invalid format")

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
        """Perform update with health check and backoff; refresh cached data."""
        try:
            logger.info("Starting auto-update...")

            # Health check
            try:
                health = await self.backend_client.get(f"{self.api_base}/health", timeout=5.0)
                if health.status_code != 200:
                    logger.warning("Backend health returned %s", health.status_code)
                    return
            except Exception as exc:  # pragma: no cover
                logger.warning("Backend not available: %s", exc)
                return

            # Trigger pipeline
            response = await self.backend_client.post(
                f"{self.api_base}/api/v1/pipeline/run",
                json={
                    "config_path": "config/sources.unified.yaml",
                    "output_dir": "output",
                    "formats": [
                        OutputFormat.JSON.value,
                        OutputFormat.CLASH.value,
                        OutputFormat.SINGBOX.value,
                        OutputFormat.BASE64.value,
                        OutputFormat.RAW.value if hasattr(OutputFormat, "RAW") else "raw",
                        OutputFormat.CSV.value if hasattr(OutputFormat, "CSV") else "csv",
                    ],
                },
                timeout=30.0,
            )

            if response.status_code != 200:
                logger.error("Failed to start auto-update: %s", response.status_code)
                return

            job_id = response.json().get("job_id")
            if not job_id:
                logger.error("No job id returned from backend")
                return

            # Poll with exponential backoff
            attempts = 0
            max_attempts = 120  # ~10 minutes
            delay = 2.0
            while attempts < max_attempts:
                await asyncio.sleep(min(delay, 30.0))
                attempts += 1
                try:
                    status_resp = await self.backend_client.get(
                        f"{self.api_base}/api/v1/pipeline/status/{job_id}",
                        timeout=10.0,
                    )
                    if status_resp.status_code != 200:
                        delay = min(delay * 1.5, 30.0)
                        continue
                    status_data = status_resp.json()
                    state = status_data.get("status")
                    if state == "completed":
                        # Refresh caches
                        await self._refresh_cached_data()
                        self.cached_data["last_update"] = datetime.now().isoformat()
                        break
                    if state == "failed":
                        logger.error("Auto-update failed: %s", status_data.get("error"))
                        break
                    delay = min(delay * 1.2, 30.0)
                except Exception as exc:  # pragma: no cover
                    logger.error("Error polling job status: %s", exc)
                    delay = min(delay * 1.5, 30.0)

            self.last_update = datetime.now()
            cache_file = self.static_dir / "cache.json"
            async with aiofiles.open(cache_file, "w") as f:
                await f.write(
                    json.dumps(
                        {
                            "last_update": self.last_update.isoformat(),
                            "data": self.cached_data,
                        },
                        indent=2,
                    )
                )
        except Exception as exc:  # pragma: no cover
            logger.error("Update failed: %s", exc)

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
        """Refresh cached data from backend endpoints."""
        try:
            cfg_resp = await self.backend_client.get(
                f"{self.api_base}/api/v1/configurations?limit=1000", timeout=30.0
            )
            if cfg_resp.status_code == 200:
                self.cached_data["configurations"] = cfg_resp.json().get("configurations", [])
            stats_resp = await self.backend_client.get(
                f"{self.api_base}/api/v1/statistics", timeout=15.0
            )
            if stats_resp.status_code == 200:
                self.cached_data["statistics"] = stats_resp.json()
            src_resp = await self.backend_client.get(
                f"{self.api_base}/api/v1/sources", timeout=15.0
            )
            if src_resp.status_code == 200:
                body = src_resp.json()
                self.cached_data["sources"] = body.get("sources", body)
        except Exception as exc:  # pragma: no cover
            logger.error("Error refreshing cached data: %s", exc)


if __name__ == "__main__":  # pragma: no cover - manual run only
    import uvicorn

    from .settings import settings

    server = EnhancedStaticServer(settings)
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        server.app,
        host=server.settings.HOST,
        port=server.settings.PORT,
        log_level="info",
    )
