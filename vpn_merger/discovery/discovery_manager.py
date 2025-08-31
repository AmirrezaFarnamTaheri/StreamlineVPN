"""
Real-time Discovery Manager
==========================

Main orchestrator for real-time VPN configuration source discovery.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .models import DiscoveredSource, DiscoveryMetrics, DEFAULT_DISCOVERY_INTERVAL
from .github_monitor import GitHubRealtimeMonitor
from .telegram_monitor import TelegramChannelMonitor
from .web_crawler import IntelligentWebCrawler

logger = logging.getLogger(__name__)


class RealTimeDiscovery:
    """Main orchestrator for real-time VPN configuration source discovery."""
    
    def __init__(self, 
                 github_token: Optional[str] = None,
                 telegram_api_id: Optional[str] = None,
                 telegram_api_hash: Optional[str] = None,
                 discovery_interval: int = DEFAULT_DISCOVERY_INTERVAL):
        """Initialize real-time discovery manager.
        
        Args:
            github_token: GitHub API token
            telegram_api_id: Telegram API ID
            telegram_api_hash: Telegram API hash
            discovery_interval: Discovery interval in seconds
        """
        self.github_monitor = GitHubRealtimeMonitor(github_token)
        self.telegram_monitor = TelegramChannelMonitor(telegram_api_id, telegram_api_hash)
        self.web_crawler = IntelligentWebCrawler()
        
        self.discovery_interval = discovery_interval
        self.is_running = False
        self.discovery_task = None
        
        # Discovery state
        self.all_discovered_sources: List[DiscoveredSource] = []
        self.last_discovery_run = None
        self.discovery_metrics = DiscoveryMetrics(
            total_sources_discovered=0,
            github_sources=0,
            telegram_sources=0,
            web_sources=0,
            paste_sources=0,
            average_reliability=0.0,
            last_discovery_run=datetime.now(),
            discovery_success_rate=0.0
        )
    
    async def start_discovery(self) -> None:
        """Start continuous discovery process."""
        if self.is_running:
            logger.warning("Discovery already running")
            return
        
        self.is_running = True
        logger.info("Starting real-time discovery process")
        
        try:
            while self.is_running:
                await self._run_discovery_cycle()
                await asyncio.sleep(self.discovery_interval)
                
        except asyncio.CancelledError:
            logger.info("Discovery process cancelled")
        except Exception as e:
            logger.error(f"Discovery process error: {e}")
        finally:
            self.is_running = False
    
    async def stop_discovery(self) -> None:
        """Stop continuous discovery process."""
        self.is_running = False
        if self.discovery_task:
            self.discovery_task.cancel()
            try:
                await self.discovery_task
            except asyncio.CancelledError:
                pass
        logger.info("Discovery process stopped")
    
    async def _run_discovery_cycle(self) -> None:
        """Run a single discovery cycle."""
        start_time = datetime.now()
        discovered_sources = []
        
        try:
            # Run all discovery methods concurrently
            tasks = [
                self._discover_github_sources(),
                self._discover_telegram_sources(),
                self._discover_web_sources()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for result in results:
                if isinstance(result, list):
                    discovered_sources.extend(result)
                else:
                    logger.error(f"Discovery task failed: {result}")
            
            # Update discovery state
            self.all_discovered_sources.extend(discovered_sources)
            self.last_discovery_run = start_time
            
            # Update metrics
            self._update_discovery_metrics(discovered_sources, start_time)
            
            logger.info(f"Discovery cycle completed: {len(discovered_sources)} new sources found")
            
        except Exception as e:
            logger.error(f"Discovery cycle failed: {e}")
    
    async def _discover_github_sources(self) -> List[DiscoveredSource]:
        """Discover sources from GitHub."""
        try:
            return await self.github_monitor.monitor_topics()
        except Exception as e:
            logger.error(f"GitHub discovery failed: {e}")
            return []
    
    async def _discover_telegram_sources(self) -> List[DiscoveredSource]:
        """Discover sources from Telegram."""
        try:
            return await self.telegram_monitor.monitor_channels()
        except Exception as e:
            logger.error(f"Telegram discovery failed: {e}")
            return []
    
    async def _discover_web_sources(self) -> List[DiscoveredSource]:
        """Discover sources from web crawling."""
        try:
            # Define target websites for crawling
            target_sites = [
                'https://github.com/topics/vpn-config',
                'https://github.com/topics/v2ray',
                'https://github.com/topics/clash',
                'https://pastebin.com/trending'
            ]
            
            async with self.web_crawler:
                return await self.web_crawler.search_multiple_sites(target_sites)
                
        except Exception as e:
            logger.error(f"Web discovery failed: {e}")
            return []
    
    def _update_discovery_metrics(self, new_sources: List[DiscoveredSource], 
                                discovery_time: datetime) -> None:
        """Update discovery metrics.
        
        Args:
            new_sources: Newly discovered sources
            discovery_time: Time of discovery
        """
        # Count sources by type
        github_count = len([s for s in new_sources if s.source_type == 'github'])
        telegram_count = len([s for s in new_sources if s.source_type == 'telegram'])
        web_count = len([s for s in new_sources if s.source_type == 'web'])
        paste_count = len([s for s in new_sources if s.source_type == 'paste'])
        
        # Calculate average reliability
        total_reliability = sum(s.reliability_score for s in new_sources)
        avg_reliability = total_reliability / len(new_sources) if new_sources else 0.0
        
        # Update metrics
        self.discovery_metrics = DiscoveryMetrics(
            total_sources_discovered=len(self.all_discovered_sources),
            github_sources=github_count,
            telegram_sources=telegram_count,
            web_sources=web_count,
            paste_sources=paste_count,
            average_reliability=avg_reliability,
            last_discovery_run=discovery_time,
            discovery_success_rate=1.0 if new_sources else 0.0
        )
    
    async def run_single_discovery(self) -> List[DiscoveredSource]:
        """Run a single discovery cycle and return results.
        
        Returns:
            List of discovered sources
        """
        discovered_sources = []
        
        try:
            # Run all discovery methods
            github_sources = await self._discover_github_sources()
            telegram_sources = await self._discover_telegram_sources()
            web_sources = await self._discover_web_sources()
            
            discovered_sources = github_sources + telegram_sources + web_sources
            
            # Update state
            self.all_discovered_sources.extend(discovered_sources)
            self.last_discovery_run = datetime.now()
            self._update_discovery_metrics(discovered_sources, self.last_discovery_run)
            
            logger.info(f"Single discovery completed: {len(discovered_sources)} sources found")
            
        except Exception as e:
            logger.error(f"Single discovery failed: {e}")
        
        return discovered_sources
    
    def get_discovered_sources(self, 
                             source_type: Optional[str] = None,
                             min_reliability: float = 0.0,
                             limit: Optional[int] = None) -> List[DiscoveredSource]:
        """Get discovered sources with optional filtering.
        
        Args:
            source_type: Filter by source type
            min_reliability: Minimum reliability score
            limit: Maximum number of sources to return
            
        Returns:
            Filtered list of discovered sources
        """
        sources = self.all_discovered_sources
        
        # Filter by source type
        if source_type:
            sources = [s for s in sources if s.source_type == source_type]
        
        # Filter by reliability
        sources = [s for s in sources if s.reliability_score >= min_reliability]
        
        # Sort by reliability (descending)
        sources.sort(key=lambda s: s.reliability_score, reverse=True)
        
        # Apply limit
        if limit:
            sources = sources[:limit]
        
        return sources
    
    def get_discovery_metrics(self) -> DiscoveryMetrics:
        """Get current discovery metrics.
        
        Returns:
            Current discovery metrics
        """
        return self.discovery_metrics
    
    def get_discovery_stats(self) -> Dict[str, Any]:
        """Get comprehensive discovery statistics.
        
        Returns:
            Dictionary containing discovery statistics
        """
        github_stats = self.github_monitor.get_discovery_stats()
        telegram_stats = self.telegram_monitor.get_discovery_stats()
        web_stats = self.web_crawler.get_discovery_stats()
        
        return {
            'overall': {
                'total_sources': len(self.all_discovered_sources),
                'active_sources': len([s for s in self.all_discovered_sources if s.is_active]),
                'average_reliability': sum(s.reliability_score for s in self.all_discovered_sources) / 
                                     max(len(self.all_discovered_sources), 1),
                'last_discovery_run': self.last_discovery_run,
                'is_running': self.is_running
            },
            'github': github_stats,
            'telegram': telegram_stats,
            'web': web_stats,
            'metrics': self.discovery_metrics
        }
    
    async def validate_sources(self, sources: List[DiscoveredSource]) -> List[DiscoveredSource]:
        """Validate discovered sources.
        
        Args:
            sources: List of sources to validate
            
        Returns:
            List of valid sources
        """
        valid_sources = []
        
        for source in sources:
            try:
                # Basic validation
                if not source.url or not source.title:
                    continue
                
                # Check if source is still accessible
                # This would typically involve making a request to the URL
                # For now, we'll just check basic criteria
                if source.reliability_score >= 0.3:
                    valid_sources.append(source)
                    
            except Exception as e:
                logger.debug(f"Error validating source {source.url}: {e}")
                continue
        
        return valid_sources
