import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
from typing import List, Dict, Tuple, Optional
import json
import os
from datetime import datetime, timedelta
import hashlib


class EnhancedConfigQualityPredictor:
    """Advanced ML-based config quality prediction with validation and tuning."""

    def __init__(self, model_path: str | None = None, model_type: str = "random_forest"):
        self.model_type = model_type
        self.model: Optional[RandomForestRegressor | GradientBoostingRegressor] = None
        self.scaler = StandardScaler()
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.feature_names = [
            "protocol_vmess", "protocol_vless", "protocol_trojan", "protocol_ss",
            "protocol_wireguard", "protocol_openvpn", "protocol_hysteria",
            "has_tls", "has_ws", "has_grpc", "has_quic", "has_reality",
            "port_443", "port_80", "port_8080", "port_8443", "port_22", "port_53",
            "alpn_h2", "alpn_http11", "alpn_h3", "alpn_quic",
            "has_sni", "has_uuid", "has_password", "has_psk",
            "hour_of_day", "day_of_week", "month", "is_weekend",
            "domain_length", "is_cdn", "is_cloudflare", "is_aws", "is_azure",
            "geo_distance", "latency_ms", "bandwidth_mbps",
            "config_age_hours", "source_reliability", "protocol_popularity"
        ]
        
        self.model_params = {
            "random_forest": {
                "n_estimators": [50, 100, 200],
                "max_depth": [5, 10, 15, None],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4]
            },
            "gradient_boosting": {
                "n_estimators": [50, 100, 200],
                "max_depth": [3, 5, 7],
                "learning_rate": [0.01, 0.1, 0.2],
                "subsample": [0.8, 0.9, 1.0]
            }
        }

        if model_path:
            self.load_model(model_path)
        else:
            self._initialize_model()

    def _initialize_model(self):
        """Initialize the ML model based on type."""
        if self.model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100, max_depth=10, min_samples_split=5, 
                random_state=42, n_jobs=-1
            )
        elif self.model_type == "gradient_boosting":
            self.model = GradientBoostingRegressor(
                n_estimators=100, max_depth=5, learning_rate=0.1,
                random_state=42
            )
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

    def extract_features(self, config: Dict) -> np.ndarray:
        """Extract comprehensive features from config."""
        features: List[float] = []

        # Protocol features (one-hot encoded)
        protocol = str(config.get("protocol", "")).lower()
        protocols = ["vmess", "vless", "trojan", "ss", "wireguard", "openvpn", "hysteria"]
        for p in protocols:
            features.append(1.0 if protocol == p else 0.0)

        # Security and transport features
        features.append(1.0 if config.get("tls") else 0.0)
        features.append(1.0 if config.get("ws") else 0.0)
        features.append(1.0 if config.get("grpc") else 0.0)
        features.append(1.0 if config.get("quic") else 0.0)
        features.append(1.0 if config.get("reality") else 0.0)

        # Port features (common ports)
        port = int(config.get("port", 0) or 0)
        common_ports = [443, 80, 8080, 8443, 22, 53]
        for p in common_ports:
            features.append(1.0 if port == p else 0.0)

        # ALPN features
        alpn = config.get("alpn", []) or []
        try:
            alpn_lower = [str(a).lower() for a in alpn]
        except Exception:
            alpn_lower = []
        alpn_features = ["h2", "http/1.1", "h3", "quic"]
        for a in alpn_features:
            features.append(1.0 if a in alpn_lower else 0.0)

        # Authentication and security features
        features.append(1.0 if config.get("sni") else 0.0)
        features.append(1.0 if config.get("uuid") else 0.0)
        features.append(1.0 if config.get("password") else 0.0)
        features.append(1.0 if config.get("psk") else 0.0)

        # Temporal features
        now = datetime.now()
        features.append(float(now.hour))
        features.append(float(now.weekday()))
        features.append(float(now.month))
        features.append(1.0 if now.weekday() >= 5 else 0.0)  # weekend

        # Domain features
        domain = str(config.get("host", ""))
        dlower = domain.lower()
        features.append(float(len(domain)))
        features.append(1.0 if "cdn" in dlower else 0.0)
        features.append(1.0 if "cloudflare" in dlower else 0.0)
        features.append(1.0 if "aws" in dlower else 0.0)
        features.append(1.0 if "azure" in dlower else 0.0)

        # Network features
        features.append(float(config.get("geo_distance", 0)))
        features.append(float(config.get("latency_ms", 0)))
        features.append(float(config.get("bandwidth_mbps", 0)))

        # Metadata features
        config_age = config.get("config_age_hours", 0)
        features.append(float(config_age))
        features.append(float(config.get("source_reliability", 0.5)))
        features.append(float(config.get("protocol_popularity", 0.5)))

        return np.array(features).reshape(1, -1)

    def train(self, configs: List[Dict], scores: List[float], 
              validation_split: float = 0.2, tune_hyperparameters: bool = True):
        """Train the model with validation and optional hyperparameter tuning."""
        if len(configs) != len(scores):
            raise ValueError("Configs and scores must have the same length")
        
        if len(configs) < 100:
            print("Warning: Training with less than 100 samples may lead to poor performance")
        
        # Split data
        X = np.vstack([self.extract_features(c) for c in configs])
        y = np.array(scores)
        
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        if tune_hyperparameters and len(configs) >= 200:
            print("Tuning hyperparameters...")
            self._tune_hyperparameters(X_train_scaled, y_train)
        else:
            print("Training with default parameters...")
            assert self.model is not None
            self.model.fit(X_train_scaled, y_train)

        # Evaluate on validation set
        val_predictions = self.predict_batch([configs[i] for i in range(len(configs)) if i in range(len(X_val))])
        val_scores = [scores[i] for i in range(len(scores)) if i in range(len(y_val))]
        
        mse = mean_squared_error(val_scores, val_predictions)
        r2 = r2_score(val_scores, val_predictions)
        mae = mean_absolute_error(val_scores, val_predictions)
        
        print(f"Validation Results:")
        print(f"  MSE: {mse:.4f}")
        print(f"  R²: {r2:.4f}")
        print(f"  MAE: {mae:.4f}")
        
        # Feature importance
        self._print_feature_importance()

    def _tune_hyperparameters(self, X_train: np.ndarray, y_train: np.ndarray):
        """Tune hyperparameters using grid search with cross-validation."""
        params = self.model_params[self.model_type]
        
        if self.model_type == "random_forest":
            base_model = RandomForestRegressor(random_state=42, n_jobs=-1)
        else:
            base_model = GradientBoostingRegressor(random_state=42)
        
        grid_search = GridSearchCV(
            base_model, params, cv=3, scoring='neg_mean_squared_error',
            n_jobs=-1, verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        self.model = grid_search.best_estimator_
        
        print(f"Best parameters: {grid_search.best_params_}")
        print(f"Best CV score: {-grid_search.best_score_:.4f}")

    def _print_feature_importance(self):
        """Print feature importance analysis."""
        if self.model is None:
            return
        
        if hasattr(self.model, 'feature_importances_'):
            importance = self.model.feature_importances_
            feature_importance = dict(zip(self.feature_names, importance))
            
            print("\nFeature Importance (Top 15):")
            for feature, imp in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:15]:
                print(f"  {feature}: {imp:.4f}")

    def predict(self, config: Dict) -> float:
        """Predict config quality."""
        if self.model is None:
            raise RuntimeError("Model is not trained")
        
        features = self.extract_features(config)
        features_scaled = self.scaler.transform(features)
        prediction = float(self.model.predict(features_scaled)[0])
        
        # Ensure prediction is in reasonable range
        return max(0.0, min(100.0, prediction))

    def predict_batch(self, configs: List[Dict]) -> List[float]:
        """Predict quality for multiple configs efficiently."""
        if self.model is None:
            raise RuntimeError("Model is not trained")
        
        if not configs:
            return []
        
        X = np.vstack([self.extract_features(c) for c in configs])
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        return [max(0.0, min(100.0, float(p))) for p in predictions]

    def cross_validate(self, configs: List[Dict], scores: List[float], cv: int = 5) -> Dict[str, float]:
        """Perform cross-validation to assess model performance."""
        if self.model is None:
            raise RuntimeError("Model is not trained")
        
        X = np.vstack([self.extract_features(c) for c in configs])
        y = np.array(scores)
        X_scaled = self.scaler.transform(X)
        
        # Perform cross-validation
        cv_scores = cross_val_score(self.model, X_scaled, y, cv=cv, scoring='r2')
        cv_mse = -cross_val_score(self.model, X_scaled, y, cv=cv, scoring='neg_mean_squared_error')
        
        results = {
            'cv_r2_mean': float(cv_scores.mean()),
            'cv_r2_std': float(cv_scores.std()),
            'cv_mse_mean': float(cv_mse.mean()),
            'cv_mse_std': float(cv_mse.std())
        }
        
        print(f"Cross-Validation Results ({cv}-fold):")
        print(f"  R²: {results['cv_r2_mean']:.4f}")
        print(f"  MSE: {results['cv_mse_mean']:.4f} ± {results['cv_mse_std']:.4f}")
        
        return results

    def save_model(self, path: str):
        """Save trained model with metadata."""
        if self.model is None:
            raise RuntimeError("No model to save")
        
        metadata = {
            "model_type": self.model_type,
            "feature_names": self.feature_names,
            "training_date": datetime.now().isoformat(),
            "model_hash": hashlib.md5(str(self.model.get_params()).encode()).hexdigest()[:8]
        }
        
        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "label_encoders": self.label_encoders,
            "metadata": metadata
        }
        
        joblib.dump(model_data, path)
        print(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load trained model with metadata."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")
        
        data = joblib.load(path)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self.label_encoders = data.get("label_encoders", {})
        
        if "metadata" in data:
            metadata = data["metadata"]
            print(f"Loaded model: {metadata['model_type']} (trained: {metadata['training_date']})")
            print(f"Model hash: {metadata['model_hash']}")

    def get_model_info(self) -> Dict:
        """Get information about the current model."""
        if self.model is None:
            return {"status": "not_trained"}
        
        # Check if model has been trained by looking for training-specific attributes
        is_trained = hasattr(self.model, 'feature_importances_') or hasattr(self.model, 'coef_')
        
        info = {
            "model_type": self.model_type,
            "status": "trained" if is_trained else "initialized",
            "feature_count": len(self.feature_names),
            "model_params": self.model.get_params()
        }
        
        if hasattr(self.model, 'n_estimators'):
            info["n_estimators"] = self.model.n_estimators
        if hasattr(self.model, 'max_depth'):
            info["max_depth"] = self.model.max_depth
        
        return info


