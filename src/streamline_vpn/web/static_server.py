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
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

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
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.static_dir.mkdir(parents=True, exist_ok=True)

        @app.on_event("startup")
        async def startup_event() -> None:
            logger.info("Starting auto-update task...")
            self.update_task = asyncio.create_task(self._auto_update_loop())
            await self._perform_update()

        @app.on_event("shutdown")
        async def shutdown_event() -> None:
            if self.update_task:
                self.update_task.cancel()

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
            "/",
            StaticFiles(directory=str(self.static_dir), html=True),
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
                    configs_response.raise_for_status()
                    self.cached_data["configurations"] = (
                        configs_response.json()
                    )
                except (httpx.RequestError, json.JSONDecodeError) as exc:
                    logger.error("Failed to fetch configurations: %s", exc)

                try:
                    stats_response = await client.get(
                        f"{self.api_base}/api/statistics"
                    )
                    stats_response.raise_for_status()
                    self.cached_data["statistics"] = stats_response.json()
                except (httpx.RequestError, json.JSONDecodeError) as exc:
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
        except Exception as exc:
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
