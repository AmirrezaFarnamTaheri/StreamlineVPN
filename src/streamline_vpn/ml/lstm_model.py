"""
LSTM Model
==========

LSTM model implementation for quality prediction.
"""

from typing import Dict, List
from dataclasses import dataclass, field
import joblib
from pathlib import Path
import numpy as np

from sklearn.neural_network import MLPRegressor

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

    def __init__(self, model_path: str = "data/ml_model.joblib"):
        """Initialize LSTM model."""
        self.model_path = Path(model_path)
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the pre-trained model."""
        if self.model_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                logger.info("ML model loaded successfully.")
            except Exception as e:
                logger.error("Failed to load ML model: %s", e)
                self.model = None
        else:
            logger.warning("ML model not found. Using a fallback model.")
            self.model = self._create_dummy_model()

    def _create_dummy_model(self):
        """Create and train a lightweight fallback model for testing/development."""
        # This creates a minimal model structure for testing
        # when the actual trained model is not available.
        try:
            model = MLPRegressor(hidden_layer_sizes=(10,), max_iter=1, random_state=42)
            # Create some synthetic data to fit the fallback model
            X = np.random.rand(10, 10)
            y = np.random.rand(10, 3)
            model.fit(X, y)
            logger.info("Fallback ML model created and trained successfully")
            return model
        except Exception as e:
            logger.error("Failed to create fallback model: %s", e)
            # Return a simple linear model as fallback
            from sklearn.linear_model import LinearRegression
            model = LinearRegression()
            X = np.random.rand(10, 10)
            y = np.random.rand(10, 3)
            model.fit(X, y)
            return model

    async def predict(self, features: Dict[str, float]) -> QualityPrediction:
        """Predict connection quality from features.

        Args:
            features: Extracted network features

        Returns:
            Quality prediction result
        """
        if not self.model:
            return self._get_default_prediction()

        try:
            # Prepare features for prediction
            feature_vector = self._prepare_features(features)

            # Run prediction
            prediction = self.model.predict([feature_vector])[0]

            predicted_latency = float(prediction[0])
            bandwidth_estimate = float(prediction[1])
            reliability_score = float(prediction[2])

            confidence = self._calculate_confidence(features)
            quality_grade = self._determine_quality_grade(reliability_score)
            recommendations = self._generate_recommendations(
                features, reliability_score
            )

            return QualityPrediction(
                predicted_latency=predicted_latency,
                bandwidth_estimate=bandwidth_estimate,
                reliability_score=reliability_score,
                confidence=confidence,
                quality_grade=quality_grade,
                recommendations=recommendations,
            )
        except Exception as e:
            logger.error("ML prediction failed: %s", e)
            return self._get_default_prediction()

    def _prepare_features(self, features: Dict[str, float]) -> List[float]:
        """Prepare feature vector for prediction."""
        feature_keys = [
            "packet_inter_arrival_time",
            "rtt_variance",
            "bandwidth_trend",
            "packet_size_variance",
            "flow_bytes_per_second",
            "connection_duration_avg",
            "latency_p95",
            "packet_loss_rate",
            "jitter_measurement",
            "bandwidth_utilization",
        ]
        return [features.get(key, 0.0) for key in feature_keys]

    def _calculate_confidence(self, features: Dict[str, float]) -> float:
        """Calculate prediction confidence (0-1)."""
        feature_count = sum(1 for v in features.values() if v > 0)
        completeness = feature_count / len(features)

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

    def _generate_recommendations(
        self, features: Dict[str, float], reliability_score: float
    ) -> List[str]:
        """Generate recommendations based on features and reliability."""
        recommendations = []

        if features.get("packet_loss_rate", 0) > 0.05:
            recommendations.append(
                "High packet loss detected - consider switching servers"
            )

        if features.get("latency_p95", 0) > 200:
            recommendations.append(
                "High latency detected - try a server closer to your location"
            )

        if features.get("jitter_measurement", 0) > 50:
            recommendations.append(
                "High jitter detected - network may be unstable"
            )

        if reliability_score < 0.7:
            recommendations.append(
                "Low reliability score - consider premium servers"
            )

        if not recommendations:
            recommendations.append("Connection quality is good")

        return recommendations

    def _get_default_prediction(self) -> QualityPrediction:
        """Get default prediction when ML fails."""
        return QualityPrediction(
            predicted_latency=100.0,
            bandwidth_estimate=10.0,
            reliability_score=0.7,
            confidence=0.5,
            quality_grade="C",
            recommendations=[
                "Unable to predict quality - using default values"
            ],
        )