class EnhancedQualityPredictor:
    """Enhanced compatibility wrapper with advanced ML capabilities."""

    def __init__(self, model_path: str | None = None, model_type: str = "random_forest"):
        self._ml: EnhancedConfigQualityPredictor | None = None
        try:
            if model_path:
                self._ml = EnhancedConfigQualityPredictor(model_path=model_path, model_type=model_type)
            else:
                self._ml = EnhancedConfigQualityPredictor(model_type=model_type)
        except Exception as e:
            print(f"Failed to initialize ML model: {e}")
            self._ml = None

    def predict_quality(self, protocol: str, port: int | None, context: Dict) -> float:
        # Try ML prediction if a model was loaded
        if self._ml is not None:
            cfg = {
                "protocol": protocol,
                "port": port or 0,
                "tls": context.get("tls", False),
                "ws": context.get("ws", False),
                "grpc": context.get("grpc", False),
                "quic": context.get("quic", False),
                "reality": context.get("reality", False),
                "alpn": context.get("alpn", []),
                "sni": context.get("sni"),
                "uuid": context.get("uuid"),
                "password": context.get("password"),
                "psk": context.get("psk"),
                "host": context.get("host", ""),
                "geo_distance": context.get("geo_distance", 0),
                "latency_ms": context.get("latency_ms", 0),
                "bandwidth_mbps": context.get("bandwidth_mbps", 0),
                "config_age_hours": context.get("config_age_hours", 0),
                "source_reliability": context.get("source_reliability", 0.5),
                "protocol_popularity": context.get("protocol_popularity", 0.5),
            }
            try:
                pred = float(self._ml.predict(cfg))
                return max(0.0, min(100.0, pred))
            except Exception:
                pass

        # Enhanced heuristic baseline as fallback
        score = 50.0
        p = (protocol or "").lower()
        
        # Protocol scoring
        if p in {"reality", "vless"}:
            score += 15
        elif p in {"vmess", "trojan"}:
            score += 10
        elif p in {"wireguard", "openvpn"}:
            score += 8
        elif p in {"hysteria", "hysteria2", "tuic"}:
            score += 12
        elif p in {"shadowsocks", "ss"}:
            score += 6
        elif p in {"shadowsocksr", "ssr"}:
            score += 4
        
        # Port penalties
        if port in {80, 443, 8080, 8443}:
            score -= 5
        elif port in {22, 53, 21, 23}:
            score -= 10
        elif port in {25, 110, 143, 993, 995}:  # Email ports
            score -= 15
        
        # Source reputation
        score += float(context.get("source_reputation", 0)) * 20
        
        # Additional context factors
        if context.get("tls"):
            score += 5
        if context.get("ws") or context.get("grpc"):
            score += 3
        if context.get("reality"):
            score += 8
        if context.get("quic"):
            score += 4
        
        # Domain quality factors
        host = context.get("host", "").lower()
        if "cdn" in host:
            score += 2
        if "cloudflare" in host:
            score += 3
        if "aws" in host or "azure" in host:
            score += 1
        
        return max(0.0, min(100.0, score))

    def train_model(self, configs: List[Dict], scores: List[float], **kwargs):
        """Train the underlying ML model."""
        if self._ml is None:
            raise RuntimeError("ML model not initialized")
        return self._ml.train(configs, scores, **kwargs)

    def get_model_info(self) -> Dict:
        """Get information about the underlying ML model."""
        if self._ml is None:
            return {"status": "not_initialized"}
        return self._ml.get_model_info()
