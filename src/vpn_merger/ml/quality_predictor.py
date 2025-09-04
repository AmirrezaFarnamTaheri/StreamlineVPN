"""
Quality Predictor
================

Simplified quality predictor for VPN configurations using machine learning.
"""

import logging
from datetime import datetime

import numpy as np

from .feature_extractor import FeatureExtractor
from .models.base_model import BaseMLModel, ModelMetrics

logger = logging.getLogger(__name__)


class QualityPredictor(BaseMLModel):
    """Quality predictor for VPN configurations."""

    def __init__(self, model_name: str = "quality_predictor"):
        """Initialize quality predictor.

        Args:
            model_name: Name of the model
        """
        super().__init__(model_name)
        self.feature_extractor = FeatureExtractor()
        self.feature_names = self.feature_extractor.get_feature_names()

        # Initialize ML components
        try:
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
            from sklearn.preprocessing import StandardScaler

            self.model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            self.scaler = StandardScaler()

        except ImportError as e:
            logger.warning(f"scikit-learn not available: {e}")
            self.model = None
            self.scaler = None

    def train(self, configs: list[str], quality_scores: list[float], **kwargs) -> ModelMetrics:
        """Train the quality predictor.

        Args:
            configs: List of VPN configuration strings
            quality_scores: List of quality scores (0.0 to 1.0)
            **kwargs: Additional training parameters

        Returns:
            Model performance metrics
        """
        if not configs or not quality_scores:
            raise ValueError("Configs and quality_scores cannot be empty")

        if len(configs) != len(quality_scores):
            raise ValueError("Configs and quality_scores must have the same length")

        if self.model is None:
            raise RuntimeError("ML model not available - scikit-learn required")

        try:
            # Extract features
            features_list = self.feature_extractor.extract_batch_features(configs)
            X = np.array([[f[name] for name in self.feature_names] for f in features_list])
            y = np.array(quality_scores)

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train model
            self.model.fit(X_scaled, y)
            self.is_trained = True
            self.last_training_time = datetime.now()

            # Calculate metrics
            y_pred = self.model.predict(X_scaled)
            metrics = self._calculate_metrics(y, y_pred, len(configs), 0)

            # Store training history
            self.training_history.append(
                {"timestamp": self.last_training_time, "samples": len(configs), "metrics": metrics}
            )

            logger.info(f"Model trained with {len(configs)} samples")
            return metrics

        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise

    def predict(self, configs: list[str]) -> np.ndarray:
        """Predict quality scores for configurations.

        Args:
            configs: List of VPN configuration strings

        Returns:
            Array of predicted quality scores
        """
        if not self.is_trained or self.model is None:
            raise RuntimeError("Model not trained")

        if not configs:
            return np.array([])

        try:
            # Extract features
            features_list = self.feature_extractor.extract_batch_features(configs)
            X = np.array([[f[name] for name in self.feature_names] for f in features_list])

            # Scale features
            X_scaled = self.scaler.transform(X)

            # Make predictions
            predictions = self.model.predict(X_scaled)

            # Ensure predictions are in valid range [0, 1]
            predictions = np.clip(predictions, 0.0, 1.0)

            return predictions

        except Exception as e:
            logger.error(f"Error making predictions: {e}")
            raise

    def predict_single(self, config: str) -> float:
        """Predict quality score for a single configuration.

        Args:
            config: VPN configuration string

        Returns:
            Predicted quality score
        """
        predictions = self.predict([config])
        return float(predictions[0]) if len(predictions) > 0 else 0.0

    def evaluate(self, configs: list[str], quality_scores: list[float]) -> ModelMetrics:
        """Evaluate model performance.

        Args:
            configs: List of VPN configuration strings
            quality_scores: List of true quality scores

        Returns:
            Model performance metrics
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained")

        predictions = self.predict(configs)
        return self._calculate_metrics(quality_scores, predictions, 0, len(configs))

    def _calculate_metrics(
        self, y_true: list[float], y_pred: np.ndarray, train_samples: int, val_samples: int
    ) -> ModelMetrics:
        """Calculate model performance metrics.

        Args:
            y_true: True values
            y_pred: Predicted values
            train_samples: Number of training samples
            val_samples: Number of validation samples

        Returns:
            Model metrics
        """
        try:
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

            mse = mean_squared_error(y_true, y_pred)
            r2 = r2_score(y_true, y_pred)
            mae = mean_absolute_error(y_true, y_pred)

            return ModelMetrics(
                r2_score=r2,
                mse=mse,
                mae=mae,
                training_samples=train_samples,
                validation_samples=val_samples,
                last_updated=datetime.now(),
                model_version="2.0.0",
            )

        except ImportError:
            # Fallback calculation without scikit-learn
            y_true_arr = np.array(y_true)
            y_pred_arr = np.array(y_pred)

            mse = np.mean((y_true_arr - y_pred_arr) ** 2)
            mae = np.mean(np.abs(y_true_arr - y_pred_arr))

            # Simple R² calculation
            ss_res = np.sum((y_true_arr - y_pred_arr) ** 2)
            ss_tot = np.sum((y_true_arr - np.mean(y_true_arr)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

            return ModelMetrics(
                r2_score=r2,
                mse=mse,
                mae=mae,
                training_samples=train_samples,
                validation_samples=val_samples,
                last_updated=datetime.now(),
                model_version="2.0.0",
            )

    def get_feature_importance(self) -> dict[str, float]:
        """Get feature importance scores.

        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not self.is_trained or self.model is None:
            return {}

        try:
            if hasattr(self.model, "feature_importances_"):
                importance_scores = self.model.feature_importances_
                return dict(zip(self.feature_names, importance_scores, strict=False))
            else:
                return {}
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return {}

    def is_available(self) -> bool:
        """Check if ML functionality is available.

        Returns:
            True if ML libraries are available, False otherwise
        """
        try:
            import sklearn

            return True
        except ImportError:
            return False
