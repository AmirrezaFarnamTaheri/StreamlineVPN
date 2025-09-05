"""
Quality Prediction Service
==========================

Main quality prediction service with caching and ML integration.
"""

import asyncio
import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..utils.logging import get_logger
from .feature_processor import NetworkFeatureProcessor, NetworkMetrics
from .lstm_model import LSTMModel, QualityPrediction
from ..core.cache_manager import CacheManager

logger = get_logger(__name__)


class QualityPredictionService:
    """Main quality prediction service with caching and ML integration."""
    
    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        feature_processor: Optional[NetworkFeatureProcessor] = None,
        lstm_model: Optional[LSTMModel] = None,
        cache_ttl: int = 60
    ):
        """Initialize quality prediction service.
        
        Args:
            cache_ttl: Cache TTL in seconds
        """
        self.cache_ttl = cache_ttl
        self.feature_processor = feature_processor or NetworkFeatureProcessor()
        self.lstm_model = lstm_model or LSTMModel()
        self.cache_manager = cache_manager
        self.metrics_history = {}
        self.performance_stats = {
            "predictions_made": 0,
            "cache_hits": 0,
            "avg_prediction_time": 0.0
        }
    
    async def predict_connection_quality(self, server_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Predict connection quality for a server.
        
        Args:
            server_metrics: Server performance metrics
            
        Returns:
            Quality prediction result
        """
        start_time = time.perf_counter()
        
        try:
            # Extract features from server metrics
            features = self.feature_processor.extract_features(
                self._convert_to_metrics(server_metrics)
            )
            
            # Check cache first
            cache_key = self._generate_cache_key(features)
            if self.cache_manager:
                cached_result = await self.cache_manager.get(cache_key)
                if cached_result:
                    self.performance_stats["cache_hits"] += 1
                    return cached_result
            
            # Run ML prediction
            prediction = await self.lstm_model.predict(features)
            
            # Cache result
            result = {
                'predicted_latency': prediction.predicted_latency,
                'bandwidth_estimate': prediction.bandwidth_estimate,
                'reliability_score': prediction.reliability_score,
                'confidence': prediction.confidence,
                'quality_grade': prediction.quality_grade,
                'recommendations': prediction.recommendations,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if self.cache_manager:
                await self.cache_manager.set(cache_key, result, ttl=self.cache_ttl)
            
            # Update performance statistics
            prediction_time = time.perf_counter() - start_time
            self._update_performance_stats(prediction_time)
            
            logger.info(f"Quality prediction completed in {prediction_time*1000:.2f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Quality prediction failed: {e}")
            return self._get_default_prediction()
    
    def _convert_to_metrics(self, server_metrics: Dict[str, Any]) -> List[NetworkMetrics]:
        """Convert server metrics to NetworkMetrics objects."""
        metrics = []
        
        # Extract time series data
        time_series = server_metrics.get('time_series_data', [])
        
        for data_point in time_series:
            metric = NetworkMetrics(
                timestamp=datetime.fromisoformat(data_point.get('timestamp', datetime.utcnow().isoformat())),
                server_id=server_metrics.get('server_id', ''),
                latency=data_point.get('latency', 0.0),
                bandwidth_up=data_point.get('bandwidth_up', 0.0),
                bandwidth_down=data_point.get('bandwidth_down', 0.0),
                packet_loss=data_point.get('packet_loss', 0.0),
                jitter=data_point.get('jitter', 0.0),
                connection_duration=data_point.get('connection_duration', 0),
                bytes_transferred=data_point.get('bytes_transferred', 0),
                protocol=server_metrics.get('protocol', ''),
                region=server_metrics.get('region', '')
            )
            metrics.append(metric)
        
        return metrics
    
    def _generate_cache_key(self, features: Dict[str, float]) -> str:
        """Generate cache key from features."""
        # Create hash of normalized features
        feature_str = json.dumps(features, sort_keys=True)
        return f"ml_prediction:{hashlib.md5(feature_str.encode()).hexdigest()}"
    
    def _update_performance_stats(self, prediction_time: float) -> None:
        """Update performance statistics."""
        self.performance_stats["predictions_made"] += 1
        
        # Update average prediction time using exponential moving average
        alpha = 0.1
        current_avg = self.performance_stats["avg_prediction_time"]
        self.performance_stats["avg_prediction_time"] = (
            alpha * prediction_time + (1 - alpha) * current_avg
        )
    
    def _get_default_prediction(self) -> Dict[str, Any]:
        """Get default prediction when ML fails."""
        return {
            'predicted_latency': 100.0,
            'bandwidth_estimate': 10.0,
            'reliability_score': 0.7,
            'confidence': 0.5,
            'quality_grade': 'C',
            'recommendations': ['Unable to predict quality - using default values'],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get service performance statistics."""
        return self.performance_stats.copy()
    
    async def clear_cache(self) -> None:
        """Clear prediction cache."""
        if self.cache_manager:
            # This is not ideal as it would clear all caches, not just the ML cache.
            # A better solution would be to use a separate Redis database or a key prefix for the ML cache.
            # For now, we'll just clear the whole cache.
            await self.cache_manager.clear()
            logger.info("Quality prediction cache cleared")
