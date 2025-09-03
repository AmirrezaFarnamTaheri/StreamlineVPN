"""
Discovery Models and Constants
============================

Data models and constants for the real-time discovery system.
"""

import re
from dataclasses import dataclass
from datetime import datetime

# Discovery constants
DEFAULT_DISCOVERY_INTERVAL = 3600  # 1 hour
DEFAULT_MAX_SOURCES_PER_RUN = 100
DEFAULT_REQUEST_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_MIN_RELIABILITY_SCORE = 0.3

# GitHub search topics
GITHUB_TOPICS = [
    "vpn-config",
    "v2ray",
    "clash",
    "sing-box",
    "proxy",
    "vpn-subscription",
    "free-vpn",
    "vpn-nodes",
    "shadowsocks",
]

# Telegram channels to monitor
TELEGRAM_CHANNELS = [
    "@vpn_configs",
    "@free_proxies",
    "@v2ray_share",
    "@clash_configs",
    "@singbox_configs",
]

# Web crawling patterns
WEB_CRAWLING_PATTERNS = [
    r"vmess://[A-Za-z0-9+/=]+",
    r"vless://[A-Za-z0-9+/=]+",
    r"trojan://[A-Za-z0-9+/=]+",
    r"ss://[A-Za-z0-9+/=]+",
    r"hysteria://[A-Za-z0-9+/=]+",
    r"tuic://[A-Za-z0-9+/=]+",
]

# Protocol keywords for detection
PROTOCOL_KEYWORDS = {
    "vmess": ["vmess", "v2ray"],
    "vless": ["vless"],
    "trojan": ["trojan"],
    "shadowsocks": ["shadowsocks", "ss"],
    "hysteria": ["hysteria"],
    "tuic": ["tuic"],
}


@dataclass
class DiscoveredSource:
    """Discovered source information."""

    url: str
    source_type: str  # 'github', 'telegram', 'web', 'paste'
    title: str
    description: str
    discovered_at: datetime
    reliability_score: float
    config_count: int
    protocols: list[str]
    region: str
    last_updated: datetime | None = None
    is_active: bool = True


@dataclass
class DiscoveryMetrics:
    """Discovery performance metrics."""

    total_sources_discovered: int
    github_sources: int
    telegram_sources: int
    web_sources: int
    paste_sources: int
    average_reliability: float
    last_discovery_run: datetime
    discovery_success_rate: float


def detect_protocols_from_text(text: str) -> list[str]:
    """Detect VPN protocols mentioned in text.

    Args:
        text: Text to analyze

    Returns:
        List of detected protocols
    """
    protocols = []
    text_lower = text.lower()

    for protocol, keywords in PROTOCOL_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            protocols.append(protocol)

    return protocols


def extract_configs_from_text(text: str) -> list[str]:
    """Extract VPN configuration URLs from text.

    Args:
        text: Text to search for configurations

    Returns:
        List of found configuration URLs
    """
    configs = []
    for pattern in WEB_CRAWLING_PATTERNS:
        matches = re.findall(pattern, text)
        configs.extend(matches)

    return list(set(configs))  # Remove duplicates
