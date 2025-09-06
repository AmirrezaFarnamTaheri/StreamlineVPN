"""
Static File Server
==================

Static file server for StreamlineVPN web interface.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from ..utils.logging import get_logger

logger = get_logger(__name__)


class StaticFileServer:
    """Static file server for StreamlineVPN."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9000,
        static_dir: str = "static",
    ):
        """Initialize static file server.

        Args:
            host: Host to bind to
            port: Port to bind to
            static_dir: Directory containing static files
        """
        self.host = host
        self.port = port
        self.static_dir = Path(static_dir)
        self.app = self._create_static_app()

    def _create_static_app(self) -> FastAPI:
        """Create static file FastAPI application."""
        app = FastAPI(title="StreamlineVPN Static Server")

        # Create static directory if it doesn't exist
        try:
            self.static_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(
                "Failed to create static directory '%s'",
                self.static_dir,
                exc_info=e,
            )
            raise RuntimeError("Failed to initialize static directory") from e

        # Mount StaticFiles to handle all file serving, including index.html
        app.mount(
            "/",
            StaticFiles(directory=str(self.static_dir), html=True),
            name="static",
        )

        # Use middleware to add cache headers specifically for index.html
        @app.middleware("http")
        async def add_cache_control_for_index(request: Request, call_next):
            response = await call_next(request)
            if request.url.path == "/" or request.url.path == "/index.html":
                response.headers["Cache-Control"] = (
                    "no-cache, no-store, must-revalidate"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            return response

        return app

    async def start(self):
        """Start the static file server."""
        logger.info(f"Starting Static File Server on {self.host}:{self.port}")
        # Note: In a real implementation, you would use uvicorn to run the app
        # uvicorn.run(self.app, host=self.host, port=self.port)

    async def stop(self):
        """Stop the static file server."""
        logger.info("Stopping Static File Server")
