"""
Quality Predictor
=================

Machine learning-based quality prediction for VPN configurations.
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models.configuration import VPNConfiguration, ProtocolType
from ..utils.logging import get_logger

logger = get_logger(__name__)


class QualityPredictor:
    """ML-based quality prediction for VPN configurations."""

    def __init__(self):
        """Initialize quality predictor."""
        self.model = self._create_simple_model()
        self.feature_extractors = {
            'protocol': self._extract_protocol_features,
            'server': self._extract_server_features,
            'encryption': self._extract_encryption_features,
            'port': self._extract_port_features,
            'metadata': self._extract_metadata_features
        }
        logger.info("Quality predictor initialized")

    def _create_simple_model(self):
        """Create a simple scoring model."""
        class SimpleModel:
            def predict(self, features: List[float]) -> float:
                # Weighted scoring based on features
                weights = [0.3, 0.2, 0.2, 0.15, 0.15]  # protocol, server, encryption, port, metadata
                
                # Ensure features array has at least 5 elements
                if len(features) < 5:
                    features.extend([0.5] * (5 - len(features)))
                
                # Calculate weighted score
                score = sum(f * w for f, w in zip(features[:5], weights))
                return max(0.0, min(1.0, score))

        return SimpleModel()

    def predict_quality(self, config: VPNConfiguration, metadata: Optional[Dict] = None) -> float:
        """Predict configuration quality score.

        Args:
            config: VPN configuration
            metadata: Additional metadata

        Returns:
            Quality score between 0 and 1
        """
        try:
            features = self._extract_features(config, metadata or {})
            score = self.model.predict(features)
            return score
        except Exception as e:
            logger.debug(f"Quality prediction failed: {e}")
            return 0.5  # Default neutral score

    def _extract_features(self, config: VPNConfiguration, metadata: Dict) -> List[float]:
        """Extract features from configuration.

        Args:
            config: VPN configuration
            metadata: Additional metadata

        Returns:
            List of feature values
        """
        features = []

        # Protocol features
        protocol_features = self._extract_protocol_features(config)
        features.extend(protocol_features)

        # Server features
        server_features = self._extract_server_features(config)
        features.extend(server_features)

        # Encryption features
        encryption_features = self._extract_encryption_features(config)
        features.extend(encryption_features)

        # Port features
        port_features = self._extract_port_features(config)
        features.extend(port_features)

        # Metadata features
        metadata_features = self._extract_metadata_features(metadata)
        features.extend(metadata_features)

        return features

    def _extract_protocol_features(self, config: VPNConfiguration) -> List[float]:
        """Extract protocol-related features.

        Args:
            config: VPN configuration

        Returns:
            List of protocol feature values
        """
        protocol_scores = {
            ProtocolType.VLESS: 0.95,
            ProtocolType.VMESS: 0.85,
            ProtocolType.TROJAN: 0.80,
            ProtocolType.SHADOWSOCKS: 0.75,
            ProtocolType.SHADOWSOCKSR: 0.70,
            ProtocolType.HYSTERIA2: 0.90,
            ProtocolType.HYSTERIA: 0.85,
            ProtocolType.TUIC: 0.88
        }

        score = protocol_scores.get(config.protocol, 0.5)
        return [score]

    def _extract_server_features(self, config: VPNConfiguration) -> List[float]:
        """Extract server-related features.

        Args:
            config: VPN configuration

        Returns:
            List of server feature values
        """
        server = config.server.lower()
        
        # Check for known good patterns
        if any(pattern in server for pattern in ['.cloudflare.', '.amazon.', '.google.']):
            return [0.9]  # Trusted infrastructure
        elif any(pattern in server for pattern in ['.tk', '.ml', '.ga']):
            return [0.3]  # Suspicious domains
        elif re.match(r'^\d+\.\d+\.\d+\.\d+$', server):
            return [0.6]  # IP address
        else:
            return [0.7]  # Regular domain

    def _extract_encryption_features(self, config: VPNConfiguration) -> List[float]:
        """Extract encryption-related features.

        Args:
            config: VPN configuration

        Returns:
            List of encryption feature values
        """
        if not config.encryption:
            return [0.5]  # No encryption info

        encryption = config.encryption.lower()
        
        strong_encryption = ['aes-256-gcm', 'chacha20-poly1305', 'aes-128-gcm', 'aes-256-cfb']
        weak_encryption = ['rc4', 'des', 'aes-128-cfb', 'none']
        
        if any(enc in encryption for enc in strong_encryption):
            return [0.95]
        elif any(enc in encryption for enc in weak_encryption):
            return [0.3]
        else:
            return [0.7]  # Standard encryption

    def _extract_port_features(self, config: VPNConfiguration) -> List[float]:
        """Extract port-related features.

        Args:
            config: VPN configuration

        Returns:
            List of port feature values
        """
        port = config.port
        
        # Standard ports are more reliable
        if port in [443, 8443, 444]:
            return [0.9]
        elif port in [80, 8080, 8888]:
            return [0.7]
        elif port > 10000:
            return [0.5]  # High ports might be less reliable
        else:
            return [0.6]

    def _extract_metadata_features(self, metadata: Dict) -> List[float]:
        """Extract metadata-related features.

        Args:
            metadata: Configuration metadata

        Returns:
            List of metadata feature values
        """
        if not metadata:
            return [0.5]

        score = 0.5

        # Source reliability
        source_tier = metadata.get('source_tier', '').lower()
        if source_tier == 'premium':
            score += 0.3
        elif source_tier == 'reliable':
            score += 0.2
        elif source_tier == 'bulk':
            score += 0.1

        # Historical performance
        success_rate = metadata.get('success_rate', 0)
        if success_rate > 0.8:
            score += 0.2
        elif success_rate > 0.6:
            score += 0.1

        # Age of configuration
        created_at = metadata.get('created_at')
        if created_at:
            try:
                if isinstance(created_at, str):
                    created_time = datetime.fromisoformat(created_at)
                else:
                    created_time = created_at
                
                age_hours = (datetime.now() - created_time).total_seconds() / 3600
                if age_hours < 24:
                    score += 0.1  # Fresh configuration
                elif age_hours > 168:  # 1 week
                    score -= 0.1  # Old configuration
            except Exception:
                pass

        return [min(score, 1.0)]

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance weights.

        Returns:
            Dictionary mapping feature names to importance weights
        """
        return {
            'protocol': 0.3,
            'server': 0.2,
            'encryption': 0.2,
            'port': 0.15,
            'metadata': 0.15
        }

    def explain_prediction(self, config: VPNConfiguration, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Explain quality prediction with feature breakdown.

        Args:
            config: VPN configuration
            metadata: Additional metadata

        Returns:
            Explanation dictionary
        """
        features = self._extract_features(config, metadata or {})
        importance = self.get_feature_importance()
        
        explanation = {
            'overall_score': self.predict_quality(config, metadata),
            'feature_scores': {},
            'feature_importance': importance
        }

        # Extract individual feature scores
        feature_names = ['protocol', 'server', 'encryption', 'port', 'metadata']
        start_idx = 0
        
        for name in feature_names:
            if start_idx < len(features):
                score = features[start_idx]
                explanation['feature_scores'][name] = {
                    'score': score,
                    'weight': importance[name],
                    'contribution': score * importance[name]
                }
                start_idx += 1

        return explanation

    def batch_predict(self, configs: List[VPNConfiguration], metadata_list: Optional[List[Dict]] = None) -> List[float]:
        """Predict quality for multiple configurations.

        Args:
            configs: List of VPN configurations
            metadata_list: List of metadata dictionaries

        Returns:
            List of quality scores
        """
        if metadata_list is None:
            metadata_list = [{}] * len(configs)
        
        scores = []
        for config, metadata in zip(configs, metadata_list):
            score = self.predict_quality(config, metadata)
            scores.append(score)
        
        return scores

    def get_statistics(self) -> Dict[str, Any]:
        """Get predictor statistics.

        Returns:
            Statistics dictionary
        """
        return {
            'model_type': 'simple_weighted',
            'feature_count': 5,
            'feature_importance': self.get_feature_importance(),
            'supported_protocols': [p.value for p in ProtocolType]
        }
