"""
ML Quality Prediction Service
============================

Advanced machine learning service for VPN connection quality prediction
using LSTM networks and ensemble methods as outlined in the technical
implementation report.

This module provides a unified interface to the modularized ML system.
"""

from typing import Dict, Any

from typing import Dict, Any

from .quality_service import QualityPredictionService
from .feature_processor import NetworkFeatureProcessor
from .lstm_model import QualityPrediction, LSTMModel
from ..core.cache_manager import CacheManager
from ..settings import get_settings

# Re-export main classes for backward compatibility
__all__ = [
    "QualityPredictionService",
    "QualityPrediction",
    "create_quality_prediction_service",
]

_quality_prediction_service_instance = None


def create_quality_prediction_service() -> QualityPredictionService:
    """Factory function to create a quality prediction service."""
    global _quality_prediction_service_instance
    if _quality_prediction_service_instance is None:
        settings = get_settings()
        cache_manager = CacheManager(redis_nodes=settings.redis.nodes)
        feature_processor = NetworkFeatureProcessor()
        lstm_model = LSTMModel()
        _quality_prediction_service_instance = QualityPredictionService(
            cache_manager=cache_manager,
            feature_processor=feature_processor,
            lstm_model=lstm_model,
        )
    return _quality_prediction_service_instance


async def predict_connection_quality(
    server_metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """Predict connection quality for a server."""
    service = create_quality_prediction_service()
    return await service.predict_connection_quality(server_metrics)


def get_quality_prediction_stats() -> Dict[str, Any]:
    """Get quality prediction service statistics."""
    service = create_quality_prediction_service()
    return service.get_performance_stats()
