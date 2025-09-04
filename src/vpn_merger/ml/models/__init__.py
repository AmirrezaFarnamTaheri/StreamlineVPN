"""
ML Models Module
===============

Machine learning models for VPN configuration quality prediction.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .base_model import BaseMLModel, DriftDetection, ModelMetrics

# Constants (mirrored from legacy vpn_merger/ml/models.py to avoid circular imports)
DEFAULT_BUFFER_SIZE = 1000
DEFAULT_FEATURE_SELECTION_K = 20
DEFAULT_CROSS_VALIDATION_FOLDS = 5
DEFAULT_RANDOM_STATE = 42
DEFAULT_N_ESTIMATORS = 100
DEFAULT_RIDGE_ALPHA = 1.0

PROTOCOL_PATTERNS = {
    "vmess": "vmess://",
    "vless": "vless://",
    "trojan": "trojan://",
    "shadowsocks": "ss://",
    "hysteria": "hysteria://",
    "tuic": "tuic://",
}

COMMON_PORTS = ["443", "80", "8080", "8443"]

SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"


@dataclass
class FeatureVector:
    config_length: int
    protocol_score: float
    port_score: float
    complexity_score: float
    encryption_score: float
    network_score: float
    security_score: float
    source_reliability: float
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
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


@dataclass
class PredictionResult:
    quality_score: float
    confidence: float
    features_used: list[str]
    model_version: str
    timestamp: datetime
    metadata: dict[str, Any]


__all__ = [
    "BaseMLModel",
    "DriftDetection",
    "ModelMetrics",
    "DEFAULT_BUFFER_SIZE",
    "DEFAULT_FEATURE_SELECTION_K",
    "DEFAULT_CROSS_VALIDATION_FOLDS",
    "DEFAULT_RANDOM_STATE",
    "DEFAULT_N_ESTIMATORS",
    "DEFAULT_RIDGE_ALPHA",
    "FeatureVector",
    "PredictionResult",
    "PROTOCOL_PATTERNS",
    "COMMON_PORTS",
    "SPECIAL_CHARS",
]
