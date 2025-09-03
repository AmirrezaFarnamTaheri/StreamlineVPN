"""
ML Models Module
===============

Machine learning models for VPN configuration quality prediction.
"""

from .base_model import BaseMLModel, DriftDetection, ModelMetrics
from dataclasses import dataclass
from datetime import datetime

# Constants for feature extraction
COMMON_PORTS = {
    "80", "443", "8080", "8443", "22", "21", "25", "110", "143", "993", "995"
}

PROTOCOL_PATTERNS = {
    "vless": "vless://",
    "vmess": "vmess://", 
    "trojan": "trojan://",
    "shadowsocks": "ss://",
    "hysteria": "hysteria://",
    "tuic": "tuic://"
}

SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;':\",./<>?"

@dataclass
class FeatureVector:
    """Feature vector for ML prediction."""
    config_length: int
    protocol_score: float
    port_score: float
    complexity_score: float
    encryption_score: float
    network_score: float
    security_score: float
    source_reliability: float
    timestamp: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for ML processing."""
        return {
            "config_length": self.config_length,
            "protocol_score": self.protocol_score,
            "port_score": self.port_score,
            "complexity_score": self.complexity_score,
            "encryption_score": self.encryption_score,
            "network_score": self.network_score,
            "security_score": self.security_score,
            "source_reliability": self.source_reliability,
        }

    def to_array(self) -> list[float]:
        """Convert to array for ML processing."""
        return [
            self.config_length,
            self.protocol_score,
            self.port_score,
            self.complexity_score,
            self.encryption_score,
            self.network_score,
            self.security_score,
            self.source_reliability,
        ]

__all__ = [
    "BaseMLModel", 
    "DriftDetection", 
    "ModelMetrics",
    "FeatureVector",
    "COMMON_PORTS",
    "PROTOCOL_PATTERNS", 
    "SPECIAL_CHARS"
]
