"""
Quality Scoring Weights and Constants
=====================================

Constants and weights used for quality scoring in source validation.
"""

# Quality scoring weights
QUALITY_WEIGHTS = {
    "historical_reliability": 0.25,
    "ssl_certificate": 0.15,
    "response_time": 0.15,
    "content_quality": 0.20,
    "protocol_diversity": 0.15,
    "uptime_consistency": 0.10,
}

# Validation constants
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_REDIRECTS = 5
DEFAULT_USER_AGENT = "VPN-Merger/2.0.0"
MIN_QUALITY_SCORE = 0.0
MAX_QUALITY_SCORE = 1.0

# Protocol patterns for detection
VPN_PROTOCOL_PATTERNS = {
    "vmess": "vmess://",
    "vless": "vless://",
    "trojan": "trojan://",
    "shadowsocks": "ss://",
    "shadowsocksr": "ssr://",
    "http": "http://",
    "https": "https://",
    "socks": "socks://",
    "socks5": "socks5://",
    "hysteria": "hysteria://",
    "hysteria2": "hysteria2://",
    "tuic": "tuic://",
    "wireguard": "wg://",
}

# Content quality indicators
CONTENT_QUALITY_INDICATORS = {
    "base64_encoded": 0.1,
    "json_format": 0.2,
    "yaml_format": 0.15,
    "multiple_protocols": 0.3,
    "server_metadata": 0.15,
    "configuration_completeness": 0.1,
}

# Response time scoring thresholds (in seconds)
RESPONSE_TIME_THRESHOLDS = {
    "excellent": 1.0,
    "good": 3.0,
    "acceptable": 5.0,
    "poor": 10.0,
}

# SSL certificate scoring weights
SSL_SCORING_WEIGHTS = {
    "valid_certificate": 0.4,
    "long_expiry": 0.2,
    "strong_encryption": 0.2,
    "trusted_ca": 0.2,
}
