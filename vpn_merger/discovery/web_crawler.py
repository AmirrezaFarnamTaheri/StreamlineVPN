"""
Intelligent Web Crawler
=====================

Intelligent web crawler for discovering VPN configuration sources.
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from urllib.parse import urlparse, urljoin

import aiohttp
import aiofiles

# Web scraping
try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False

from .models import DiscoveredSource, extract_configs_from_text, detect_protocols_from_text

logger = logging.getLogger(__name__)

# Web crawling constants
DEFAULT_CRAWL_DEPTH = 2
DEFAULT_MAX_PAGES_PER_SITE = 10
DEFAULT_REQUEST_DELAY = 1.0  # seconds
DEFAULT_TIMEOUT = 30.0

# Common VPN-related websites
VPN_RELATED_DOMAINS = {
    'github.com', 'gitlab.com', 'pastebin.com', 'gist.github.com',
    'raw.githubusercontent.com', 'cdn.jsdelivr.net', 'unpkg.com'
}

# User agent for web requests
DEFAULT_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
)


class IntelligentWebCrawler:
    """Intelligent web crawler for discovering VPN configuration sources."""
    
    def __init__(self, max_depth: int = DEFAULT_CRAWL_DEPTH, 
                 max_pages_per_site: int = DEFAULT_MAX_PAGES_PER_SITE):
        """Initialize web crawler.
        
        Args:
            max_depth: Maximum crawl depth
            max_pages_per_site: Maximum pages to crawl per site
        """
        self.max_depth = max_depth
        self.max_pages_per_site = max_pages_per_site
        self.discovered_sources = []
        self.visited_urls: Set[str] = set()
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
            headers={'User-Agent': DEFAULT_USER_AGENT}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def crawl_website(self, start_url: str) -> List[DiscoveredSource]:
        """Crawl a website for VPN configurations.
        
        Args:
            start_url: Starting URL for crawling
            
        Returns:
            List of discovered sources
        """
        if not self.session:
            raise RuntimeError("Crawler not initialized. Use async context manager.")
        
        discovered_sources = []
        urls_to_crawl = [(start_url, 0)]  # (url, depth)
        
        while urls_to_crawl:
            url, depth = urls_to_crawl.pop(0)
            
            if depth > self.max_depth or url in self.visited_urls:
                continue
            
            self.visited_urls.add(url)
            
            try:
                # Crawl the page
                page_sources = await self._crawl_single_page(url)
                discovered_sources.extend(page_sources)
                
                # Add new URLs to crawl if not at max depth
                if depth < self.max_depth:
                    new_urls = await self._extract_links(url)
                    for new_url in new_urls[:self.max_pages_per_site]:
                        if new_url not in self.visited_urls:
                            urls_to_crawl.append((new_url, depth + 1))
                
                # Rate limiting
                await asyncio.sleep(DEFAULT_REQUEST_DELAY)
                
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                continue
        
        self.discovered_sources.extend(discovered_sources)
        logger.info(f"Discovered {len(discovered_sources)} sources from {start_url}")
        return discovered_sources
    
    async def _crawl_single_page(self, url: str) -> List[DiscoveredSource]:
        """Crawl a single page for VPN configurations.
        
        Args:
            url: URL to crawl
            
        Returns:
            List of discovered sources
        """
        discovered_sources = []
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return discovered_sources
                
                content_type = response.headers.get('content-type', '')
                if 'text/html' not in content_type and 'text/plain' not in content_type:
                    return discovered_sources
                
                text = await response.text()
                
                # Extract configurations from text
                configs = extract_configs_from_text(text)
                if not configs:
                    return discovered_sources
                
                # Parse HTML for additional information
                title = url
                description = ""
                
                if BEAUTIFULSOUP_AVAILABLE and 'text/html' in content_type:
                    soup = BeautifulSoup(text, 'html.parser')
                    title_elem = soup.find('title')
                    if title_elem:
                        title = title_elem.get_text().strip()
                    
                    # Extract meta description
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc:
                        description = meta_desc.get('content', '')
                
                # Calculate reliability score
                reliability_score = self._calculate_web_reliability(url, len(configs), text)
                
                # Create discovered source
                source = DiscoveredSource(
                    url=url,
                    source_type='web',
                    title=title,
                    description=description[:200] + "..." if len(description) > 200 else description,
                    discovered_at=datetime.now(),
                    reliability_score=reliability_score,
                    config_count=len(configs),
                    protocols=detect_protocols_from_text(text),
                    region=self._detect_region_from_url(url)
                )
                discovered_sources.append(source)
                
        except Exception as e:
            logger.debug(f"Error crawling single page {url}: {e}")
        
        return discovered_sources
    
    async def _extract_links(self, url: str) -> List[str]:
        """Extract links from a webpage.
        
        Args:
            url: URL to extract links from
            
        Returns:
            List of extracted URLs
        """
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return []
                
                text = await response.text()
                
                if not BEAUTIFULSOUP_AVAILABLE:
                    return []
                
                soup = BeautifulSoup(text, 'html.parser')
                links = []
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    absolute_url = urljoin(url, href)
                    
                    # Filter out non-HTTP URLs and already visited URLs
                    if (absolute_url.startswith('http') and 
                        absolute_url not in self.visited_urls and
                        self._is_valid_crawl_target(absolute_url)):
                        links.append(absolute_url)
                
                return list(set(links))  # Remove duplicates
                
        except Exception as e:
            logger.debug(f"Error extracting links from {url}: {e}")
            return []
    
    def _is_valid_crawl_target(self, url: str) -> bool:
        """Check if URL is a valid crawl target.
        
        Args:
            url: URL to check
            
        Returns:
            True if valid crawl target
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Skip certain domains
            skip_domains = {
                'google.com', 'facebook.com', 'twitter.com', 'youtube.com',
                'amazon.com', 'ebay.com', 'wikipedia.org'
            }
            
            if domain in skip_domains:
                return False
            
            # Skip certain file types
            skip_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                             '.zip', '.rar', '.exe', '.dmg', '.pkg'}
            
            if any(url.lower().endswith(ext) for ext in skip_extensions):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _calculate_web_reliability(self, url: str, config_count: int, content: str) -> float:
        """Calculate reliability score for web source.
        
        Args:
            url: Source URL
            config_count: Number of configurations found
            content: Page content
            
        Returns:
            Reliability score between 0.0 and 1.0
        """
        score = 0.0
        
        # Configuration count (0-50 points)
        score += min(50, config_count * 5)
        
        # Content length (0-20 points)
        content_length = len(content)
        score += min(20, content_length / 1000)
        
        # Domain reputation (0-30 points)
        domain = urlparse(url).netloc.lower()
        if domain in VPN_RELATED_DOMAINS:
            score += 30
        elif any(keyword in domain for keyword in ['vpn', 'proxy', 'config']):
            score += 20
        elif any(keyword in domain for keyword in ['github', 'gitlab', 'pastebin']):
            score += 15
        
        return min(1.0, score / 100.0)
    
    def _detect_region_from_url(self, url: str) -> str:
        """Detect region from URL.
        
        Args:
            url: URL to analyze
            
        Returns:
            Detected region
        """
        domain = urlparse(url).netloc.lower()
        
        # Simple region detection based on TLD
        region_mapping = {
            '.cn': 'china',
            '.jp': 'japan',
            '.kr': 'korea',
            '.sg': 'singapore',
            '.hk': 'hongkong',
            '.tw': 'taiwan',
            '.us': 'united_states',
            '.uk': 'united_kingdom',
            '.de': 'germany',
            '.fr': 'france',
            '.nl': 'netherlands',
            '.ru': 'russia'
        }
        
        for tld, region in region_mapping.items():
            if domain.endswith(tld):
                return region
        
        return 'global'
    
    async def search_multiple_sites(self, urls: List[str]) -> List[DiscoveredSource]:
        """Search multiple websites for VPN configurations.
        
        Args:
            urls: List of URLs to search
            
        Returns:
            List of discovered sources
        """
        all_sources = []
        
        async with self:
            tasks = [self.crawl_website(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_sources.extend(result)
                else:
                    logger.error(f"Error in site search: {result}")
        
        return all_sources
    
    def get_discovery_stats(self) -> Dict[str, Any]:
        """Get discovery statistics.
        
        Returns:
            Dictionary containing discovery statistics
        """
        return {
            'total_sources': len(self.discovered_sources),
            'active_sources': len([s for s in self.discovered_sources if s.is_active]),
            'average_reliability': sum(s.reliability_score for s in self.discovered_sources) / 
                                 max(len(self.discovered_sources), 1),
            'visited_urls': len(self.visited_urls),
            'total_configs_found': sum(s.config_count for s in self.discovered_sources)
        }
