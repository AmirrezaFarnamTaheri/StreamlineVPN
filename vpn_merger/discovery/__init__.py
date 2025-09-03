"""
Real-time Source Discovery Module
================================

Advanced real-time discovery system for finding new VPN configuration sources
through GitHub monitoring, Telegram channels, and intelligent web crawling.
"""

from .discovery_manager import RealTimeDiscovery
from .github_monitor import GitHubRealtimeMonitor
from .models import DiscoveredSource, DiscoveryMetrics
from .telegram_monitor import TelegramChannelMonitor
from .web_crawler import IntelligentWebCrawler

__all__ = [
    "DiscoveredSource",
    "DiscoveryMetrics",
    "GitHubRealtimeMonitor",
    "IntelligentWebCrawler",
    "RealTimeDiscovery",
    "TelegramChannelMonitor",
]
