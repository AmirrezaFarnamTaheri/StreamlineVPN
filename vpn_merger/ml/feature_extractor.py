"""
Feature Extractor for ML Quality Prediction
==========================================

Extracts and processes features from VPN configurations for ML prediction.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from .models import FeatureVector, PROTOCOL_PATTERNS, COMMON_PORTS, SPECIAL_CHARS

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extracts features from VPN configurations for ML prediction."""
    
    def __init__(self):
        """Initialize the feature extractor."""
        self._protocol_scores = {
            'vless': 0.9,
            'vmess': 0.8,
            'trojan': 0.85,
            'shadowsocks': 0.7,
            'hysteria': 0.75,
            'tuic': 0.8
        }
        
        self._encryption_scores = {
            'none': 0.3,
            'tls': 0.9,
            'reality': 0.95,
            'xtls': 0.9,
            'ws': 0.7,
            'h2': 0.8,
            'grpc': 0.85
        }
        
        self._network_scores = {
            'tcp': 0.6,
            'ws': 0.8,
            'h2': 0.85,
            'grpc': 0.9,
            'quic': 0.75
        }
    
    def extract_features(self, config: str, source_reliability: float = 0.5) -> FeatureVector:
        """Extract features from a VPN configuration.
        
        Args:
            config: VPN configuration string
            source_reliability: Reliability score of the source
            
        Returns:
            FeatureVector with extracted features
        """
        try:
            config_length = len(config)
            protocol_score = self._extract_protocol_score(config)
            port_score = self._extract_port_score(config)
            complexity_score = self._extract_complexity_score(config)
            encryption_score = self._extract_encryption_score(config)
            network_score = self._extract_network_score(config)
            security_score = self._extract_security_score(config)
            
            return FeatureVector(
                config_length=config_length,
                protocol_score=protocol_score,
                port_score=port_score,
                complexity_score=complexity_score,
                encryption_score=encryption_score,
                network_score=network_score,
                security_score=security_score,
                source_reliability=source_reliability,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return self._create_default_feature_vector(source_reliability)
    
    def _extract_protocol_score(self, config: str) -> float:
        """Extract protocol-based quality score."""
        config_lower = config.lower()
        
        for protocol, pattern in PROTOCOL_PATTERNS.items():
            if pattern in config_lower:
                return self._protocol_scores.get(protocol, 0.5)
        
        return 0.5  # Default score for unknown protocols
    
    def _extract_port_score(self, config: str) -> float:
        """Extract port-based quality score."""
        try:
            # Extract port from various formats
            port_patterns = [
                r':(\d{1,5})',  # Standard port format
                r'port["\']?\s*:\s*(\d{1,5})',  # JSON format
                r'port=(\d{1,5})'  # Query parameter format
            ]
            
            for pattern in port_patterns:
                match = re.search(pattern, config)
                if match:
                    port = match.group(1)
                    if port in COMMON_PORTS:
                        return 0.8  # Common ports are generally more reliable
                    elif 1024 <= int(port) <= 65535:
                        return 0.7  # Valid port range
                    else:
                        return 0.3  # Unusual ports
            
            return 0.5  # Default score if no port found
        except Exception:
            return 0.5
    
    def _extract_complexity_score(self, config: str) -> float:
        """Extract complexity-based quality score."""
        try:
            # Count special characters
            special_char_count = sum(1 for char in config if char in SPECIAL_CHARS)
            
            # Count different character types
            has_letters = bool(re.search(r'[a-zA-Z]', config))
            has_numbers = bool(re.search(r'\d', config))
            has_special = special_char_count > 0
            
            # Calculate complexity score
            complexity = 0.0
            if has_letters:
                complexity += 0.3
            if has_numbers:
                complexity += 0.3
            if has_special:
                complexity += 0.4
            
            # Normalize by length to avoid bias towards very long configs
            normalized_complexity = complexity * (100 / max(len(config), 100))
            
            return min(normalized_complexity, 1.0)
        except Exception:
            return 0.5
    
    def _extract_encryption_score(self, config: str) -> float:
        """Extract encryption-based quality score."""
        config_lower = config.lower()
        
        for encryption, score in self._encryption_scores.items():
            if encryption in config_lower:
                return score
        
        return 0.5  # Default score for unknown encryption
    
    def _extract_network_score(self, config: str) -> float:
        """Extract network transport-based quality score."""
        config_lower = config.lower()
        
        for network, score in self._network_scores.items():
            if network in config_lower:
                return score
        
        return 0.6  # Default to TCP score
    
    def _extract_security_score(self, config: str) -> float:
        """Extract overall security score."""
        try:
            security_indicators = {
                'tls': 0.3,
                'ssl': 0.3,
                'reality': 0.4,
                'xtls': 0.3,
                'ws': 0.2,
                'h2': 0.2,
                'grpc': 0.2
            }
            
            config_lower = config.lower()
            total_score = 0.0
            
            for indicator, score in security_indicators.items():
                if indicator in config_lower:
                    total_score += score
            
            return min(total_score, 1.0)
        except Exception:
            return 0.5
    
    def _create_default_feature_vector(self, source_reliability: float) -> FeatureVector:
        """Create a default feature vector when extraction fails."""
        return FeatureVector(
            config_length=0,
            protocol_score=0.5,
            port_score=0.5,
            complexity_score=0.5,
            encryption_score=0.5,
            network_score=0.5,
            security_score=0.5,
            source_reliability=source_reliability,
            timestamp=datetime.now()
        )
    
    def extract_batch_features(self, configs: List[str], source_reliability: float = 0.5) -> List[FeatureVector]:
        """Extract features from multiple configurations.
        
        Args:
            configs: List of VPN configuration strings
            source_reliability: Reliability score of the source
            
        Returns:
            List of FeatureVector objects
        """
        features = []
        for config in configs:
            feature_vector = self.extract_features(config, source_reliability)
            features.append(feature_vector)
        return features
