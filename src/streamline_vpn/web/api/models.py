"""
API Models
==========

Pydantic models and data classes for the API.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UserTier(Enum):
    """User subscription tiers."""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class ConnectionStatus(Enum):
    """VPN connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    ERROR = "error"


@dataclass
class User:
    """User model."""
    id: str
    username: str
    email: str
    tier: UserTier
    created_at: datetime
    last_login: datetime
    is_active: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60


@dataclass
class VPNServer:
    """VPN server model."""
    id: str
    name: str
    host: str
    port: int
    protocol: str
    region: str
    country: str
    performance_score: float
    is_online: bool
    max_connections: int
    current_connections: int


@dataclass
class VPNConnection:
    """VPN connection model."""
    id: str
    user_id: str
    server_id: str
    status: ConnectionStatus
    connected_at: Optional[datetime]
    bytes_uploaded: int = 0
    bytes_downloaded: int = 0
    session_duration: int = 0


# Pydantic models for API
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


class ServerRecommendationRequest(BaseModel):
    region: Optional[str] = None
    protocol: Optional[str] = None
    max_latency: Optional[float] = None


class ServerRecommendationResponse(BaseModel):
    servers: List[Dict[str, Any]]
    recommendations: List[str]
    quality_prediction: Dict[str, Any]


class ConnectionRequest(BaseModel):
    server_id: str
    protocol: Optional[str] = None


class ConnectionResponse(BaseModel):
    connection_id: str
    status: str
    server: Dict[str, Any]
    estimated_latency: float


class VPNStatusResponse(BaseModel):
    connected: bool
    server: Optional[Dict[str, Any]]
    bandwidth: Dict[str, float]
    latency: float
    session_duration: int
    bytes_transferred: Dict[str, int]


class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: str
