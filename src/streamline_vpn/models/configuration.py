"""
VPN Configuration Model
=======================

Data model for VPN configurations with validation and serialization.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import json


class Protocol(Enum):
    """Supported VPN protocols."""

    VMESS = "vmess"
    VLESS = "vless"
    TROJAN = "trojan"
    SHADOWSOCKS = "ss"
    SHADOWSOCKSR = "ssr"
    HYSTERIA = "hysteria"
    HYSTERIA2 = "hysteria2"
    TUIC = "tuic"


# Alias for backward compatibility
ProtocolType = Protocol


@dataclass
class VPNConfiguration:
    """VPN configuration data model.

    Attributes:
        protocol: VPN protocol type
        server: Server address
        port: Server port
        user_id: User ID (for VMess/VLESS)
        password: Password (for Trojan/Shadowsocks)
        encryption: Encryption method
        network: Network type (tcp/ws/grpc)
        path: Path for websocket/grpc
        host: Host header
        tls: TLS configuration
        quality_score: ML-predicted quality score
        source_url: Source URL where this config was found
        created_at: Creation timestamp
        metadata: Additional metadata
    """

    protocol: Protocol
    server: str
    port: int
    user_id: Optional[str] = None
    password: Optional[str] = None
    encryption: Optional[str] = None
    network: str = "tcp"
    path: Optional[str] = None
    host: Optional[str] = None
    tls: bool = False
    quality_score: float = 0.0
    source_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Generate ID and validate configuration after initialization."""
        if not hasattr(self, "id") or not self.id:
            # Generate a unique ID based on configuration content
            import hashlib

            content = f"{self.protocol.value}:{self.server}:{self.port}:{self.user_id or ''}:{self.password or ''}"
            self.id = hashlib.md5(content.encode()).hexdigest()[:8]

        if not self.server:
            raise ValueError("Server address is required")
        if not (1 <= self.port <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        if self.quality_score < 0 or self.quality_score > 1:
            raise ValueError("Quality score must be between 0 and 1")

    @property
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        try:
            self.__post_init__()
            return True
        except ValueError:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "protocol": self.protocol.value,
            "server": self.server,
            "port": self.port,
            "user_id": self.user_id,
            "password": self.password,
            "encryption": self.encryption,
            "network": self.network,
            "path": self.path,
            "host": self.host,
            "tls": self.tls,
            "quality_score": self.quality_score,
            "source_url": self.source_url,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VPNConfiguration":
        """Create from dictionary."""
        data = data.copy()
        data["protocol"] = ProtocolType(data["protocol"])
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "VPNConfiguration":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def __str__(self) -> str:
        """String representation."""
        return f"{self.protocol.value}://{self.server}:{self.port}"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"VPNConfiguration(protocol={self.protocol.value}, "
            f"server={self.server}, port={self.port}, "
            f"quality_score={self.quality_score:.2f})"
        )
