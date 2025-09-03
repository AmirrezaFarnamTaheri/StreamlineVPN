"""
Enhanced ML Quality Predictor for VPN Configuration Assessment
============================================================

Advanced machine learning model for predicting VPN configuration quality
with online learning, drift detection, and hyperparameter optimization.
"""

import asyncio
import json
import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd

# ML Libraries
try:
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.feature_selection import SelectKBest, f_regression
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import GridSearchCV, cross_val_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import RobustScaler, StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available, ML features disabled")

# Optional advanced ML libraries
try:
    import lightgbm as lgb
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
    LIGHTGBM_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    LIGHTGBM_AVAILABLE = False

try:
    from river import drift, stream
    RIVER_AVAILABLE = True
except ImportError:
    RIVER_AVAILABLE = False

from .feature_extractor import FeatureExtractor
from .models import (
    DEFAULT_BUFFER_SIZE,
    DEFAULT_CROSS_VALIDATION_FOLDS,
    DEFAULT_FEATURE_SELECTION_K,
    DEFAULT_N_ESTIMATORS,
    DEFAULT_RANDOM_STATE,
    DEFAULT_RIDGE_ALPHA,
    DriftDetection,
    FeatureVector,
    ModelMetrics,
    PredictionResult,
)

logger = logging.getLogger(__name__)


