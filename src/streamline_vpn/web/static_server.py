"""
Enhanced Static File Server with Auto-Update
============================================

Static file server with auto-update capability for StreamlineVPN.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import httpx

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
            version="2.0.0"
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Create static directory if it doesn't exist
        self.static_dir.mkdir(parents=True, exist_ok=True)

        # API Routes
        @app.on_event("startup")
        async def startup_event():
            """Start auto-update task on server startup."""
            self.update_task = asyncio.create_task(self._auto_update_loop())
            await self._perform_update()  # Initial update

        @app.on_event("shutdown")
        async def shutdown_event():
            """Cancel auto-update task on shutdown."""
            if self.update_task:
                self.update_task.cancel()

        @app.get("/")
        async def serve_index():
            """Serve the main index page."""
            index_path = self.static_dir / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return HTMLResponse(self._generate_fallback_index())

        @app.get("/interactive")
        async def serve_interactive():
            """Serve the interactive control panel."""
            panel_path = self.static_dir / "interactive.html"
            if panel_path.exists():
                return FileResponse(panel_path)
            return HTMLResponse(self._generate_fallback_panel())

        @app.get("/api/status")
        async def get_status():
            """Get current system status."""
            return JSONResponse({
                "status": "online",
                "last_update": self.last_update.isoformat() if self.last_update else None,
                "next_update": (
                    self.last_update + timedelta(seconds=self.update_interval)
                ).isoformat() if self.last_update else None,
                "cached_configs": len(self.cached_data.get("configurations", [])),
                "auto_update_enabled": self.update_task is not None
            })

        @app.get("/api/configurations")
        async def get_configurations():
            """Get cached VPN configurations."""
            return JSONResponse(self.cached_data.get("configurations", []))

        @app.get("/api/statistics")
        async def get_statistics():
            """Get system statistics."""
            return JSONResponse(self.cached_data.get("statistics", {}))

        @app.post("/api/process")
        async def trigger_process(background_tasks: BackgroundTasks):
            """Trigger VPN configuration processing."""
            background_tasks.add_task(self._perform_update)
            return JSONResponse({
                "message": "Processing started",
                "status": "running"
            })

        @app.post("/api/refresh")
        async def force_refresh():
            """Force immediate data refresh."""
            await self._perform_update()
            return JSONResponse({
                "message": "Data refreshed",
                "last_update": self.last_update.isoformat()
            })

        @app.get("/api/export/{format}")
        async def export_configurations(format: str):
            """Export configurations in specified format."""
            configs = self.cached_data.get("configurations", [])

            if format == "json":
                return JSONResponse({
                    "configurations": configs,
                    "exported_at": datetime.now().isoformat(),
                    "total": len(configs)
                })
            elif format == "text":
                text_output = "\n".join([
                    f"{c.get('protocol', 'unknown')}://{c.get('server', 'unknown')}:{c.get('port', 0)}"
                    for c in configs
                ])
                return HTMLResponse(
                    content=f"<pre>{text_output}</pre>",
                    media_type="text/plain"
                )
            elif format == "download":
                # Create downloadable JSON file
                file_content = json.dumps(configs, indent=2)
                return HTMLResponse(
                    content=file_content,
                    media_type="application/json",
                    headers={
                        "Content-Disposition": f"attachment; filename=vpn_configs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    }
                )
            else:
                raise HTTPException(status_code=400, detail="Invalid format")

        # Mount static files for assets
        app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")

        return app

    async def _perform_update(self):
        """Perform data update from backend services."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Fetch configurations
                try:
                    configs_response = await client.get(f"{self.api_base}/api/configs")
                    if configs_response.status_code == 200:
                        self.cached_data["configurations"] = configs_response.json()
                except Exception as e:
                    logger.error(f"Failed to fetch configurations: {e}")

                # Fetch statistics
                try:
                    stats_response = await client.get(f"{self.api_base}/api/statistics")
                    if stats_response.status_code == 200:
                        self.cached_data["statistics"] = stats_response.json()
                except Exception as e:
                    logger.error(f"Failed to fetch statistics: {e}")

            self.last_update = datetime.now()
            logger.info(f"Data updated successfully at {self.last_update}")

            # Save cache to disk for persistence
            cache_file = self.static_dir / "cache.json"
            async with aiofiles.open(cache_file, "w") as f:
                await f.write(json.dumps({
                    "last_update": self.last_update.isoformat(),
                    "data": self.cached_data
                }, indent=2))

        except Exception as e:
            logger.error(f"Update failed: {e}")

    async def _auto_update_loop(self):
        """Auto-update loop that runs every 8 hours."""
        while True:
            try:
                await asyncio.sleep(self.update_interval)
                await self._perform_update()
                logger.info("Auto-update completed")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-update error: {e}")

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
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="spinner"></div>
                <h1>StreamlineVPN</h1>
                <p>Loading control panel...</p>
                <script>
                    setTimeout(() => {
                        window.location.href = '/interactive';
                    }, 2000);
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


# Run the enhanced server
if __name__ == "__main__":
    import uvicorn

    server = EnhancedStaticServer()
    uvicorn.run(
        server.app,
        host=server.host,
        port=server.port,
        log_level="info"
    )
