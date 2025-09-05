"""
ML Quality Prediction Service
============================

Advanced machine learning service for VPN connection quality prediction
using LSTM networks and ensemble methods as outlined in the technical
implementation report.

This module provides a unified interface to the modularized ML system.
"""

from typing import Dict, Any

from .quality_service import QualityPredictionService
from .feature_processor import NetworkMetrics
from .lstm_model import QualityPrediction

# Re-export main classes for backward compatibility
__all__ = [
    'QualityPredictionService',
    'NetworkMetrics',
    'QualityPrediction'
]

# Global service instance
_quality_prediction_service = QualityPredictionService()


async def predict_connection_quality(server_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Predict connection quality for a server.
    
    Args:
        server_metrics: Server performance metrics
        
    Returns:
        Quality prediction result
    """
    return await _quality_prediction_service.predict_connection_quality(server_metrics)


def get_quality_prediction_stats() -> Dict[str, Any]:
    """Get quality prediction service statistics."""
    return _quality_prediction_service.get_performance_stats()