class EnhancedConfigQualityPredictor:
    """Enhanced ML-based quality predictor for VPN configurations.
    
    This class provides advanced machine learning capabilities for predicting
    VPN configuration quality with online learning, drift detection, and
    hyperparameter optimization.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the enhanced quality predictor.
        
        Args:
            model_path: Path to saved model file
        """
        self.feature_extractor = FeatureExtractor()
        self.model = None
        self.scaler = StandardScaler()
        self.feature_selector = None
        self.drift_detector = None
        self.model_metrics = None
        self.training_buffer = []
        self.model_version = "2.0.0"
        
        # Initialize ML components
        self._initialize_ml_components()
        
        # Load model if path provided
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
    
    def _initialize_ml_components(self):
        """Initialize ML components."""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, using fallback predictor")
            return
        
        # Initialize base model
        self.model = RandomForestRegressor(
            n_estimators=DEFAULT_N_ESTIMATORS,
            random_state=DEFAULT_RANDOM_STATE,
            n_jobs=-1
        )
        
        # Initialize feature selector
        self.feature_selector = SelectKBest(
            score_func=f_regression,
            k=DEFAULT_FEATURE_SELECTION_K
        )
        
        # Initialize drift detector if available
        if RIVER_AVAILABLE:
            self.drift_detector = drift.ADWIN()
        
    async def predict_quality(self, config: str, source_reliability: float = 0.5) -> PredictionResult:
        """Predict quality score for a VPN configuration.
        
        Args:
            config: VPN configuration string
            source_reliability: Reliability score of the source
            
        Returns:
            PredictionResult with quality score and confidence
        """
        try:
            # Extract features
            feature_vector = self.feature_extractor.extract_features(config, source_reliability)
            
            # Convert to ML format
            features = self._prepare_features_for_prediction(feature_vector)
            
            if self.model is None:
                # Fallback to rule-based prediction
                return self._fallback_prediction(feature_vector)
            
            # Make prediction
            quality_score = self.model.predict([features])[0]
            confidence = self._calculate_prediction_confidence(features)
            
            return PredictionResult(
                quality_score=max(0.0, min(1.0, quality_score)),
                confidence=confidence,
                features_used=list(feature_vector.to_dict().keys()),
                model_version=self.model_version,
                timestamp=datetime.now(),
                metadata={'source_reliability': source_reliability}
            )
            
        except Exception as e:
            logger.error(f"Error predicting quality: {e}")
            return self._create_error_prediction()
    
    def _prepare_features_for_prediction(self, feature_vector: FeatureVector) -> List[float]:
        """Prepare features for ML prediction."""
        feature_dict = feature_vector.to_dict()
        # Remove timestamp and convert to list
        feature_dict.pop('timestamp', None)
        return list(feature_dict.values())
    
    def _fallback_prediction(self, feature_vector: FeatureVector) -> PredictionResult:
        """Fallback prediction when ML model is not available."""
        # Simple weighted average of features
        weights = [0.2, 0.15, 0.1, 0.15, 0.15, 0.1, 0.15]
        features = [
            feature_vector.protocol_score,
            feature_vector.port_score,
            feature_vector.complexity_score,
            feature_vector.encryption_score,
            feature_vector.network_score,
            feature_vector.security_score,
            feature_vector.source_reliability
        ]
        
        quality_score = sum(w * f for w, f in zip(weights, features))
        
        return PredictionResult(
            quality_score=max(0.0, min(1.0, quality_score)),
            confidence=0.6,  # Lower confidence for fallback
            features_used=['fallback_rule_based'],
            model_version='fallback',
            timestamp=datetime.now(),
            metadata={'method': 'fallback'}
        )
    
    def _calculate_prediction_confidence(self, features: List[float]) -> float:
        """Calculate prediction confidence."""
        # Simple confidence based on feature variance
        if len(features) < 2:
            return 0.5
        
        variance = np.var(features)
        confidence = 1.0 / (1.0 + variance)
        return max(0.1, min(0.95, confidence))
    
    def _create_error_prediction(self) -> PredictionResult:
        """Create error prediction result."""
        return PredictionResult(
            quality_score=0.5,
            confidence=0.0,
            features_used=[],
            model_version=self.model_version,
            timestamp=datetime.now(),
            metadata={'error': True}
        )
    
    async def train_model(self, training_data: List[Tuple[str, float, float]]) -> ModelMetrics:
        """Train the ML model with new data.
        
        Args:
            training_data: List of (config, quality_score, source_reliability) tuples
            
        Returns:
            ModelMetrics with training results
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("Cannot train model: scikit-learn not available")
            return None
        
        try:
            # Extract features and prepare training data
            X, y = [], []
            for config, quality_score, source_reliability in training_data:
                feature_vector = self.feature_extractor.extract_features(config, source_reliability)
                features = self._prepare_features_for_prediction(feature_vector)
                X.append(features)
                y.append(quality_score)
            
            X = np.array(X)
            y = np.array(y)
            
            # Split data for validation
            split_idx = int(0.8 * len(X))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_val_scaled = self.scaler.transform(X_val)
            
            # Select features
            if self.feature_selector:
                X_train_selected = self.feature_selector.fit_transform(X_train_scaled, y_train)
                X_val_selected = self.feature_selector.transform(X_val_scaled)
            else:
                X_train_selected = X_train_scaled
                X_val_selected = X_val_scaled
            
            # Train model
            self.model.fit(X_train_selected, y_train)
            
            # Make predictions
            y_pred = self.model.predict(X_val_selected)
                
                # Calculate metrics
            r2 = r2_score(y_val, y_pred)
            mse = mean_squared_error(y_val, y_pred)
            mae = mean_absolute_error(y_val, y_pred)
            
            # Update model metrics
            self.model_metrics = ModelMetrics(
                r2_score=r2,
                mse=mse,
                mae=mae,
                training_samples=len(X_train),
                validation_samples=len(X_val),
                last_updated=datetime.now(),
                model_version=self.model_version
            )
            
            logger.info(f"Model trained successfully. R²: {r2:.3f}, MSE: {mse:.3f}")
            return self.model_metrics
                
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return None
    
    def detect_drift(self, recent_data: List[Tuple[str, float, float]]) -> Optional[DriftDetection]:
        """Detect concept drift in the data.
        
        Args:
            recent_data: Recent data for drift detection
            
        Returns:
            DriftDetection result or None
        """
        if not RIVER_AVAILABLE or not self.drift_detector:
            return None
        
        try:
            drift_detected = False
            affected_features = []
            
            # Extract features from recent data
            for config, _, source_reliability in recent_data:
                feature_vector = self.feature_extractor.extract_features(config, source_reliability)
                features = self._prepare_features_for_prediction(feature_vector)
                
                # Check for drift in each feature
                for i, feature_value in enumerate(features):
                    if self.drift_detector.update(feature_value):
                        drift_detected = True
                        affected_features.append(f"feature_{i}")
            
            if drift_detected:
                return DriftDetection(
                    drift_detected=True,
                    confidence=0.8,
                    drift_type="concept_drift",
                    affected_features=affected_features,
                    timestamp=datetime.now()
                )
            
            return None
                
        except Exception as e:
            logger.error(f"Error detecting drift: {e}")
            return None
    
    def save_model(self, model_path: str) -> bool:
        """Save the trained model to disk.
        
        Args:
            model_path: Path to save the model
            
        Returns:
            True if successful, False otherwise
        """
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_selector': self.feature_selector,
                'model_metrics': self.model_metrics,
                'model_version': self.model_version
            }
            
            with open(model_path, 'wb') as f:
                pickle.dump(model_data, f)
        
            logger.info(f"Model saved to {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def load_model(self, model_path: str) -> bool:
        """Load a trained model from disk.
        
        Args:
            model_path: Path to the model file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data.get('model')
            self.scaler = model_data.get('scaler', StandardScaler())
            self.feature_selector = model_data.get('feature_selector')
            self.model_metrics = model_data.get('model_metrics')
            self.model_version = model_data.get('model_version', 'unknown')
            
            logger.info(f"Model loaded from {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        info = {
            'model_version': self.model_version,
            'model_type': type(self.model).__name__ if self.model else 'None',
            'features_count': DEFAULT_FEATURE_SELECTION_K if self.feature_selector else 'Unknown',
            'drift_detection': RIVER_AVAILABLE and self.drift_detector is not None
        }
        
        if self.model_metrics:
            info.update({
                'r2_score': self.model_metrics.r2_score,
                'mse': self.model_metrics.mse,
                'mae': self.model_metrics.mae,
                'training_samples': self.model_metrics.training_samples,
                'last_updated': self.model_metrics.last_updated.isoformat()
            })
        
        return info
