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
        try:
            self.static_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create static directory '{self.static_dir}': {e}")
            raise

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
            requested = (self.static_dir / file_path).resolve()
            static_root = self.static_dir.resolve()
            if not str(requested).startswith(str(static_root) + str(Path().anchor if Path().anchor else "")) and static_root not in requested.parents:
                from fastapi.responses import JSONResponse
                return JSONResponse(content={"error": "File not found"}, status_code=404)
            if requested.exists() and requested.is_file():
                return FileResponse(str(requested))
            else:
                from fastapi.responses import JSONResponse
                return JSONResponse(content={"error": "File not found"}, status_code=404)

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
