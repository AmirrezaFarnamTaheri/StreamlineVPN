"""
Base ML Model
============

Base class for machine learning models used in VPN configuration quality prediction.
"""

import logging
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


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


class BaseMLModel(ABC):
    """Base class for machine learning models."""
    
    def __init__(self, model_name: str = "base_model"):
        """Initialize base model.
        
        Args:
            model_name: Name of the model
        """
        self.model_name = model_name
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.is_trained = False
        self.training_history = []
        self.last_training_time = None
        
    @abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray, **kwargs) -> ModelMetrics:
        """Train the model.
        
        Args:
            X: Training features
            y: Training targets
            **kwargs: Additional training parameters
            
        Returns:
            Model performance metrics
        """
        pass
    
    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions.
        
        Args:
            X: Input features
            
        Returns:
            Predicted values
        """
        pass
    
    @abstractmethod
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> ModelMetrics:
        """Evaluate model performance.
        
        Args:
            X: Test features
            y: Test targets
            
        Returns:
            Model performance metrics
        """
        pass
    
    def save_model(self, filepath: Union[str, Path]) -> None:
        """Save model to file.
        
        Args:
            filepath: Path to save the model
        """
        try:
            import joblib
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'is_trained': self.is_trained,
                'training_history': self.training_history,
                'last_training_time': self.last_training_time,
                'model_name': self.model_name
            }
            joblib.dump(model_data, filepath)
            logger.info(f"Model saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise
    
    def load_model(self, filepath: Union[str, Path]) -> None:
        """Load model from file.
        
        Args:
            filepath: Path to load the model from
        """
        try:
            import joblib
            model_data = joblib.load(filepath)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.is_trained = model_data['is_trained']
            self.training_history = model_data['training_history']
            self.last_training_time = model_data['last_training_time']
            self.model_name = model_data['model_name']
            
            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not self.is_trained or self.model is None:
            return {}
        
        try:
            if hasattr(self.model, 'feature_importances_'):
                importance_scores = self.model.feature_importances_
            elif hasattr(self.model, 'coef_'):
                importance_scores = np.abs(self.model.coef_)
            else:
                return {}
            
            return dict(zip(self.feature_names, importance_scores))
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return {}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'is_trained': self.is_trained,
            'feature_count': len(self.feature_names),
            'last_training_time': self.last_training_time,
            'training_history_length': len(self.training_history)
        }
    
    def validate_input(self, X: np.ndarray) -> bool:
        """Validate input data.
        
        Args:
            X: Input features
            
        Returns:
            True if input is valid, False otherwise
        """
        if X is None or len(X) == 0:
            return False
        
        if not isinstance(X, np.ndarray):
            return False
        
        if len(X.shape) != 2:
            return False
        
        if X.shape[1] != len(self.feature_names):
            return False
        
        return True
