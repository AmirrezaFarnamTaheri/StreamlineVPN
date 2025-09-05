"""
API Routes
==========

FastAPI route definitions for the StreamlineVPN API.
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ...utils.logging import get_logger
from .models import (
    LoginRequest, LoginResponse, ServerRecommendationRequest, ServerRecommendationResponse,
    ConnectionRequest, ConnectionResponse, VPNStatusResponse, User
)
from .auth import AuthenticationService
from .websocket import WebSocketManager

logger = get_logger(__name__)

# Global instances (would be injected in production)
_auth_service: Optional[AuthenticationService] = None
_websocket_manager: Optional[WebSocketManager] = None


def set_auth_service(auth_service: AuthenticationService) -> None:
    """Set global authentication service."""
    global _auth_service
    _auth_service = auth_service


def set_websocket_manager(websocket_manager: WebSocketManager) -> None:
    """Set global WebSocket manager."""
    global _websocket_manager
    _websocket_manager = websocket_manager


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> User:
    """Get current authenticated user."""
    if not _auth_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not initialized"
        )
    
    user = _auth_service.verify_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return user


def setup_routes(app, auth_service: AuthenticationService, websocket_manager: WebSocketManager) -> None:
    """Setup API routes.
    
    Args:
        app: FastAPI application instance
        auth_service: Authentication service
        websocket_manager: WebSocket manager
    """
    set_auth_service(auth_service)
    set_websocket_manager(websocket_manager)
    
    # Authentication routes
    @app.post("/api/v1/auth/login", response_model=LoginResponse)
    async def login(request: LoginRequest):
        """Handle user login."""
        user = await auth_service.authenticate_user(request.username, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        access_token = auth_service.generate_access_token(user)
        refresh_token = auth_service.generate_refresh_token(user)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "tier": user.tier.value
            }
        )
    
    @app.post("/api/v1/auth/refresh")
    async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Handle token refresh."""
        new_token = auth_service.refresh_access_token(credentials.credentials)
        if not new_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_in": 3600
        }
    
    # Server routes
    @app.get("/api/v1/servers")
    async def get_servers(current_user: User = Depends(get_current_user)):
        """Get available VPN servers."""
        # Mock server data
        servers = [
            {
                "id": "server_1",
                "name": "US East Premium",
                "host": "us-east.streamlinevpn.com",
                "port": 443,
                "protocol": "vless",
                "region": "us-east",
                "country": "US",
                "performance_score": 0.95,
                "is_online": True,
                "current_connections": 150,
                "max_connections": 1000
            },
            {
                "id": "server_2",
                "name": "EU West Standard",
                "host": "eu-west.streamlinevpn.com",
                "port": 443,
                "protocol": "shadowsocks2022",
                "region": "eu-west",
                "country": "NL",
                "performance_score": 0.88,
                "is_online": True,
                "current_connections": 75,
                "max_connections": 500
            }
        ]
        return servers
    
    @app.post("/api/v1/servers/recommendations", response_model=ServerRecommendationResponse)
    async def get_server_recommendations(
        request: ServerRecommendationRequest,
        current_user: User = Depends(get_current_user)
    ):
        """Get server recommendations."""
        # Mock recommendations
        recommendations = ["Multiple high-quality servers available"]
        quality_prediction = {
            "predicted_latency": 50.0,
            "bandwidth_estimate": 100.0,
            "reliability_score": 0.95,
            "confidence": 0.9,
            "quality_grade": "A"
        }
        
        servers = [
            {
                "id": "server_1",
                "name": "US East Premium",
                "region": "us-east",
                "protocol": "vless",
                "performance_score": 0.95
            }
        ]
        
        return ServerRecommendationResponse(
            servers=servers,
            recommendations=recommendations,
            quality_prediction=quality_prediction
        )
    
    # Connection routes
    @app.post("/api/v1/connections", response_model=ConnectionResponse)
    async def create_connection(
        request: ConnectionRequest,
        current_user: User = Depends(get_current_user)
    ):
        """Create VPN connection."""
        # Mock connection creation
        connection_id = f"conn_{current_user.id}_{int(time.time())}"
        
        return ConnectionResponse(
            connection_id=connection_id,
            status="connected",
            server={
                "id": request.server_id,
                "name": "US East Premium",
                "host": "us-east.streamlinevpn.com",
                "port": 443,
                "protocol": request.protocol or "vless",
                "region": "us-east"
            },
            estimated_latency=50.0
        )
    
    @app.get("/api/v1/connections/{connection_id}")
    async def get_connection(
        connection_id: str,
        current_user: User = Depends(get_current_user)
    ):
        """Get connection details."""
        # Mock connection data
        return {
            "id": connection_id,
            "status": "connected",
            "server": {
                "id": "server_1",
                "name": "US East Premium",
                "region": "us-east",
                "protocol": "vless"
            },
            "connected_at": "2024-01-01T10:00:00Z",
            "session_duration": 3600,
            "bytes_uploaded": 1024000,
            "bytes_downloaded": 2048000
        }
    
    @app.delete("/api/v1/connections/{connection_id}")
    async def disconnect_connection(
        connection_id: str,
        current_user: User = Depends(get_current_user)
    ):
        """Disconnect VPN connection."""
        return {"status": "disconnected"}
    
    # Status routes
    @app.get("/api/v1/status", response_model=VPNStatusResponse)
    async def get_vpn_status(current_user: User = Depends(get_current_user)):
        """Get VPN status."""
        return VPNStatusResponse(
            connected=True,
            server={
                "id": "server_1",
                "name": "US East Premium",
                "region": "us-east",
                "protocol": "vless"
            },
            bandwidth={"upload": 10.0, "download": 50.0},
            latency=50.0,
            session_duration=3600,
            bytes_transferred={"upload": 1024000, "download": 2048000}
        )
    
    # WebSocket route
    @app.websocket("/ws/{user_id}")
    async def websocket_endpoint(websocket: WebSocket, user_id: str):
        """WebSocket endpoint for real-time updates."""
        await websocket_manager.connect(websocket, user_id)
        
        try:
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                await websocket_manager.handle_message(websocket, user_id, message_data)
        except WebSocketDisconnect:
            await websocket_manager.disconnect(user_id)
    
    # Health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    
    # Metrics endpoint
    @app.get("/metrics")
    async def get_metrics():
        """Get Prometheus metrics."""
        # This would return actual metrics in production
        return "# StreamlineVPN Metrics\n# (metrics would be implemented here)"
