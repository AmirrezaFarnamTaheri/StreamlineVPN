"""Discovery Manager - Complete Implementation.

Manages source discovery and validation with full API integration.
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Set

import aiohttp

from ..security.validator import SecurityValidator
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DiscoveryManager:
    """Manages source discovery and validation with API integration."""

    def __init__(self) -> None:
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
            "trojan+vless+vmess+subscription",
        ]

        # Common subscription file patterns
        self.subscription_patterns = [
            "subscription.txt",
            "sub.txt",
            "subscribe.txt",
            "configs.txt",
            "nodes.txt",
            "servers.txt",
            "vpn.txt",
            "proxy.txt",
            "free.txt",
        ]

        # Rate limiting
        self.rate_limit_remaining = 60
        self.rate_limit_reset = datetime.now()

        logger.info("Discovery manager initialized with full API support")

    async def discover_sources(self) -> List[str]:
        """Discover new sources from various platforms."""

        sources: List[str] = []

        tasks = [
            self._discover_github_sources(),
            self._discover_gitlab_sources(),
            self._discover_gitee_sources(),
            self._discover_public_lists(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                sources.extend(result)
            elif isinstance(result, Exception):
                logger.error("Discovery task failed: %s", result)

        valid_sources: List[str] = []
        for source in sources:
            if (
                self.validator.validate_url(source)
                and source not in self.discovered_sources
            ):
                valid_sources.append(source)
                self.discovered_sources.add(source)

        logger.info("Discovered %d new sources", len(valid_sources))
        return valid_sources

    async def _discover_github_sources(self) -> List[str]:
        """Discover sources from GitHub repositories with API integration."""

        sources: List[str] = []

        try:
            async with aiohttp.ClientSession() as session:
                if not await self._check_github_rate_limit(session):
                    logger.warning("GitHub API rate limit exceeded")
                    return sources

                headers = {
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "StreamlineVPN/2.0",
                }
                if self.github_token:
                    headers["Authorization"] = f"token {self.github_token}"

                for query in self.github_search_queries:
                    try:
                        search_url = (
                            f"{self.github_api_url}/search/repositories"
                        )
                        params = {
                            "q": query,
                            "sort": "updated",
                            "order": "desc",
                            "per_page": 30,
                        }
                        async with session.get(
                            search_url,
                            params=params,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=30),
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                for repo in data.get("items", []):
                                    repo_sources = (
                                        await self._scan_repository(
                                            session,
                                            repo["full_name"],
                                            headers,
                                        )
                                    )
                                    sources.extend(repo_sources)
                            elif response.status == 403:
                                logger.warning(
                                    "GitHub API rate limit reached"
                                )
                                break
                    except asyncio.TimeoutError:
                        logger.warning(
                            f"GitHub search timeout for query: {query}"
                        )
                    except Exception as exc:  # pragma: no cover
                        logger.error(
                            f"GitHub search error for query {query}: {exc}"
                        )

                known_repos = [
                    "mahdibland/V2RayAggregator",
                    "peasoft/NoMoreWalls",
                    "aiboboxx/v2rayfree",
                    "Leon406/SubCrawler",
                    "ripaojiedian/freenode",
                ]

                for repo in known_repos:
                    repo_sources = await self._scan_repository(
                        session, repo, headers
                    )
                    sources.extend(repo_sources)

            logger.info("Discovered %d GitHub sources", len(sources))
        except Exception as exc:  # pragma: no cover - network errors
            logger.error("GitHub discovery failed: %s", exc, exc_info=True)

        return sources

    async def _scan_repository(
        self,
        session: aiohttp.ClientSession,
        repo_name: str,
        headers: Dict[str, str],
    ) -> List[str]:
        """Scan a specific repository for subscription files."""

        sources: List[str] = []

        try:
            contents_url = (
                f"{self.github_api_url}/repos/{repo_name}/contents"
            )
            async with session.get(
                contents_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                if response.status == 200:
                    contents = await response.json()
                    for item in contents:
                        if item["type"] == "file":
                            filename = item["name"].lower()
                            if any(
                                pattern in filename
                                for pattern in self.subscription_patterns
                            ):
                                raw_url = (
                                    f"https://raw.githubusercontent.com/"
                                    f"{repo_name}/main/{item['name']}"
                                )
                                if await self._validate_source_content(
                                    session, raw_url
                                ):
                                    sources.append(raw_url)
                                    logger.debug(
                                        "Found subscription file: %s", raw_url
                                    )
                        elif item["type"] == "dir" and item["name"] in [
                            "sub",
                            "subscription",
                            "config",
                        ]:
                            dir_sources = await self._scan_directory(
                                session, repo_name, item["path"], headers
                            )
                            sources.extend(dir_sources)
        except Exception as exc:  # pragma: no cover - network errors
            logger.debug("Error scanning repository %s: %s", repo_name, exc, exc_info=True)

        return sources

    async def _scan_directory(
        self,
        session: aiohttp.ClientSession,
        repo_name: str,
        path: str,
        headers: Dict[str, str],
    ) -> List[str]:
        """Scan a directory in a repository for subscription files."""

        sources: List[str] = []

        try:
            dir_url = (
                f"{self.github_api_url}/repos/{repo_name}/contents/{path}"
            )
            async with session.get(
                dir_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    contents = await response.json()
                    for item in contents:
                        if item["type"] == "file" and item["name"].endswith(
                            (".txt", ".yaml", ".yml", ".json")
                        ):
                            raw_url = (
                                f"https://raw.githubusercontent.com/"
                                f"{repo_name}/main/{item['path']}"
                            )
                            if await self._validate_source_content(
                                session, raw_url
                            ):
                                sources.append(raw_url)
        except Exception as exc:  # pragma: no cover - network errors
            logger.debug("Error scanning directory %s: %s", path, exc, exc_info=True)

        return sources

    async def _discover_gitlab_sources(self) -> List[str]:
        """Discover sources from GitLab repositories."""

        sources: List[str] = []
        try:
            gitlab_api_url = "https://gitlab.com/api/v4"

            async with aiohttp.ClientSession() as session:
                search_terms = [
                    "vpn subscription",
                    "v2ray config",
                    "clash rules",
                ]
                for term in search_terms:
                    params = {
                        "search": term,
                        "order_by": "last_activity_at",
                        "sort": "desc",
                        "per_page": 20,
                    }
                    async with session.get(
                        f"{gitlab_api_url}/projects",
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        if response.status == 200:
                            projects = await response.json()
                            for project in projects:
                                for pattern in self.subscription_patterns:
                                    for branch in ["main", "master"]:
                                        url = (
                                            f"https://gitlab.com/"
                                            f"{project['path_with_namespace']}"
                                            f"/-/raw/{branch}/{pattern}"
                                        )
                                        if await self._validate_source_exists(
                                            session, url
                                        ):
                                            sources.append(url)
                                            logger.debug(
                                                "Found GitLab source: %s", url
                                            )
        except Exception as exc:  # pragma: no cover - network errors
            logger.error("GitLab discovery failed: %s", exc, exc_info=True)

        logger.info("Discovered %d GitLab sources", len(sources))
        return sources

    async def _discover_gitee_sources(self) -> List[str]:
        """Discover sources from Gitee repositories."""

        sources: List[str] = []
        try:
            gitee_api_url = "https://gitee.com/api/v5"

            async with aiohttp.ClientSession() as session:
                search_queries = [
                    "vpn订阅",
                    "v2ray配置",
                    "clash规则",
                    "免费节点",
                ]
                for query in search_queries:
                    params = {
                        "q": query,
                        "sort": "updated",
                        "order": "desc",
                        "per_page": 20,
                    }
                    async with session.get(
                        f"{gitee_api_url}/search/repositories",
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            for repo in data:
                                for pattern in self.subscription_patterns:
                                    url = (
                                        f"https://gitee.com/"
                                        f"{repo['full_name']}/raw/master/"
                                        f"{pattern}"
                                    )
                                    if await self._validate_source_exists(
                                        session, url
                                    ):
                                        sources.append(url)
                                        logger.debug(
                                            "Found Gitee source: %s", url
                                        )
        except Exception as exc:  # pragma: no cover - network errors
            logger.error("Gitee discovery failed: %s", exc, exc_info=True)

        logger.info("Discovered %d Gitee sources", len(sources))
        return sources

    async def _discover_public_lists(self) -> List[str]:
        """Discover sources from known public subscription lists."""

        sources: List[str] = []
        public_lists = [
            "https://raw.githubusercontent.com/freefq/free/master/v2",
            "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
            (
                "https://raw.githubusercontent.com/ermaozi/"
                "get_subscribe/main/subscribe/v2ray.txt"
            ),
            (
                "https://raw.githubusercontent.com/vveg26/"
                "get_proxy/main/dist/v2ray.config.txt"
            ),
            (
                "https://raw.githubusercontent.com/mianfeifq/"
                "share/main/data2023087.txt"
            ),
        ]

        async with aiohttp.ClientSession() as session:
            for url in public_lists:
                if await self._validate_source_exists(session, url):
                    sources.append(url)
                    logger.debug("Found public list source: %s", url)

        logger.info("Discovered %d public list sources", len(sources))
        return sources

    async def _validate_source_exists(
        self, session: aiohttp.ClientSession, url: str
    ) -> bool:
        """Validate if a source URL exists and is accessible."""

        try:
            async with session.head(
                url,
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                return response.status == 200
        except Exception:  # pragma: no cover - network errors
            return False

    async def _validate_source_content(
        self, session: aiohttp.ClientSession, url: str
    ) -> bool:
        """Validate if a source contains valid VPN configurations."""

        try:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    vpn_patterns = [
                        r"vmess://",
                        r"vless://",
                        r"trojan://",
                        r"ss://",
                        r"ssr://",
                        r"hysteria://",
                    ]
                    return any(
                        re.search(pattern, content)
                        for pattern in vpn_patterns
                    )
        except Exception:  # pragma: no cover - network errors
            pass

        return False

    async def _check_github_rate_limit(
        self, session: aiohttp.ClientSession
    ) -> bool:
        """Check GitHub API rate limit."""

        try:
            headers = {"Accept": "application/vnd.github.v3+json"}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"

            async with session.get(
                f"{self.github_api_url}/rate_limit", headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.rate_limit_remaining = data["rate"]["remaining"]
                    self.rate_limit_reset = datetime.fromtimestamp(
                        data["rate"]["reset"]
                    )
                    return self.rate_limit_remaining > 10
        except Exception:  # pragma: no cover - network errors
            pass

        return True

    def should_discover(self) -> bool:
        """Check if it's time to run discovery."""

        return datetime.now() - self.last_discovery > self.discovery_interval

    def update_discovery_time(self) -> None:
        """Update last discovery time."""

        self.last_discovery = datetime.now()

    def get_discovered_sources(self) -> List[str]:
        """Get all discovered sources."""

        return list(self.discovered_sources)

    def clear_discovered_sources(self) -> None:
        """Clear discovered sources cache."""

        self.discovered_sources.clear()
        logger.info("Discovered sources cache cleared")

    def get_statistics(self) -> Dict[str, Any]:
        """Get discovery statistics."""

        return {
            "discovered_sources_count": len(self.discovered_sources),
            "last_discovery": self.last_discovery.isoformat(),
            "discovery_interval_hours": (
                self.discovery_interval.total_seconds() / 3600
            ),
            "github_queries": len(self.github_search_queries),
            "rate_limit_remaining": self.rate_limit_remaining,
            "rate_limit_reset": self.rate_limit_reset.isoformat(),
        }
