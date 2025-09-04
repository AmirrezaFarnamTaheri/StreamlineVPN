"""
GitHub Real-time Monitor
======================

Real-time GitHub repository monitor for VPN configuration sources.
"""

import logging
from datetime import datetime
from typing import Any

# GitHub API
try:
    import github
    from github import Github, GithubException

    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

from .models import GITHUB_TOPICS, DiscoveredSource, detect_protocols_from_text

logger = logging.getLogger(__name__)


class GitHubRealtimeMonitor:
    """Real-time GitHub repository monitor for VPN configuration sources."""

    def __init__(self, github_token: str | None = None):
        """Initialize GitHub monitor.

        Args:
            github_token: GitHub API token for authentication
        """
        self.github_token = github_token
        self.github_client = None
        self.monitored_topics = GITHUB_TOPICS
        self.monitored_repos = set()
        self.discovered_sources = []

        if GITHUB_AVAILABLE and github_token:
            self._initialize_github_client()

    def _initialize_github_client(self):
        """Initialize GitHub API client."""
        try:
            self.github_client = Github(self.github_token)
            logger.info("GitHub client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {e}")

    async def search_repositories(self, query: str, max_results: int = 50) -> list[dict[str, Any]]:
        """Search GitHub repositories for VPN configurations.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of repository information
        """
        if not self.github_client:
            logger.warning("GitHub client not available")
            return []

        try:
            repositories = []
            search_results = self.github_client.search_repositories(
                query=query, sort="updated", order="desc"
            )

            for repo in search_results[:max_results]:
                try:
                    repo_info = {
                        "name": repo.name,
                        "full_name": repo.full_name,
                        "description": repo.description or "",
                        "url": repo.html_url,
                        "language": repo.language,
                        "stars": repo.stargazers_count,
                        "forks": repo.forks_count,
                        "updated_at": repo.updated_at,
                        "topics": repo.get_topics(),
                    }
                    repositories.append(repo_info)
                except Exception as e:
                    logger.debug(f"Error processing repository {repo.name}: {e}")
                    continue

            logger.info(f"Found {len(repositories)} GitHub repositories for query: {query}")
            return repositories

        except Exception as e:
            logger.error(f"Error searching GitHub repositories: {e}")
            return []

    async def monitor_topics(self, topics: list[str] | None = None) -> list[DiscoveredSource]:
        """Monitor GitHub topics for new VPN configuration repositories.

        Args:
            topics: List of topics to monitor

        Returns:
            List of discovered sources
        """
        topics = topics or self.monitored_topics
        discovered_sources = []

        for topic in topics:
            try:
                query = f"topic:{topic} vpn config"
                repositories = await self.search_repositories(query, max_results=20)

                for repo in repositories:
                    source = DiscoveredSource(
                        url=repo["url"],
                        source_type="github",
                        title=repo["name"],
                        description=repo["description"],
                        discovered_at=datetime.now(),
                        reliability_score=self._calculate_github_reliability(repo),
                        config_count=0,  # Would be calculated by scanning repo
                        protocols=detect_protocols_from_text(repo["description"]),
                        region="global",
                    )
                    discovered_sources.append(source)

            except Exception as e:
                logger.error(f"Error monitoring GitHub topic {topic}: {e}")
                continue

        self.discovered_sources.extend(discovered_sources)
        logger.info(f"Discovered {len(discovered_sources)} new GitHub sources")
        return discovered_sources

    def _calculate_github_reliability(self, repo: dict[str, Any]) -> float:
        """Calculate reliability score for GitHub repository.

        Args:
            repo: Repository information dictionary

        Returns:
            Reliability score between 0.0 and 1.0
        """
        score = 0.0

        # Star count (0-50 points)
        stars = repo.get("stars", 0)
        score += min(50, stars / 10)

        # Fork count (0-20 points)
        forks = repo.get("forks", 0)
        score += min(20, forks / 5)

        # Recent updates (0-20 points)
        updated_at = repo.get("updated_at")
        if updated_at:
            days_since_update = (datetime.now() - updated_at).days
            if days_since_update < 30:
                score += 20
            elif days_since_update < 90:
                score += 10
            elif days_since_update < 365:
                score += 5

        # Description quality (0-10 points)
        description = repo.get("description", "")
        if description and len(description) > 20:
            score += 10

        return min(1.0, score / 100.0)

    async def scan_repository_files(self, repo_url: str) -> list[str]:
        """Scan repository files for VPN configurations.

        Args:
            repo_url: Repository URL

        Returns:
            List of found configuration URLs
        """
        if not self.github_client:
            return []

        try:
            # Extract owner and repo name from URL
            parts = repo_url.split("/")
            if len(parts) < 5:
                return []

            owner = parts[-2]
            repo_name = parts[-1]

            repo = self.github_client.get_repo(f"{owner}/{repo_name}")

            # Search for common configuration file patterns
            config_files = []
            search_patterns = ["*.yaml", "*.yml", "*.json", "*.txt", "*.conf"]

            for pattern in search_patterns:
                try:
                    contents = repo.get_contents("", ref="main")
                    for content in contents:
                        if content.name.endswith(pattern.split(".")[-1]):
                            config_files.append(content.download_url)
                except Exception as e:
                    logger.debug(f"Error searching for {pattern} in {repo_name}: {e}")
                    continue

            return config_files

        except Exception as e:
            logger.error(f"Error scanning repository {repo_url}: {e}")
            return []

    def get_discovery_stats(self) -> dict[str, Any]:
        """Get discovery statistics.

        Returns:
            Dictionary containing discovery statistics
        """
        return {
            "total_sources": len(self.discovered_sources),
            "active_sources": len([s for s in self.discovered_sources if s.is_active]),
            "average_reliability": sum(s.reliability_score for s in self.discovered_sources)
            / max(len(self.discovered_sources), 1),
            "monitored_topics": len(self.monitored_topics),
            "monitored_repos": len(self.monitored_repos),
        }
