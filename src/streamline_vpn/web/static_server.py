"""
Static File Server
==================

Static file server for StreamlineVPN web interface.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ..utils.logging import get_logger

logger = get_logger(__name__)


class StaticFileServer:
    """Static file server for StreamlineVPN."""

    def __init__(
        self, host: str = "127.0.0.1", port: int = 9000, static_dir: str = "static"
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
        self.static_dir.mkdir(parents=True, exist_ok=True)

        # Mount static files
        app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")

        # Serve index.html at root
        @app.get("/")
        async def serve_index():
            index_file = self.static_dir / "index.html"
            if index_file.exists():
                return FileResponse(str(index_file))
            else:
                return {"message": "StreamlineVPN Static Server", "files": "/static"}

        # Serve any file from static directory
        @app.get("/{file_path:path}")
        async def serve_file(file_path: str):
            file_path = Path(file_path)
            full_path = self.static_dir / file_path

            if full_path.exists() and full_path.is_file():
                return FileResponse(str(full_path))
            else:
                return {"error": "File not found"}, 404

        return app

    async def start(self):
        """Start the static file server."""
        logger.info(f"Starting Static File Server on {self.host}:{self.port}")
        # Note: In a real implementation, you would use uvicorn to run the app
        # uvicorn.run(self.app, host=self.host, port=self.port)

    async def stop(self):
        """Stop the static file server."""
        logger.info("Stopping Static File Server")
