import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
from typing import List, Dict


class ConfigQualityPredictor:
    """ML-based config quality prediction."""

    def __init__(self, model_path: str | None = None):
        self.model: RandomForestRegressor | None = None
        self.scaler = StandardScaler()
        self.feature_names = [
            "protocol_vmess",
            "protocol_vless",
            "protocol_trojan",
            "protocol_ss",
            "has_tls",
            "has_ws",
            "has_grpc",
            "port_443",
            "port_80",
            "alpn_h2",
            "alpn_http11",
            "has_sni",
            "has_uuid",
            "hour_of_day",
            "day_of_week",
            "domain_length",
            "is_cdn",
            "is_cloudflare",
            "geo_distance",
        ]

        if model_path:
            self.load_model(model_path)
        else:
            self.model = RandomForestRegressor(
                n_estimators=100, max_depth=10, min_samples_split=5, random_state=42
            )

    def extract_features(self, config: Dict) -> np.ndarray:
        """Extract features from config."""
        features: list[int | float] = []

        # Protocol features
        protocol = str(config.get("protocol", "")).lower()
        features.append(1 if protocol == "vmess" else 0)
        features.append(1 if protocol == "vless" else 0)
        features.append(1 if protocol == "trojan" else 0)
        features.append(1 if protocol == "ss" else 0)

        # Security features
        features.append(1 if config.get("tls") else 0)
        features.append(1 if config.get("ws") else 0)
        features.append(1 if config.get("grpc") else 0)

        # Port features
        port = int(config.get("port", 0) or 0)
        features.append(1 if port == 443 else 0)
        features.append(1 if port == 80 else 0)

        # ALPN features
        alpn = config.get("alpn", []) or []
        try:
            alpn_lower = [str(a).lower() for a in alpn]
        except Exception:
            alpn_lower = []
        features.append(1 if "h2" in alpn_lower else 0)
        features.append(1 if "http/1.1" in alpn_lower else 0)

        # Other features
        features.append(1 if config.get("sni") else 0)
        features.append(1 if config.get("uuid") else 0)

        # Temporal features
        from datetime import datetime

        now = datetime.now()
        features.append(now.hour)
        features.append(now.weekday())

        # Domain features
        domain = str(config.get("host", ""))
        dlower = domain.lower()
        features.append(len(domain))
        features.append(1 if "cdn" in dlower else 0)
        features.append(1 if "cloudflare" in dlower else 0)

        # Geo feature (simplified)
        features.append(0)  # Placeholder for geo distance

        return np.array(features).reshape(1, -1)

    def train(self, configs: List[Dict], scores: List[float]):
        """Train the model."""
        X = np.vstack([self.extract_features(c) for c in configs])
        y = np.array(scores)

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train model
        assert self.model is not None
        self.model.fit(X_scaled, y)

        # Feature importance
        importance = self.model.feature_importances_
        feature_importance = dict(zip(self.feature_names, importance))

        print("Feature Importance:")
        for feature, imp in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {feature}: {imp:.3f}")

    def predict(self, config: Dict) -> float:
        """Predict config quality."""
        if self.model is None:
            raise RuntimeError("Model is not initialized")
        features = self.extract_features(config)
        # If scaler is not fitted, StandardScaler will raise; we let caller handle.
        features_scaled = self.scaler.transform(features)
        return float(self.model.predict(features_scaled)[0])

    def save_model(self, path: str):
        """Save trained model."""
        joblib.dump({"model": self.model, "scaler": self.scaler, "features": self.feature_names}, path)

    def load_model(self, path: str):
        """Load trained model."""
        data = joblib.load(path)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self.feature_names = data["features"]


class QualityPredictor:
    """Compatibility wrapper around ConfigQualityPredictor.

    Exposes the previous `predict_quality(protocol, port, context)` API used elsewhere
    while allowing projects to opt into the ML model by providing a trained artifacts
    path when constructing the predictor (or by extending this class).
    """

    def __init__(self, model_path: str | None = None):
        self._ml: ConfigQualityPredictor | None = None
        try:
            if model_path:
                self._ml = ConfigQualityPredictor(model_path=model_path)
        except Exception:
            # Fall back to heuristics
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

        # Heuristic baseline as fallback
        score = 50.0
        p = (protocol or "").lower()
        if p in {"reality", "vless"}:
            score += 15
        elif p in {"vmess", "trojan"}:
            score += 10
        elif p in {"wireguard", "openvpn"}:
            score += 8
        elif p in {"hysteria", "hysteria2", "tuic"}:
            score += 12
        
        # Port penalties
        if port in {80, 443, 8080, 8443}:
            score -= 5
        elif port in {22, 53, 21, 23}:
            score -= 10
        
        # Source reputation
        score += float(context.get("source_reputation", 0)) * 20
        
        # Additional context factors
        if context.get("tls"):
            score += 5
        if context.get("ws") or context.get("grpc"):
            score += 3
        if context.get("reality"):
            score += 8
        
        return max(0.0, min(100.0, score))
