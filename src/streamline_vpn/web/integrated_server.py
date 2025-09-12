"""
Integrated Web Server
=====================

Integrated web server combining all StreamlineVPN web services.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..utils.logging import get_logger
from ..settings import get_settings

logger = get_logger(__name__)


class IntegratedWebServer:
    """Integrated web server for all StreamlineVPN services."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        """Initialize integrated server.

        Args:
            host: Host to bind to
            port: Port to bind to
        """
        self.host = host
        self.port = port
        self.app = self._create_integrated_app()

    def _create_integrated_app(self) -> FastAPI:
        """Create integrated FastAPI application."""
        app = FastAPI(
            title="StreamlineVPN Integrated Server",
            description="Complete StreamlineVPN web interface",
            version="2.0.0",
        )

        # Add CORS middleware (restrict in production via settings)
        settings = get_settings()
        allow_origins = settings.allowed_origins
        allow_credentials = settings.allow_credentials
        allow_methods = settings.allowed_methods
        allow_headers = settings.allowed_headers

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=allow_credentials,
            allow_methods=allow_methods,
            allow_headers=allow_headers,
            max_age=3600,
        )

        # Include API routes (commented out - use unified_api.py instead)
        # api_app = create_api_server()
        # app.mount("/api", api_app)

        # Include GraphQL routes (if available)
        try:
            from .graphql import create_graphql_app
            graphql_app = create_graphql_app()
            app.mount("/graphql", graphql_app)
        except ImportError:
            logger.warning("GraphQL not available, skipping GraphQL routes")

        # Root endpoint
        @app.get("/")
        async def root():
            """Root endpoint for integrated server."""
            return {"message": "StreamlineVPN Integrated Server", "version": "2.0.0"}

        return app

    async def start(self):
        """Start the integrated server."""
        logger.info(
            "Starting Integrated Web Server on %s:%d", self.host, self.port
        )
        try:
            import uvicorn
            logger.info("Starting server with uvicorn")
            uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")
        except ImportError:
            logger.error("uvicorn not available, server not started")
            logger.info("Install uvicorn to run the server: pip install uvicorn")
        except Exception as exc:
            logger.error("Failed to start integrated server: %s", exc, exc_info=True)

    async def stop(self):
        """Stop the integrated server."""
        logger.info("Stopping Integrated Web Server")
