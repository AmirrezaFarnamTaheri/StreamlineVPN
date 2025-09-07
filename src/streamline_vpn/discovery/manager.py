"""
Discovery Manager - Complete Implementation
===========================================
"""

import asyncio
import re
import aiohttp
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import base64

from ..utils.logging import get_logger
from ..security.validator import SecurityValidator

logger = get_logger(__name__)


class DiscoveryManager:
    """Manages source discovery and validation with full API integration."""

    def __init__(self):
        """Initialize discovery manager."""
        self.discovered_sources: Set[str] = set()
        self.last_discovery = datetime.now()
        self.discovery_interval = timedelta(hours=6)
        self.validator = SecurityValidator()

        # GitHub API configuration
        self.github_api_url = "https://api.github.com"
        self.github_token = None  # Optional: Set via environment variable
        self.github_search_queries = [
            "vpn+config+subscription+in:readme",
            "v2ray+subscription+in:description",
            "clash+subscription+yaml",
            "shadowsocks+subscription+base64",
            "trojan+vless+vmess+subscription"
        ]

        # Common subscription file patterns
        self.subscription_patterns = [
            "subscription.txt", "sub.txt", "subscribe.txt",
            "configs.txt", "nodes.txt", "servers.txt",
            "vpn.txt", "proxy.txt", "free.txt"
        ]

        # Rate limiting
        self.rate_limit_remaining = 60
        self.rate_limit_reset = datetime.now()

        logger.info("Discovery manager initialized with full API support")

    async def discover_sources(self) -> List[str]:
        """Discover new sources from various platforms."""
        sources = []

        # Run discovery tasks concurrently
        tasks = [
            self._discover_github_sources(),
            self._discover_gitlab_sources(),
            self._discover_gitee_sources(),
            self._discover_public_lists()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                sources.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Discovery task failed: {result}")

        # Filter and validate sources
        valid_sources = []
        for source in sources:
            if self.validator.validate_url(source) and source not in self.discovered_sources:
                valid_sources.append(source)
                self.discovered_sources.add(source)

        logger.info(f"Discovered {len(valid_sources)} new sources")
        return valid_sources

    async def _discover_github_sources(self) -> List[str]:
        """Discover sources from GitHub repositories with full API integration."""
        sources = []

        try:
            async with aiohttp.ClientSession() as session:
                # Check rate limit
                if not await self._check_github_rate_limit(session):
                    logger.warning("GitHub API rate limit exceeded")
                    return sources

                for query in self.github_search_queries:
                    try:
                        # Search repositories
                        search_url = f"{self.github_api_url}/search/repositories"
                        params = {
                            'q': query,
                            'sort': 'updated',
                            'order': 'desc',
                            'per_page': 30
                        }

                        headers = {
                            'Accept': 'application/vnd.github.v3+json',
                            'User-Agent': 'StreamlineVPN/2.0'
                        }

                        if self.github_token:
                            headers['Authorization'] = f'token {self.github_token}'

                        async with session.get(
                            search_url,
                            params=params,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as response:
                            if response.status == 200:
                                data = await response.json()

                                # Process each repository
                                for repo in data.get('items', []):
                                    repo_sources = await self._scan_repository(
                                        session, repo['full_name'], headers
                                    )
                                    sources.extend(repo_sources)

                            elif response.status == 403:
                                logger.warning("GitHub API rate limit reached")
                                break

                    except asyncio.TimeoutError:
                        logger.warning(f"GitHub search timeout for query: {query}")
                    except Exception as e:
                        logger.error(f"GitHub search error for query {query}: {e}")

                # Also check known good repositories
                known_repos = [
                    "mahdibland/V2RayAggregator",
                    "peasoft/NoMoreWalls",
                    "aiboboxx/v2rayfree",
                    "Leon406/SubCrawler",
                    "ripaojiedian/freenode"
                ]

                for repo in known_repos:
                    repo_sources = await self._scan_repository(session, repo, headers)
                    sources.extend(repo_sources)

            logger.info(f"Discovered {len(sources)} GitHub sources")

        except Exception as e:
            logger.error(f"GitHub discovery failed: {e}")

        return sources

    async def _scan_repository(
        self,
        session: aiohttp.ClientSession,
        repo_name: str,
        headers: Dict[str, str]
    ) -> List[str]:
        """Scan a specific repository for subscription files."""
        sources = []

        try:
            # Get repository contents
            contents_url = f"{self.github_api_url}/repos/{repo_name}/contents"

            async with session.get(
                contents_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    contents = await response.json()

                    for item in contents:
                        if item['type'] == 'file':
                            # Check if filename matches subscription patterns
                            filename = item['name'].lower()
                            if any(pattern in filename for pattern in self.subscription_patterns):
                                # Get raw URL
                                raw_url = f"https://raw.githubusercontent.com/{repo_name}/main/{item['name']}"

                                # Verify the file exists and contains valid content
                                if await self._validate_source_content(session, raw_url):
                                    sources.append(raw_url)
                                    logger.debug(f"Found subscription file: {raw_url}")

                        elif item['type'] == 'dir' and item['name'] in ['sub', 'subscription', 'config']:
                            # Recursively scan subscription directories
                            dir_sources = await self._scan_directory(
                                session, repo_name, item['path'], headers
                            )
                            sources.extend(dir_sources)

        except Exception as e:
            logger.debug(f"Error scanning repository {repo_name}: {e}")

        return sources

    async def _scan_directory(
        self,
        session: aiohttp.ClientSession,
        repo_name: str,
        path: str,
        headers: Dict[str, str]
    ) -> List[str]:
        """Scan a directory in a repository for subscription files."""
        sources = []

        try:
            dir_url = f"{self.github_api_url}/repos/{repo_name}/contents/{path}"

            async with session.get(
                dir_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    contents = await response.json()

                    for item in contents:
                        if item['type'] == 'file' and item['name'].endswith(('.txt', '.yaml', '.yml', '.json')):
                            raw_url = f"https://raw.githubusercontent.com/{repo_name}/main/{item['path']}"

                            if await self._validate_source_content(session, raw_url):
                                sources.append(raw_url)

        except Exception as e:
            logger.debug(f"Error scanning directory {path}: {e}")

        return sources

    async def _discover_gitlab_sources(self) -> List[str]:
        """Discover sources from GitLab repositories."""
        sources = []

        try:
            gitlab_api_url = "https://gitlab.com/api/v4"

            async with aiohttp.ClientSession() as session:
                # Search projects
                search_terms = ["vpn subscription", "v2ray config", "clash rules"]

                for term in search_terms:
                    params = {
                        'search': term,
                        'order_by': 'last_activity_at',
                        'sort': 'desc',
                        'per_page': 20
                    }

                    async with session.get(
                        f"{gitlab_api_url}/projects",
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            projects = await response.json()

                            for project in projects:
                                # Check for subscription files
                                for pattern in self.subscription_patterns:
                                    for branch in ['main', 'master']:
                                        url = f"https://gitlab.com/{project['path_with_namespace']}/-/raw/{branch}/{pattern}"

                                        if await self._validate_source_exists(session, url):
                                            sources.append(url)
                                            logger.debug(f"Found GitLab source: {url}")

            logger.info(f"Discovered {len(sources)} GitLab sources")

        except Exception as e:
            logger.error(f"GitLab discovery failed: {e}")

        return sources

    async def _discover_gitee_sources(self) -> List[str]:
        """Discover sources from Gitee (Chinese GitHub alternative)."""
        sources = []

        try:
            gitee_api_url = "https://gitee.com/api/v5"

            async with aiohttp.ClientSession() as session:
                # Search repositories
                search_queries = ["vpn订阅", "v2ray配置", "clash规则", "免费节点"]

                for query in search_queries:
                    params = {
                        'q': query,
                        'sort': 'updated',
                        'order': 'desc',
                        'per_page': 20
                    }

                    async with session.get(
                        f"{gitee_api_url}/search/repositories",
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()

                            for repo in data:
                                # Check for subscription files
                                for pattern in self.subscription_patterns:
                                    url = f"https://gitee.com/{repo['full_name']}/raw/master/{pattern}"

                                    if await self._validate_source_exists(session, url):
                                        sources.append(url)
                                        logger.debug(f"Found Gitee source: {url}")

            logger.info(f"Discovered {len(sources)} Gitee sources")

        except Exception as e:
            logger.error(f"Gitee discovery failed: {e}")

        return sources

    async def _discover_public_lists(self) -> List[str]:
        """Discover sources from known public subscription lists."""
        sources = []

        # Known public subscription aggregators
        public_lists = [
            "https://raw.githubusercontent.com/freefq/free/master/v2",
            "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
            "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
            "https://raw.githubusercontent.com/vveg26/get_proxy/main/dist/v2ray.config.txt",
            "https://raw.githubusercontent.com/mianfeifq/share/main/data2023087.txt"
        ]

        async with aiohttp.ClientSession() as session:
            for url in public_lists:
                if await self._validate_source_exists(session, url):
                    sources.append(url)
                    logger.debug(f"Found public list source: {url}")

        logger.info(f"Discovered {len(sources)} public list sources")
        return sources

    async def _validate_source_exists(self, session: aiohttp.ClientSession, url: str) -> bool:
        """Validate if a source URL exists and is accessible."""
        try:
            async with session.head(
                url,
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
        except Exception:
            return False

    async def _validate_source_content(self, session: aiohttp.ClientSession, url: str) -> bool:
        """Validate if a source contains valid VPN configurations."""
        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    content = await response.text()

                    # Check for VPN protocol patterns
                    vpn_patterns = [
                        r'vmess://',
                        r'vless://',
                        r'trojan://',
                        r'ss://',
                        r'ssr://',
                        r'hysteria://'
                    ]

                    return any(re.search(pattern, content) for pattern in vpn_patterns)
        except Exception:
            pass

        return False

    async def _check_github_rate_limit(self, session: aiohttp.ClientSession) -> bool:
        """Check GitHub API rate limit."""
        try:
            headers = {'Accept': 'application/vnd.github.v3+json'}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'

            async with session.get(
                f"{self.github_api_url}/rate_limit",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.rate_limit_remaining = data['rate']['remaining']
                    self.rate_limit_reset = datetime.fromtimestamp(data['rate']['reset'])

                    return self.rate_limit_remaining > 10
        except Exception:
            pass

        return True

    def get_statistics(self) -> Dict[str, any]:
        """Get discovery statistics."""
        return {
            'discovered_sources_count': len(self.discovered_sources),
            'last_discovery': self.last_discovery.isoformat(),
            'discovery_interval_hours': self.discovery_interval.total_seconds() / 3600,
            'github_queries': len(self.github_search_queries),
            'rate_limit_remaining': self.rate_limit_remaining,
            'rate_limit_reset': self.rate_limit_reset.isoformat()
        }

