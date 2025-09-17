"""API Server
==========

Main API server implementation.
"""

from typing import Dict, List

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

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
        self._setup_exception_handlers()
        setup_routes(self.app, self.auth_service, self.websocket_manager)

        # Schedule the pipeline to run every 12 hours
        # self.app.add_event_handler("startup", self.start_scheduler)

        logger.info("API server initialized with %d Redis nodes", len(redis_nodes))
        if redis_nodes:
            addresses = ", ".join(f"{n['host']}:{n['port']}" for n in redis_nodes)
            logger.debug("Redis nodes configured: %s", addresses)

    async def start_scheduler(self):
        """
        Starts the background scheduler.
        """
        from ...scheduler import setup_scheduler

        setup_scheduler()

    def _setup_middleware(self) -> None:
        """Setup API middleware."""
        # Trusted host middleware
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"],  # Configure appropriately for production
        )

    def _setup_exception_handlers(self) -> None:
        """Setup global exception handlers for comprehensive error handling."""

        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            """Handle HTTP exceptions with proper logging."""
            logger.warning("HTTP %d: %s - %s", exc.status_code, exc.detail, request.url)
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": exc.detail,
                    "status_code": exc.status_code,
                    "path": str(request.url.path),
                },
            )

        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(
            request: Request, exc: RequestValidationError
        ):
            """Handle validation errors with detailed information."""
            logger.warning("Validation error: %s - %s", exc.errors(), request.url)
            return JSONResponse(
                status_code=422,
                content={
                    "error": "Validation failed",
                    "details": exc.errors(),
                    "path": str(request.url.path),
                },
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            """Handle unexpected exceptions with proper logging."""
            logger.error("Unexpected error: %s - %s", exc, request.url, exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred. Please try again later.",
                    "path": str(request.url.path),
                },
            )

    def run(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        """Run the API server with comprehensive error handling.

        Args:
            host: Host to bind to
            port: Port to bind to
        """
        try:
            logger.info("Starting API server on %s:%d", host, port)
            uvicorn.run(
                self.app,
                host=host,
                port=port,
                log_level="info",
                access_log=True,
                server_header=False,
                date_header=False,
            )
        except Exception as e:
            logger.error("Failed to start API server: %s", e, exc_info=True)
            raise

    def get_app(self) -> FastAPI:
        """Get FastAPI application instance.

        Returns:
            FastAPI application
        """
        return self.app
