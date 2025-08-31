"""
Real-time Source Discovery Module
================================

Advanced real-time discovery system for finding new VPN configuration sources
through GitHub monitoring, Telegram channels, and intelligent web crawling.
"""

from .models import DiscoveredSource, DiscoveryMetrics
from .github_monitor import GitHubRealtimeMonitor
from .telegram_monitor import TelegramChannelMonitor
from .web_crawler import IntelligentWebCrawler
from .discovery_manager import RealTimeDiscovery

__all__ = [
    "DiscoveredSource",
    "DiscoveryMetrics", 
    "GitHubRealtimeMonitor",
    "TelegramChannelMonitor",
    "IntelligentWebCrawler",
    "RealTimeDiscovery"
]
