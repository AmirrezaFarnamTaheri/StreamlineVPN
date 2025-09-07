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
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..utils.logging import get_logger

logger = get_logger(__name__)


class EnhancedStaticServer:
    """Enhanced static file server with auto-update and monitoring."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        static_dir: str = "docs",
        api_base: str = "http://localhost:8080",
        update_interval: int = 28800,  # 8 hours in seconds
    ):
        """Initialize enhanced static server.

        Args:
            host: Host to bind to
            port: Port to bind to
            static_dir: Directory containing static files
            api_base: Base URL for API endpoints
            update_interval: Auto-update interval in seconds (default 8 hours)
        """
        self.host = host
        self.port = port
        self.static_dir = Path(static_dir)
        self.api_base = api_base
        self.update_interval = update_interval
        self.app = self._create_app()
        self.last_update: Optional[datetime] = None
        self.cached_data: Dict[str, Any] = {}
        self.update_task: Optional[asyncio.Task] = None

    def _create_app(self) -> FastAPI:
        """Create enhanced FastAPI application."""
        app = FastAPI(
            title="StreamlineVPN Control Center",
            description="Enterprise VPN Configuration Platform",
            version="2.0.0",
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.static_dir.mkdir(parents=True, exist_ok=True)

        @app.on_event("startup")
        async def startup_event() -> None:
            self.update_task = asyncio.create_task(self._auto_update_loop())
            await self._perform_update()

        @app.on_event("shutdown")
        async def shutdown_event() -> None:
            if self.update_task:
                self.update_task.cancel()

        @app.get("/")
        async def serve_index() -> HTMLResponse | FileResponse:
            index_path = self.static_dir / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return HTMLResponse(self._generate_fallback_index())

        @app.get("/interactive")
        async def serve_interactive() -> HTMLResponse | FileResponse:
            panel_path = self.static_dir / "interactive.html"
            if panel_path.exists():
                return FileResponse(panel_path)
            return HTMLResponse(self._generate_fallback_panel())

        @app.get("/api/status")
        async def get_status() -> JSONResponse:
            return JSONResponse(
                {
                    "status": "online",
                    "last_update": (
                        self.last_update.isoformat()
                        if self.last_update
                        else None
                    ),
                    "next_update": (
                        (
                            self.last_update
                            + timedelta(seconds=self.update_interval)
                        ).isoformat()
                        if self.last_update
                        else None
                    ),
                    "cached_configs": len(
                        self.cached_data.get("configurations", [])
                    ),
                    "auto_update_enabled": self.update_task is not None,
                }
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
                        f"{c.get('protocol', 'unknown')}://{c.get('server', 'unknown')}:{c.get('port', 0)}"
                        for c in configs
                    ]
                )
                return HTMLResponse(
                    content=f"<pre>{text_output}</pre>",
                    media_type="text/plain",
                )
            if format == "download":
                file_content = json.dumps(configs, indent=2)
                return HTMLResponse(
                    content=file_content,
                    media_type="application/json",
                    headers={
                        "Content-Disposition": "attachment; filename="
                        f"vpn_configs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    },
                )
            raise HTTPException(status_code=400, detail="Invalid format")

        app.mount(
            "/static",
            StaticFiles(directory=str(self.static_dir)),
            name="static",
        )
        return app

    async def _perform_update(self) -> None:
        """Perform data update from backend services."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                try:
                    configs_response = await client.get(
                        f"{self.api_base}/api/configs"
                    )
                    if configs_response.status_code == 200:
                        self.cached_data["configurations"] = (
                            configs_response.json()
                        )
                except Exception as exc:  # noqa: BLE001
                    logger.error("Failed to fetch configurations: %s", exc)

                try:
                    stats_response = await client.get(
                        f"{self.api_base}/api/statistics"
                    )
                    if stats_response.status_code == 200:
                        self.cached_data["statistics"] = stats_response.json()
                except Exception as exc:  # noqa: BLE001
                    logger.error("Failed to fetch statistics: %s", exc)

            self.last_update = datetime.now()
            logger.info("Data updated successfully at %s", self.last_update)

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
        except Exception as exc:  # noqa: BLE001
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
            except Exception as exc:  # noqa: BLE001
                logger.error("Auto-update error: %s", exc)

    def _generate_fallback_index(self) -> str:
        """Generate fallback index page if file doesn't exist."""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>StreamlineVPN - Loading...</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    margin: 0;
                }
                .container { text-align: center; }
                .spinner {
                    border: 3px solid rgba(255,255,255,0.3);
                    border-top-color: white;
                    border-radius: 50%;
                    width: 50px;
                    height: 50px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 20px;
                }
                @keyframes spin { to { transform: rotate(360deg); } }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="spinner"></div>
                <h1>StreamlineVPN</h1>
                <p>Loading control panel...</p>
                <script>
                    setTimeout(() => { window.location.href = '/interactive'; }, 2000);
                </script>
            </div>
        </body>
        </html>
        """

    def _generate_fallback_panel(self) -> str:
        """Generate fallback interactive panel."""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>StreamlineVPN Control Panel</title>
        </head>
        <body>
            <h1>Control Panel Loading...</h1>
            <p>Please ensure the interactive.html file is present in the static directory.</p>
        </body>
        </html>
        """


if __name__ == "__main__":  # pragma: no cover - manual run only
    import uvicorn

    server = EnhancedStaticServer()
    uvicorn.run(
        server.app,
        host=server.host,
        port=server.port,
        log_level="info",
    )
