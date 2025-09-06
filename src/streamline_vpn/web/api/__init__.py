"""
API Module
==========

Modern RESTful API with JWT authentication and WebSocket real-time updates.
"""

from .models import (
    UserTier,
    ConnectionStatus,
    User,
    VPNServer,
    VPNConnection,
    LoginRequest,
    LoginResponse,
    ServerRecommendationRequest,
    ServerRecommendationResponse,
    ConnectionRequest,
    ConnectionResponse,
    VPNStatusResponse,
    WebSocketMessage,
)
from .auth import AuthenticationService
from .routes import setup_routes
from .websocket import WebSocketManager
from .server import APIServer
from ...constants import DEFAULT_REDIS_NODES, DEFAULT_JWT_SECRET_KEY


def create_app(
    secret_key: str = DEFAULT_JWT_SECRET_KEY, redis_nodes: list = None
) -> APIServer:
    """Create API server instance.

    Args:
        secret_key: JWT secret key
        redis_nodes: Redis cluster nodes

    Returns:
        APIServer instance
    """
    if redis_nodes is None:
        redis_nodes = DEFAULT_REDIS_NODES

    return APIServer(secret_key, redis_nodes)


__all__ = [
    "UserTier",
    "ConnectionStatus",
    "User",
    "VPNServer",
    "VPNConnection",
    "LoginRequest",
    "LoginResponse",
    "ServerRecommendationRequest",
    "ServerRecommendationResponse",
    "ConnectionRequest",
    "ConnectionResponse",
    "VPNStatusResponse",
    "WebSocketMessage",
    "AuthenticationService",
    "setup_routes",
    "WebSocketManager",
    "APIServer",
    "create_app",
]
