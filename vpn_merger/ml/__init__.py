"""
Machine Learning Module
======================

Machine learning components for VPN configuration quality prediction and analysis.
"""

from .quality_predictor import QualityPredictor
from .feature_extractor import FeatureExtractor
from .models.base_model import BaseMLModel, ModelMetrics, DriftDetection

# Legacy import for backward compatibility
try:
    from .quality_predictor_enhanced import EnhancedConfigQualityPredictor
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False

__all__ = [
    'QualityPredictor',
    'FeatureExtractor',
    'BaseMLModel',
    'ModelMetrics',
    'DriftDetection',
    'EnhancedConfigQualityPredictor',
    'ENHANCED_AVAILABLE'
]
