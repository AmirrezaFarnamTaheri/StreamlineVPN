"""
Machine Learning Module
======================

Machine learning components for VPN configuration quality prediction and analysis.
"""

from .feature_extractor import FeatureExtractor
from .models.base_model import BaseMLModel, DriftDetection, ModelMetrics
from .quality_predictor import QualityPredictor

# Legacy import for backward compatibility
try:
    from .quality_predictor_enhanced import EnhancedConfigQualityPredictor

    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False

__all__ = [
    "ENHANCED_AVAILABLE",
    "BaseMLModel",
    "DriftDetection",
    "EnhancedConfigQualityPredictor",
    "FeatureExtractor",
    "ModelMetrics",
    "QualityPredictor",
]
