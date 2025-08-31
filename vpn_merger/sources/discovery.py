"""
Source Discovery
===============

Automatic discovery of VPN configuration sources.
"""

import asyncio
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import aiohttp

logger = logging.getLogger(__name__)


async def discover_all(limit: Optional[int] = None) -> List[str]:
    """Discover all available VPN configuration sources.
    
    Args:
        limit: Maximum number of sources to return (None for all)
    
    Returns:
        List of discovered source URLs
    """
    logger.info("Starting source discovery...")
    
    # Known source patterns and repositories
    discovery_sources = [
        "https://raw.githubusercontent.com/freefq/free/master/v2",
        "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
        "https://raw.githubusercontent.com/ermaozi/get_subscribe/master/subscribe/v2ray.txt",
        "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription1",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/ssrsub",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/ss-sub",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/v2ray",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/trojan",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/clash",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/surge",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/quantumult",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/quantumultx",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/surfboard",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/loon",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/stash",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/shadowrocket",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/ssr",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/ss",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/trojan",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/v2ray",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/clash",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/surge",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/quantumult",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/quantumultx",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/surfboard",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/loon",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/stash",
        "https://raw.githubusercontent.com/ssrsub/ssr/master/shadowrocket"
    ]
    
    discovered_sources = []
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for source in discovery_sources:
            task = asyncio.create_task(_validate_source(session, source))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to validate {discovery_sources[i]}: {result}")
            elif result:
                discovered_sources.append(discovery_sources[i])
    
    logger.info(f"Discovery completed: {len(discovered_sources)} valid sources found")
    
    if limit is not None:
        discovered_sources = discovered_sources[:limit]
        logger.info(f"Limited to {len(discovered_sources)} sources")
    
    return discovered_sources


async def _validate_source(session: aiohttp.ClientSession, url: str) -> bool:
    """Validate if a source URL is accessible and contains VPN configurations.
    
    Args:
        session: aiohttp session
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status == 200:
                content = await response.text()
                # Check if content contains VPN configuration patterns
                if _contains_vpn_configs(content):
                    logger.debug(f"Valid source found: {url}")
                    return True
                else:
                    logger.debug(f"Source does not contain VPN configs: {url}")
                    return False
            else:
                logger.debug(f"Source not accessible (HTTP {response.status}): {url}")
                return False
    except Exception as e:
        logger.debug(f"Error validating source {url}: {e}")
        return False


def _contains_vpn_configs(content: str) -> bool:
    """Check if content contains VPN configuration patterns.
    
    Args:
        content: Content to analyze
        
    Returns:
        True if VPN configs found, False otherwise
    """
    vpn_patterns = [
        'vmess://',
        'vless://',
        'trojan://',
        'ss://',
        'ssr://',
        'http://',
        'https://',
        'socks://',
        'socks5://'
    ]
    
    content_lower = content.lower()
    return any(pattern in content_lower for pattern in vpn_patterns)


async def discover_from_github_repos() -> List[str]:
    """Discover sources from GitHub repositories.
    
    Returns:
        List of discovered source URLs
    """
    logger.info("Discovering sources from GitHub repositories...")
    
    # GitHub repositories known to contain VPN configurations
    repos = [
        "freefq/free",
        "peasoft/NoMoreWalls", 
        "ermaozi/get_subscribe",
        "w1770946466/Auto_proxy",
        "ssrsub/ssr"
    ]
    
    discovered_sources = []
    
    async with aiohttp.ClientSession() as session:
        for repo in repos:
            try:
                sources = await _discover_from_repo(session, repo)
                discovered_sources.extend(sources)
            except Exception as e:
                logger.warning(f"Failed to discover from repo {repo}: {e}")
    
    logger.info(f"GitHub discovery completed: {len(discovered_sources)} sources found")
    return discovered_sources


async def _discover_from_repo(session: aiohttp.ClientSession, repo: str) -> List[str]:
    """Discover sources from a specific GitHub repository.
    
    Args:
        session: aiohttp session
        repo: Repository name (owner/repo)
        
    Returns:
        List of discovered source URLs
    """
    sources = []
    
    # Common file patterns for VPN configurations
    file_patterns = [
        "v2ray.txt",
        "list.txt", 
        "sub.txt",
        "config.txt",
        "proxy.txt",
        "clash.yaml",
        "clash.yml"
    ]
    
    base_url = f"https://raw.githubusercontent.com/{repo}/master/"
    
    for pattern in file_patterns:
        url = urljoin(base_url, pattern)
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    sources.append(url)
                    logger.debug(f"Found source: {url}")
        except Exception:
            continue
    
    return sources
