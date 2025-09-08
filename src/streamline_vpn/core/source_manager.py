"""
Source Manager
==============

Manages VPN configuration sources.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..models.processing_result import ProcessingResult
from ..models.source import SourceMetadata, SourceTier
from ..security.manager import SecurityManager
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SourceManager:
    """Manages VPN configuration sources with reputation tracking."""

    def __init__(
        self,
        config_path: str,
        security_manager: Optional[SecurityManager] = None,
    ):
        """Initialize source manager.

        Args:
            config_path: Path to sources configuration file
            security_manager: Optional security manager for validating sources
        """
        self.config_path = Path(config_path)
        self.sources: Dict[str, SourceMetadata] = {}
        self.performance_file = Path("data/source_performance.json")
        self.security_manager = security_manager or SecurityManager()
        self._lock = asyncio.Lock()

        # Load sources and performance data
        self._load_sources()
        self._load_performance_data()

    def _load_sources(self) -> None:
        """Load sources from configuration file."""
        try:
            if not self.config_path.exists():
                logger.warning(
                    f"Configuration file not found: {self.config_path}"
                )
                return

            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            sources_config = config.get("sources", {})

            for tier_name, tier_data in sources_config.items():
                if not isinstance(tier_data, dict) or "urls" not in tier_data:
                    continue

                tier = SourceTier(tier_name)

                for source_config in tier_data["urls"]:
                    if isinstance(source_config, dict):
                        url = source_config.get("url")
                        validation_result = (
                            self.security_manager.validate_source(url)
                        )
                        if url and validation_result["is_safe"]:
                            metadata = SourceMetadata(
                                url=url,
                                tier=tier,
                                weight=source_config.get("weight", 0.5),
                                protocols=source_config.get(
                                    "protocols", ["all"]
                                ),
                                update_frequency=source_config.get(
                                    "update", "24h"
                                ),
                                metadata=source_config.get("metadata", {}),
                            )
                            self.sources[url] = metadata
                        else:
                            logger.warning(
                                f"Invalid or unsafe source URL: {url}"
                            )
                    elif isinstance(source_config, str):
                        validation_result = (
                            self.security_manager.validate_source(
                                source_config
                            )
                        )
                        if validation_result["is_safe"]:
                            metadata = SourceMetadata(
                                url=source_config,
                                tier=tier,
                                weight=0.5,
                                protocols=["all"],
                                update_frequency="24h",
                            )
                            self.sources[source_config] = metadata
                        else:
                            logger.warning(
                                "Invalid or unsafe source URL: %s",
                                source_config,
                            )

            logger.info(
                f"Loaded {len(self.sources)} sources "
                f"from {self.config_path}"
            )

        except Exception as e:
            logger.error(f"Failed to load sources: {e}")

    def _load_performance_data(self) -> None:
        """Load historical performance data."""
        try:
            if not self.performance_file.exists():
                return

            with open(self.performance_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for url, perf_data in data.items():
                if url in self.sources:
                    source = self.sources[url]
                    source.history = perf_data.get("history", [])
                    source.success_count = perf_data.get("success_count", 0)
                    source.failure_count = perf_data.get("failure_count", 0)
                    source.avg_response_time = perf_data.get(
                        "avg_response_time", 0.0
                    )
                    source.avg_config_count = perf_data.get(
                        "avg_config_count", 0
                    )
                    source.reputation_score = perf_data.get(
                        "reputation_score", 0.5
                    )
                    source.is_blacklisted = perf_data.get(
                        "is_blacklisted", False
                    )
                    source.update_reputation()

            logger.info(f"Loaded performance data for {len(data)} sources")

        except Exception as e:
            logger.error(f"Failed to load performance data: {e}")

    async def add_source(
        self, url: str, tier: SourceTier = SourceTier.RELIABLE
    ) -> SourceMetadata:
        """Add a new source after validation and persist it."""
        async with self._lock:
            raw_url = url.strip()
            if not raw_url:
                raise ValueError("Source URL is required")
            if self.security_manager is None:
                raise ValueError("Security validation is unavailable")

            from urllib.parse import urlparse, urlunparse

            parsed = urlparse(raw_url)
            netloc = (parsed.hostname or "").lower()
            if parsed.port and (
                (parsed.scheme == "http" and parsed.port != 80)
                or (parsed.scheme == "https" and parsed.port != 443)
            ):
                netloc = f"{netloc}:{parsed.port}"
            norm_path = parsed.path.rstrip("/") or "/"
            normalized_url = urlunparse(
                (
                    parsed.scheme.lower(),
                    netloc,
                    norm_path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )

            if normalized_url in self.sources:
                raise ValueError("Source already exists")

            validation = self.security_manager.validate_source(normalized_url)
            if not validation.get("is_safe") or not validation.get(
                "is_valid_url", False
            ):
                raise ValueError("Invalid or unsafe source URL")

            metadata = SourceMetadata(url=normalized_url, tier=tier)
            await self._persist_new_source_atomically(metadata)
            self.sources[normalized_url] = metadata
            return metadata

    async def _persist_new_source_atomically(
        self, metadata: SourceMetadata
    ) -> None:
        """Persist a newly added source to the configuration file atomically."""
        try:
            config_data: Dict[str, Any] = {}
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f) or {}

            sources_cfg = config_data.setdefault("sources", {})
            tier_key = self._find_tier_key(metadata.tier, sources_cfg)
            tier_section = sources_cfg.setdefault(tier_key, {})
            url_list = tier_section.setdefault("urls", [])
            url_list.append(
                {
                    "url": metadata.url,
                    "weight": metadata.weight,
                    "protocols": metadata.protocols,
                    "update": metadata.update_frequency,
                    "metadata": metadata.metadata,
                }
            )

            temp_path = self.config_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(config_data, f, sort_keys=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, self.config_path)
        except Exception as exc:  # pragma: no cover - logging path
            logger.error("Failed to persist new source: %s", exc)
            raise

    def _find_tier_key(
        self, tier: SourceTier, sources_cfg: Dict[str, Any]
    ) -> str:
        """Find the appropriate key for a tier in the config file."""
        for key in sources_cfg:
            if tier.value in key.lower():
                return key
        return tier.value

    async def save_performance_data(self) -> None:
        """Save performance data to file."""
        try:
            self.performance_file.parent.mkdir(parents=True, exist_ok=True)

            data = {}
            for url, source in self.sources.items():
                data[url] = {
                    "history": source.history[-100:],  # Keep last 100 records
                    "success_count": source.success_count,
                    "failure_count": source.failure_count,
                    "avg_response_time": source.avg_response_time,
                    "avg_config_count": source.avg_config_count,
                    "reputation_score": source.reputation_score,
                    "is_blacklisted": source.is_blacklisted,
                }

            with open(self.performance_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Saved performance data for {len(data)} sources")

        except Exception as e:
            logger.error(f"Failed to save performance data: {e}")

    async def get_active_sources(self, max_sources: int = 100) -> List[str]:
        """Get active sources that should be processed.

        Args:
            max_sources: Maximum number of sources to return

        Returns:
            List of source URLs
        """
        # Filter sources that need updating and are not blacklisted
        eligible_sources = []

        for url, source in self.sources.items():
            if not source.is_blacklisted and source.should_update():
                eligible_sources.append((source.reputation_score, url))

        # Sort by reputation score (descending)
        eligible_sources.sort(reverse=True)

        # Return top sources
        return [url for _, url in eligible_sources[:max_sources]]

    async def get_sources_by_tier(self, tier: SourceTier) -> List[str]:
        """Get sources by tier.

        Args:
            tier: Source tier

        Returns:
            List of source URLs for the tier
        """
        return [
            url
            for url, source in self.sources.items()
            if source.tier == tier and not source.is_blacklisted
        ]

    async def fetch_source(self, source_url: str) -> ProcessingResult:
        """Fetch configuration from a source.

        Args:
            source_url: Source URL to fetch

        Returns:
            Processing result
        """
        import aiohttp

        # Import moved to avoid circular imports

        start_time = datetime.now()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(source_url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.text()
                        configs = self._parse_configs(content)

                        response_time = (
                            datetime.now() - start_time
                        ).total_seconds()

                        return ProcessingResult(
                            url=source_url,
                            success=True,
                            configs=configs,
                            response_time=response_time,
                            config_count=len(configs),
                        )
                    else:
                        return ProcessingResult(
                            url=source_url,
                            success=False,
                            error=f"HTTP {response.status}: {response.reason}",
                            response_time=(
                                datetime.now() - start_time
                            ).total_seconds(),
                        )

        except asyncio.TimeoutError:
            return ProcessingResult(
                url=source_url,
                success=False,
                error="Request timeout",
                response_time=(datetime.now() - start_time).total_seconds(),
            )
        except Exception as e:
            return ProcessingResult(
                url=source_url,
                success=False,
                error=str(e),
                response_time=(datetime.now() - start_time).total_seconds(),
            )

    def _parse_configs(self, content: str) -> List[str]:
        """Parse configurations from content.

        Args:
            content: Raw content from source

        Returns:
            List of configuration lines
        """
        configs = []
        for line in content.splitlines():
            line = line.strip()
            if self._is_valid_config_line(line):
                configs.append(line)
        return configs

    def _is_valid_config_line(self, line: str) -> bool:
        """Check if line is a valid configuration.

        Args:
            line: Line to check

        Returns:
            True if valid configuration
        """
        if not line:
            return False

        valid_protocols = [
            "vmess://",
            "vless://",
            "trojan://",
            "ss://",
            "ssr://",
            "hysteria://",
            "hysteria2://",
            "tuic://",
        ]

        return any(line.startswith(protocol) for protocol in valid_protocols)

    async def update_source_performance(
        self,
        source_url: str,
        success: bool,
        config_count: int,
        response_time: float,
    ) -> None:
        """Update source performance metrics.

        Args:
            source_url: Source URL
            success: Whether fetch was successful
            config_count: Number of configurations found
            response_time: Response time in seconds
        """
        if source_url in self.sources:
            self.sources[source_url].add_performance_record(
                success, config_count, response_time
            )

    def get_source_statistics(self) -> Dict[str, Any]:
        """Get source statistics.

        Returns:
            Statistics dictionary
        """
        total_sources = len(self.sources)
        active_sources = len(
            [s for s in self.sources.values() if not s.is_blacklisted]
        )
        blacklisted_sources = len(
            [s for s in self.sources.values() if s.is_blacklisted]
        )

        tier_counts = {}
        for source in self.sources.values():
            tier = source.tier.value
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        avg_reputation = sum(
            s.reputation_score for s in self.sources.values()
        ) / max(total_sources, 1)

        return {
            "total_sources": total_sources,
            "active_sources": active_sources,
            "blacklisted_sources": blacklisted_sources,
            "tier_distribution": tier_counts,
            "average_reputation": avg_reputation,
            "top_sources": self._get_top_sources(10),
        }

    def _get_top_sources(self, count: int) -> List[Dict[str, Any]]:
        """Get top performing sources.

        Args:
            count: Number of top sources to return

        Returns:
            List of top source information
        """
        sorted_sources = sorted(
            self.sources.items(),
            key=lambda x: x[1].reputation_score,
            reverse=True,
        )

        return [
            {
                "url": url,
                "tier": source.tier.value,
                "reputation_score": source.reputation_score,
                "success_count": source.success_count,
                "failure_count": source.failure_count,
                "avg_config_count": source.avg_config_count,
            }
            for url, source in sorted_sources[:count]
        ]

    def blacklist_source(self, source_url: str, reason: str = "") -> None:
        """Blacklist a source.

        Args:
            source_url: Source URL to blacklist
            reason: Reason for blacklisting
        """
        if source_url in self.sources:
            self.sources[source_url].is_blacklisted = True
            self.sources[source_url].metadata["blacklist_reason"] = reason
            logger.warning(f"Blacklisted source {source_url}: {reason}")

    def whitelist_source(self, source_url: str) -> None:
        """Remove source from blacklist.

        Args:
            source_url: Source URL to whitelist
        """
        if source_url in self.sources:
            self.sources[source_url].is_blacklisted = False
            if "blacklist_reason" in self.sources[source_url].metadata:
                del self.sources[source_url].metadata["blacklist_reason"]
            logger.info(f"Whitelisted source {source_url}")
