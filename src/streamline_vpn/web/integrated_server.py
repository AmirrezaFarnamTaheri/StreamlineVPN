"""
Integrated Web Server
=====================

Integrated web server combining all StreamlineVPN web services.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..utils.logging import get_logger
from .api import create_api_server

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

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Include API routes
        api_app = create_api_server()
        app.mount("/api", api_app)

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
            return {
                "message": "StreamlineVPN Integrated Server",
                "version": "2.0.0",
                "services": {
                    "api": "/api",
                    "graphql": "/graphql",
                    "docs": "/docs",
                },
            }

        return app

    async def start(self):
        """Start the integrated server."""
        logger.info(
            f"Starting Integrated Web Server on {self.host}:{self.port}"
        )
        try:
            import uvicorn
            uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")
        except ImportError:
            logger.warning("uvicorn not available, server not started")
            logger.info("Install uvicorn to run the server: pip install uvicorn")

    async def stop(self):
        """Stop the integrated server."""
        logger.info("Stopping Integrated Web Server")
