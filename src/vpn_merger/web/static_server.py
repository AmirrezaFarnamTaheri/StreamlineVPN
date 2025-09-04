"""
Static File Server for VPN Configuration Generator
================================================

Handles serving static files and integrating with the main VPN merger application.
"""

import logging
from pathlib import Path
from typing import Any

from aiohttp import web

logger = logging.getLogger(__name__)


class StaticFileServer:
    """Static file server for the VPN configuration generator."""

    def __init__(self, static_path: Path | None = None):
        """Initialize the static file server.

        Args:
            static_path: Path to static files directory
        """
        self.static_path = static_path or Path(__file__).parent / "static"
        self.app = web.Application()
        self.runner = None
        self.site = None

        # Setup routes
        self._setup_routes()

        logger.info(f"Static file server initialized with path: {self.static_path}")

    def _setup_routes(self):
        """Setup static file routes."""
        # Serve static files
        self.app.router.add_static("/", self.static_path)

        # Health check
        self.app.router.add_get("/health", self._handle_health)

    async def _handle_health(self, request: web.Request) -> web.Response:
        """Handle health check request."""
        return web.json_response(
            {
                "status": "healthy",
                "static_path": str(self.static_path),
                "files_available": (
                    len(list(self.static_path.glob("*"))) if self.static_path.exists() else 0
                ),
            }
        )

    async def start(self, host: str = "0.0.0.0", port: int = 8081):
        """Start the static file server."""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()

            self.site = web.TCPSite(self.runner, host, port)
            await self.site.start()

            logger.info(f"Static file server started at http://{host}:{port}")

        except Exception as e:
            logger.error(f"Failed to start static file server: {e}")
            raise

    async def stop(self):
        """Stop the static file server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Static file server stopped")

    def get_server_info(self) -> dict[str, Any]:
        """Get server information."""
        return {
            "static_path": str(self.static_path),
            "status": "running" if self.site else "stopped",
            "files_available": (
                len(list(self.static_path.glob("*"))) if self.static_path.exists() else 0
            ),
        }
