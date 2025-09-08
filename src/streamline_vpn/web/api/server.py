"""API Server
==========

Main API server implementation.
"""

from typing import Dict, List

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from ...scheduler import setup_scheduler
from ...utils.logging import get_logger
from .auth import AuthenticationService
from .routes import setup_routes
from .websocket import WebSocketManager

logger = get_logger(__name__)


class APIServer:
    """Main API server with authentication and real-time features."""

    def __init__(self, secret_key: str, redis_nodes: List[Dict[str, str]]):
        """Initialize API server.

        Args:
            secret_key: JWT secret key
            redis_nodes: Redis cluster nodes
        """
        self.secret_key = secret_key
        self.redis_nodes = redis_nodes

        # Initialize FastAPI app
        self.app = FastAPI(
            title="StreamlineVPN API",
            description="High-performance VPN management API",
            version="1.0.0",
        )

        # Initialize services
        self.auth_service = AuthenticationService(secret_key)
        self.websocket_manager = WebSocketManager()

        # Setup middleware and routes
        self._setup_middleware()
        setup_routes(self.app, self.auth_service, self.websocket_manager)

        # Schedule the pipeline to run every 12 hours
        self.app.add_event_handler("startup", self.start_scheduler)

        logger.info("API server initialized")

    async def start_scheduler(self):
        """
        Starts the background scheduler.
        """
        setup_scheduler()

    def _setup_middleware(self) -> None:
        """Setup API middleware."""
        # Trusted host middleware
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"],  # Configure appropriately for production
        )

    def run(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        """Run the API server.

        Args:
            host: Host to bind to
            port: Port to bind to
        """
        logger.info(f"Starting API server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)

    def get_app(self) -> FastAPI:
        """Get FastAPI application instance.

        Returns:
            FastAPI application
        """
        return self.app
