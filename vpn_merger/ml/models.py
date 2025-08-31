"""
ML Models and Data Structures
============================

Data models and constants for the ML quality prediction system.
"""

import logging
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Constants
DEFAULT_BUFFER_SIZE = 1000
DEFAULT_FEATURE_SELECTION_K = 20
DEFAULT_CROSS_VALIDATION_FOLDS = 5
DEFAULT_RANDOM_STATE = 42
DEFAULT_N_ESTIMATORS = 100
DEFAULT_RIDGE_ALPHA = 1.0

# Protocol patterns
PROTOCOL_PATTERNS = {
    'vmess': 'vmess://',
    'vless': 'vless://',
    'trojan': 'trojan://',
    'shadowsocks': 'ss://',
    'hysteria': 'hysteria://',
    'tuic': 'tuic://'
}

# Common ports for quality assessment
COMMON_PORTS = ['443', '80', '8080', '8443']

# Special characters for complexity assessment
SPECIAL_CHARS = '!@#$%^&*()_+-=[]{}|;:,.<>?'


@dataclass
class ModelMetrics:
    """Model performance metrics."""
    r2_score: float
    mse: float
    mae: float
    training_samples: int
    validation_samples: int
    last_updated: datetime
    model_version: str


@dataclass
class DriftDetection:
    """Drift detection results."""
    drift_detected: bool
    confidence: float
    drift_type: str
    affected_features: List[str]
    timestamp: datetime


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for ML processing."""
        return {
            'config_length': self.config_length,
            'protocol_score': self.protocol_score,
            'port_score': self.port_score,
            'complexity_score': self.complexity_score,
            'encryption_score': self.encryption_score,
            'network_score': self.network_score,
            'security_score': self.security_score,
            'source_reliability': self.source_reliability,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class PredictionResult:
    """Prediction result with confidence."""
    quality_score: float
    confidence: float
    features_used: List[str]
    model_version: str
    timestamp: datetime
    metadata: Dict[str, Any]
