"""
Static File Server
==================

Static file server for StreamlineVPN web interface.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
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
            logger.error(
                "Failed to create static directory '%s'", self.static_dir, exc_info=e
            )
            raise RuntimeError("Failed to initialize static directory") from e

        # Mount static files
        app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")

        # Serve index.html at root
        @app.get("/")
        async def serve_index():
            index_file = self.static_dir / "index.html"
            if index_file.exists():
                resp = FileResponse(str(index_file))
                resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                resp.headers["Pragma"] = "no-cache"
                resp.headers["Expires"] = "0"
                return resp
            raise HTTPException(status_code=404, detail="Index not found")

        # Serve any file from static directory
        @app.get("/{file_path:path}")
        async def serve_file(file_path: str):
            safe_path = file_path.lstrip("/\\")
            requested = (self.static_dir / safe_path).resolve()
            static_root = self.static_dir.resolve()
            try:
                is_within = requested.is_relative_to(static_root)
            except AttributeError:
                try:
                    requested.relative_to(static_root)
                    is_within = True
                except ValueError:
                    is_within = False
            if not is_within:
                raise HTTPException(status_code=404, detail="File not found")
            if requested.exists() and requested.is_file():
                media_type = "text/html" if requested.suffix == ".html" else None
                return FileResponse(str(requested), media_type=media_type)
            raise HTTPException(status_code=404, detail="File not found")

        return app

    async def start(self):
        """Start the static file server."""
        logger.info(f"Starting Static File Server on {self.host}:{self.port}")
        # Note: In a real implementation, you would use uvicorn to run the app
        # uvicorn.run(self.app, host=self.host, port=self.port)

    async def stop(self):
        """Stop the static file server."""
        logger.info("Stopping Static File Server")
