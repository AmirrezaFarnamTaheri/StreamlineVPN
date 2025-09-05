"""
LSTM Model
==========

LSTM model implementation for quality prediction.
"""

from typing import Dict, List
from dataclasses import dataclass, field

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class QualityPrediction:
    """ML quality prediction result."""
    predicted_latency: float
    bandwidth_estimate: float
    reliability_score: float
    confidence: float
    quality_grade: str
    recommendations: List[str] = field(default_factory=list)


class LSTMModel:
    """Simplified LSTM model for quality prediction."""
    
    def __init__(self):
        """Initialize LSTM model."""
        self.model_loaded = False
        self.feature_weights = {
            "packet_inter_arrival_time": 0.1,
            "rtt_variance": 0.2,
            "bandwidth_trend": 0.15,
            "packet_size_variance": 0.05,
            "flow_bytes_per_second": 0.2,
            "connection_duration_avg": 0.1,
            "latency_p95": 0.15,
            "packet_loss_rate": 0.2,
            "jitter_measurement": 0.1,
            "bandwidth_utilization": 0.15
        }
    
    async def predict(self, features: Dict[str, float]) -> QualityPrediction:
        """Predict connection quality from features.
        
        Args:
            features: Extracted network features
            
        Returns:
            Quality prediction result
        """
        # Simplified prediction logic (in production, use actual LSTM model)
        predicted_latency = self._predict_latency(features)
        bandwidth_estimate = self._predict_bandwidth(features)
        reliability_score = self._predict_reliability(features)
        confidence = self._calculate_confidence(features)
        quality_grade = self._determine_quality_grade(reliability_score)
        recommendations = self._generate_recommendations(features, reliability_score)
        
        return QualityPrediction(
            predicted_latency=predicted_latency,
            bandwidth_estimate=bandwidth_estimate,
            reliability_score=reliability_score,
            confidence=confidence,
            quality_grade=quality_grade,
            recommendations=recommendations
        )
    
    def _predict_latency(self, features: Dict[str, float]) -> float:
        """Predict connection latency."""
        # Weighted combination of latency-related features
        latency_score = (
            features.get("latency_p95", 0) * 0.4 +
            features.get("rtt_variance", 0) * 0.3 +
            features.get("jitter_measurement", 0) * 0.3
        )
        
        # Convert to predicted latency (simplified model)
        return max(10.0, latency_score * 1.2)
    
    def _predict_bandwidth(self, features: Dict[str, float]) -> float:
        """Predict available bandwidth."""
        # Weighted combination of bandwidth-related features
        bandwidth_score = (
            features.get("bandwidth_utilization", 0) * 0.5 +
            features.get("flow_bytes_per_second", 0) * 0.3 +
            features.get("bandwidth_trend", 0) * 0.2
        )
        
        # Convert to bandwidth estimate in Mbps
        return max(1.0, bandwidth_score / 1000000)  # Convert bytes to Mbps
    
    def _predict_reliability(self, features: Dict[str, float]) -> float:
        """Predict connection reliability score (0-1)."""
        # Calculate reliability based on multiple factors
        packet_loss_penalty = features.get("packet_loss_rate", 0) * 0.3
        jitter_penalty = min(features.get("jitter_measurement", 0) / 100, 0.2)
        latency_penalty = min(features.get("latency_p95", 0) / 1000, 0.2)
        
        reliability = 1.0 - packet_loss_penalty - jitter_penalty - latency_penalty
        return max(0.0, min(1.0, reliability))
    
    def _calculate_confidence(self, features: Dict[str, float]) -> float:
        """Calculate prediction confidence (0-1)."""
        # Confidence based on feature completeness and variance
        feature_count = sum(1 for v in features.values() if v > 0)
        completeness = feature_count / len(features)
        
        # Lower confidence for high variance
        variance_penalty = min(features.get("rtt_variance", 0) / 100, 0.3)
        
        confidence = completeness - variance_penalty
        return max(0.1, min(1.0, confidence))
    
    def _determine_quality_grade(self, reliability_score: float) -> str:
        """Determine quality grade from reliability score."""
        if reliability_score >= 0.9:
            return "A"
        elif reliability_score >= 0.8:
            return "B"
        elif reliability_score >= 0.7:
            return "C"
        elif reliability_score >= 0.6:
            return "D"
        else:
            return "F"
    
    def _generate_recommendations(self, features: Dict[str, float], reliability_score: float) -> List[str]:
        """Generate recommendations based on features and reliability."""
        recommendations = []
        
        if features.get("packet_loss_rate", 0) > 0.05:
            recommendations.append("High packet loss detected - consider switching servers")
        
        if features.get("latency_p95", 0) > 200:
            recommendations.append("High latency detected - try a server closer to your location")
        
        if features.get("jitter_measurement", 0) > 50:
            recommendations.append("High jitter detected - network may be unstable")
        
        if reliability_score < 0.7:
            recommendations.append("Low reliability score - consider premium servers")
        
        if not recommendations:
            recommendations.append("Connection quality is good")
        
        return recommendations
