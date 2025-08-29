from __future__ import annotations

import asyncio
import re
import os
import aiohttp
from typing import List, Set, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
from urllib.parse import urlparse, urljoin
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class DiscoveredSource:
    """Represents a discovered source with metadata."""
    url: str
    source_type: str  # 'github', 'telegram', 'website', 'api'
    discovery_method: str  # 'search', 'crawl', 'api', 'manual'
    repository_info: Optional[Dict] = None
    content_preview: Optional[str] = None
    last_updated: Optional[datetime] = None
    stars: int = 0
    forks: int = 0
    language: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    description: Optional[str] = None
    discovery_score: float = 0.0
    verified: bool = False
    discovered_at: datetime = field(default_factory=datetime.now)

class IntelligentSourceDiscovery:
    """Advanced source discovery with ML-based ranking and validation."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.discovered_sources: Dict[str, DiscoveredSource] = {}
        self.blacklist: Set[str] = set()
        self.source_scores: Dict[str, float] = {}
        self.discovery_history: List[Dict] = []
        
        # GitHub API rate limiting
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = None
        
        # Discovery patterns
        self.source_patterns = {
            'subscription': [
                r'https?://[^\s]+\.txt',
                r'https?://[^\s]+\.yaml',
                r'https?://[^\s]+\.yml',
                r'https?://[^\s]+\.json',
                r'https?://[^\s]+/sub',
                r'https?://[^\s]+/subscribe',
                r'https?://[^\s]+/config'
            ],
            'repository': [
                r'github\.com/[^/\s]+/[^/\s]+',
                r'gitlab\.com/[^/\s]+/[^/\s]+',
                r'bitbucket\.org/[^/\s]+/[^/\s]+'
            ]
        }
        
        # Keywords for VPN-related content
        self.vpn_keywords = [
            'v2ray', 'vmess', 'vless', 'trojan', 'shadowsocks', 'ss', 'ssr',
            'hysteria', 'hysteria2', 'tuic', 'reality', 'clash', 'sing-box',
            'vpn', 'proxy', 'subscription', 'config', 'node', 'server'
        ]
    
    async def discover_github_sources(self, max_results: int = 100) -> List[DiscoveredSource]:
        """Discover new sources from GitHub using advanced search."""
        if not self.github_token:
            logger.warning("No GitHub token provided, using limited discovery")
            return await self._discover_github_public(max_results)
        
        search_queries = [
            "v2ray subscription updated:>2024-01-01",
            "clash config stars:>10",
            "vmess vless trojan base64",
            "sing-box subscribe json",
            "hysteria2 config",
            "reality vless config",
            "vpn subscription list",
            "proxy config collection"
        ]
        
        discovered = set()
        all_sources = []
        
        async with aiohttp.ClientSession() as session:
            for query in search_queries:
                if self._is_rate_limited():
                    logger.info("Rate limit reached, waiting...")
                    await self._wait_for_rate_limit()
                
                sources = await self._search_github_api(session, query, max_results // len(search_queries))
                for source in sources:
                    if source.url not in discovered:
                        discovered.add(source.url)
                        all_sources.append(source)
        
        # Score and rank sources
        scored_sources = await self._score_sources(all_sources)
        
        # Return top sources
        return scored_sources[:max_results]
    
    async def _discover_github_public(self, max_results: int) -> List[DiscoveredSource]:
        """Discover sources using public GitHub search (limited)."""
        # This method would use web scraping as fallback
        # Implementation depends on GitHub's current structure
        logger.info("Using public GitHub discovery (limited)")
        return []
    
    async def _search_github_api(self, session: aiohttp.ClientSession, query: str, max_results: int) -> List[DiscoveredSource]:
        """Search GitHub using official API."""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {self.github_token}'
        }
        
        search_url = f"https://api.github.com/search/code?q={query}&per_page={min(max_results, 100)}&sort=updated"
        
        try:
            async with session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Update rate limit info
                    self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                    reset_time = response.headers.get('X-RateLimit-Reset')
                    if reset_time:
                        self.rate_limit_reset = datetime.fromtimestamp(int(reset_time))
                    
                    sources = []
                    for item in data.get('items', []):
                        source = await self._process_github_item(item)
                        if source:
                            sources.append(source)
                    
                    return sources
                else:
                    logger.error(f"GitHub API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"GitHub search error: {e}")
            return []
    
    async def _process_github_item(self, item: Dict) -> Optional[DiscoveredSource]:
        """Process a GitHub search result item."""
        try:
            repo = item.get('repository', {})
            repo_name = repo.get('full_name', '')
            repo_url = repo.get('html_url', '')
            file_path = item.get('path', '')
            
            # Convert to raw URL
            raw_url = f"https://raw.githubusercontent.com/{repo_name}/main/{file_path}"
            
            # Check if this looks like a subscription file
            if not self._is_subscription_file(file_path):
                return None
            
            # Get repository details
            repo_info = await self._get_repository_info(repo_name)
            
            source = DiscoveredSource(
                url=raw_url,
                source_type='github',
                discovery_method='api',
                repository_info=repo_info,
                stars=repo_info.get('stargazers_count', 0) if repo_info else 0,
                forks=repo_info.get('forks_count', 0) if repo_info else 0,
                language=repo_info.get('language') if repo_info else None,
                topics=repo_info.get('topics', []) if repo_info else [],
                description=repo_info.get('description') if repo_info else None,
                last_updated=repo_info.get('updated_at') if repo_info else None
            )
            
            return source
            
        except Exception as e:
            logger.error(f"Error processing GitHub item: {e}")
            return None
    
    def _is_subscription_file(self, file_path: str) -> bool:
        """Check if a file path looks like a subscription file."""
        subscription_indicators = [
            'sub', 'subscribe', 'config', 'node', 'server', 'proxy',
            'v2ray', 'clash', 'singbox', 'hysteria', 'reality'
        ]
        
        file_lower = file_path.lower()
        return any(indicator in file_lower for indicator in subscription_indicators)
    
    async def _get_repository_info(self, repo_name: str) -> Optional[Dict]:
        """Get detailed repository information."""
        if not self.github_token:
            return None
        
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {self.github_token}'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.github.com/repos/{repo_name}", headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.error(f"Error getting repo info for {repo_name}: {e}")
        
        return None
    
    async def _score_sources(self, sources: List[DiscoveredSource]) -> List[DiscoveredSource]:
        """Score sources based on multiple factors."""
        scored = []
        
        for source in sources:
            score = await self._calculate_source_score(source)
            source.discovery_score = score
            scored.append(source)
        
        # Sort by score (descending)
        scored.sort(key=lambda x: x.discovery_score, reverse=True)
        return scored
    
    async def _calculate_source_score(self, source: DiscoveredSource) -> float:
        """Calculate comprehensive source score."""
        score = 0.0
        
        # Repository metrics (if available)
        if source.repository_info:
            # Stars weight (capped at 1000)
            score += min(source.stars / 100, 10)
            
            # Recent updates weight
            if source.last_updated:
                days_old = (datetime.now() - source.last_updated).days
                if days_old < 7:
                    score += 5
                elif days_old < 30:
                    score += 3
                elif days_old < 90:
                    score += 1
            
            # Forks indicate trust
            score += min(source.forks / 10, 5)
            
            # Language preference
            if source.language in ['Python', 'Go', 'JavaScript', 'TypeScript']:
                score += 2
            
            # Topics relevance
            vpn_topic_score = sum(2 for topic in source.topics if any(keyword in topic.lower() for keyword in self.vpn_keywords))
            score += min(vpn_topic_score, 5)
        
        # URL structure quality
        url_lower = source.url.lower()
        if any(keyword in url_lower for keyword in ['official', 'verified', 'trusted', 'main', 'master']):
            score += 3
        
        if any(keyword in url_lower for keyword in ['config', 'sub', 'subscribe']):
            score += 2
        
        # Penalize suspicious patterns
        if any(pattern in url_lower for pattern in ['temp', 'test', 'backup', 'old', 'dev', 'beta']):
            score -= 5
        
        # Source type preference
        if source.source_type == 'github':
            score += 2
        
        # Discovery method preference
        if source.discovery_method == 'api':
            score += 1
        
        return max(0, score)
    
    def _is_rate_limited(self) -> bool:
        """Check if we're rate limited."""
        return self.rate_limit_remaining <= 10
    
    async def _wait_for_rate_limit(self):
        """Wait for rate limit to reset."""
        if self.rate_limit_reset:
            wait_time = (self.rate_limit_reset - datetime.now()).total_seconds()
            if wait_time > 0:
                logger.info(f"Waiting {wait_time:.0f} seconds for rate limit reset")
                await asyncio.sleep(wait_time)
    
    async def discover_from_telegram(self, channels: List[str]) -> List[DiscoveredSource]:
        """Discover sources from Telegram channels (placeholder for future implementation)."""
        # This would require Telegram API integration
        logger.info("Telegram discovery not yet implemented")
        return []
    
    async def discover_from_websites(self, websites: List[str]) -> List[DiscoveredSource]:
        """Discover sources by crawling websites."""
        discovered = []
        
        async with aiohttp.ClientSession() as session:
            for website in websites:
                try:
                    sources = await self._crawl_website(session, website)
                    discovered.extend(sources)
                except Exception as e:
                    logger.error(f"Error crawling {website}: {e}")
        
        return discovered
    
    async def _crawl_website(self, session: aiohttp.ClientSession, website: str) -> List[DiscoveredSource]:
        """Crawl a website for subscription links."""
        try:
            async with session.get(website, timeout=30) as response:
                if response.status != 200:
                    return []
                
                content = await response.text()
                
                # Find subscription URLs
                sources = []
                for pattern in self.source_patterns['subscription']:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        source = DiscoveredSource(
                            url=match,
                            source_type='website',
                            discovery_method='crawl',
                            discovered_at=datetime.now()
                        )
                        sources.append(source)
                
                return sources
                
        except Exception as e:
            logger.error(f"Error crawling {website}: {e}")
            return []
    
    async def validate_discovered_sources(self, sources: List[DiscoveredSource]) -> List[DiscoveredSource]:
        """Validate discovered sources to ensure they're accessible."""
        valid_sources = []
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for source in sources:
                task = self._validate_source_async(session, source)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Validation error for {sources[i].url}: {result}")
                    continue
                
                if result:
                    valid_sources.append(sources[i])
        
        return valid_sources
    
    async def _validate_source_async(self, session: aiohttp.ClientSession, source: DiscoveredSource) -> bool:
        """Asynchronously validate a single source."""
        try:
            async with session.head(source.url, timeout=10) as response:
                return response.status == 200
        except Exception:
            return False
    
    def export_discovery_report(self, output_path: str = "discovery_report.json"):
        """Export discovery results to JSON."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_discovered': len(self.discovered_sources),
            'sources': []
        }
        
        for source in self.discovered_sources.values():
            source_dict = {
                'url': source.url,
                'source_type': source.source_type,
                'discovery_method': source.discovery_method,
                'discovery_score': source.discovery_score,
                'stars': source.stars,
                'forks': source.forks,
                'language': source.language,
                'topics': source.topics,
                'description': source.description,
                'discovered_at': source.discovered_at.isoformat(),
                'verified': source.verified
            }
            report['sources'].append(source_dict)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Discovery report exported to {output_path}")
        return output_path
    
    def get_discovery_stats(self) -> Dict:
        """Get discovery statistics."""
        total = len(self.discovered_sources)
        if total == 0:
            return {}
        
        by_type = {}
        by_method = {}
        score_distribution = {'high': 0, 'medium': 0, 'low': 0}
        
        for source in self.discovered_sources.values():
            # Count by type
            by_type[source.source_type] = by_type.get(source.source_type, 0) + 1
            
            # Count by method
            by_method[source.discovery_method] = by_method.get(source.discovery_method, 0) + 1
            
            # Score distribution
            if source.discovery_score >= 7:
                score_distribution['high'] += 1
            elif source.discovery_score >= 4:
                score_distribution['medium'] += 1
            else:
                score_distribution['low'] += 1
        
        return {
            'total_discovered': total,
            'by_source_type': by_type,
            'by_discovery_method': by_method,
            'score_distribution': score_distribution,
            'average_score': sum(s.discovery_score for s in self.discovered_sources.values()) / total,
            'last_discovery': max(s.discovered_at for s in self.discovered_sources.values()).isoformat() if total > 0 else None
        }
