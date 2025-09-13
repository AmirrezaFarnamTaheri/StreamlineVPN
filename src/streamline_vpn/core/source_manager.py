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
from ..fetcher.service import FetcherService

logger = get_logger(__name__)


class SourceManager:
    """Manages VPN configuration sources with reputation tracking."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        security_manager: Optional[SecurityManager] = None,
        fetcher_service: Optional[FetcherService] = None,
    ):
        """Initialize source manager.

        Args:
            config_path: Path to sources configuration file
            security_manager: Optional security manager for validating sources
            fetcher_service: Optional fetcher service for fetching sources
        """
        # Use default config if not provided
        if config_path is None:
            config_path = Path(__file__).parents[3] / "config" / "sources.yaml"
            logger.info("Using default config path: %s", config_path)
        
        self.config_path = Path(config_path)
        logger.info("Initializing SourceManager with config: %s", self.config_path)
        
        # Validate config file exists (do not hard-fail in test/mocked flows)
        if not self.config_path.exists():
            logger.warning(
                "Configuration file not found: %s; proceeding with empty sources",
                self.config_path,
            )
        
        # Validate it's not the unified file (which should be deleted)
        if "unified" in str(self.config_path):
            logger.warning("Unified config detected, switching to main sources.yaml")
            self.config_path = self.config_path.parent / "sources.yaml"
            if not self.config_path.exists():
                logger.error("Main sources.yaml not found: %s", self.config_path)
                raise FileNotFoundError(f"Main sources.yaml not found: {self.config_path}")
            logger.info("Switched to main sources.yaml: %s", self.config_path)
        
        self.sources: Dict[str, SourceMetadata] = {}
        self.performance_file = Path("data/source_performance.json")
        self.security_manager = security_manager or SecurityManager()
        self.fetcher_service = fetcher_service
        self._lock = asyncio.Lock()

        # Load sources and performance data
        self._load_sources()
        self._load_performance_data()

    def _load_sources(self) -> None:
        """Load sources from configuration file."""
        try:
            logger.info("Loading sources from configuration file: %s", self.config_path)
            
            if not self.config_path.exists():
                logger.error("Configuration file not found: %s", self.config_path)
                return

            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config:
                logger.warning("Configuration file is empty or invalid")
                return

            sources_config = config.get("sources", {})
            logger.info("Found %d source tiers in configuration", len(sources_config))

            for tier_name, tier_data in sources_config.items():
                if not isinstance(tier_data, dict) or "urls" not in tier_data:
                    logger.warning(
                        "Invalid tier configuration for %s: expected {'urls': [...]}, got %r",
                        tier_name,
                        tier_data,
                    )
                    continue

                tier_str = tier_name.split('_')[-1]
                try:
                    tier = SourceTier(tier_str)
                    logger.debug("Processing tier: %s (%s)", tier_name, tier_str)
                except ValueError:
                    valid = ", ".join(t.value for t in SourceTier)
                    logger.warning(
                        "Unknown tier '%s' encountered; valid tiers are [%s]. Skipping",
                        tier_name,
                        valid,
                    )
                    continue

                for source_config in tier_data["urls"]:
                    try:
                        if isinstance(source_config, dict):
                            url = source_config.get("url")
                            if not url:
                                continue
                            validation_result = (
                                self.security_manager.validate_source(url)
                            )
                            if validation_result["is_safe"]:
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
                                    "Invalid or unsafe source URL: %s - Reason: %s", 
                                    url, 
                                    validation_result.get("reason", "Unknown")
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
                    except Exception as source_error:
                        logger.error(
                            "Failed to process source config: %s - Config: %s", 
                            source_error, 
                            source_config
                        )
                        continue

            tier_counts: Dict[str, int] = {}
            for src in self.sources.values():
                tier_counts[src.tier.value] = tier_counts.get(src.tier.value, 0) + 1
            logger.info(
                "Successfully loaded %d sources from %s",
                len(self.sources),
                self.config_path,
            )
            logger.info("Tier distribution: %s", tier_counts)

        except yaml.YAMLError as e:
            logger.error("Failed to parse YAML configuration: %s - File: %s", e, self.config_path)
            raise ValueError(f"Invalid YAML format in {self.config_path}") from e
        except Exception as e:
            logger.error("Failed to load sources: %s - File: %s", e, self.config_path, exc_info=True)

    def _load_performance_data(self) -> None:
        """Load historical performance data."""
        try:
            if not self.performance_file.exists():
                return

            with open(self.performance_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                logger.warning("Performance data file is not a valid JSON object")
                return

            for url, perf_data in data.items():
                if url in self.sources and isinstance(perf_data, dict):
                    try:
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
                    except Exception as source_error:
                        logger.error("Failed to load performance data for %s: %s", url, source_error)
                        continue

            logger.info("Loaded performance data for %d sources", len(data))

        except json.JSONDecodeError as e:
            logger.error("Failed to parse performance data JSON: %s", e)
        except Exception as e:
            logger.error("Failed to load performance data: %s", e, exc_info=True)

    async def add_source(
        self, url: str, tier: SourceTier = SourceTier.RELIABLE
    ) -> SourceMetadata:
        """Add a new source after validation and persist it."""
        async with self._lock:
            try:
                raw_url = url.strip()
                if not raw_url:
                    raise ValueError("Source URL is required")
                if self.security_manager is None:
                    raise ValueError("Security validation is unavailable")

                from urllib.parse import urlparse, urlunparse

                try:
                    parsed = urlparse(raw_url)
                except Exception as e:
                    raise ValueError(f"Invalid URL format: {e}")

                netloc = (parsed.hostname or "").lower()
                if parsed.port and not (
                    (parsed.scheme == "http" and parsed.port == 80)
                    or (parsed.scheme == "https" and parsed.port == 443)
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
                self.sources[normalized_url] = metadata
                try:
                    await self._persist_new_source_atomically(metadata)
                except Exception as persist_error:
                    self.sources.pop(normalized_url, None)
                    raise ValueError(f"Failed to persist source: {persist_error}")
                return metadata
            except Exception as e:
                logger.error("Failed to add source %s: %s", url, e)
                raise

    async def _persist_new_source_atomically(
        self, metadata: SourceMetadata
    ) -> None:
        """Persist new source to config file atomically."""
        try:
            config_data: Dict[str, Any] = {}
            if self.config_path.exists():
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        config_data = yaml.safe_load(f) or {}
                except Exception as e:
                    logger.error("Failed to read existing config: %s", e)
                    config_data = {}

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
            try:
                with open(temp_path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(config_data, f, sort_keys=False)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temp_path, self.config_path)
            except Exception as write_error:
                # Clean up temp file if it exists
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except Exception:
                        pass
                raise write_error
        except Exception as exc:  # pragma: no cover - logging path
            logger.error("Failed to persist new source: %s", exc, exc_info=True)
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
                try:
                    data[url] = {
                        "history": source.history[-100:],  # Keep last 100 records
                        "success_count": source.success_count,
                        "failure_count": source.failure_count,
                        "avg_response_time": source.avg_response_time,
                        "avg_config_count": source.avg_config_count,
                        "reputation_score": source.reputation_score,
                        "is_blacklisted": source.is_blacklisted,
                    }
                except Exception as source_error:
                    logger.error("Failed to serialize performance data for %s: %s", url, source_error)
                    continue

            with open(self.performance_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)

            logger.info("Saved performance data for %d sources", len(data))

        except Exception as e:
            logger.error("Failed to save performance data: %s", e, exc_info=True)

    async def get_active_sources(self, max_sources: int = 100) -> List[str]:
        """Get active sources that should be processed.

        Args:
            max_sources: Maximum number of sources to return

        Returns:
            List of source URLs
        """
        try:
            # Filter sources that need updating and are not blacklisted
            eligible_sources = []

            for url, source in self.sources.items():
                try:
                    if not source.is_blacklisted and source.should_update():
                        eligible_sources.append((source.reputation_score, url))
                except Exception as source_error:
                    logger.error("Failed to check source %s: %s", url, source_error)
                    continue

            # Sort by reputation score (descending)
            eligible_sources.sort(reverse=True)

            # Return top sources
            return [url for _, url in eligible_sources[:max_sources]]
        except Exception as e:
            logger.error("Failed to get active sources: %s", e, exc_info=True)
            return []

    async def get_sources_by_tier(self, tier: SourceTier) -> List[str]:
        """Get sources by tier.

        Args:
            tier: Source tier

        Returns:
            List of source URLs for the tier
        """
        try:
            return [
                url
                for url, source in self.sources.items()
                if source.tier == tier and not source.is_blacklisted
            ]
        except Exception as e:
            logger.error(
                "Failed to get sources for tier '%s': %s", tier.value, e, exc_info=True
            )
            return []

    async def fetch_source(self, source_url: str) -> ProcessingResult:
        """Fetch configuration from a source.

        Args:
            source_url: Source URL to fetch

        Returns:
            Processing result
        """
        start_time = datetime.now()

        if not self.fetcher_service:
            logger.error("Fetcher service not available")
            return ProcessingResult(
                url=source_url,
                success=False,
                error="Fetcher service not available",
            )

        try:
            content = await self.fetcher_service.fetch(source_url, method="GET")
            response_time = (datetime.now() - start_time).total_seconds()

            if content:
                configs = self._parse_configs(content)
                return ProcessingResult(
                    url=source_url,
                    success=True,
                    configs=configs,
                    response_time=response_time,
                    config_count=len(configs),
                )
            else:
                # Surface last error from fetcher (if available) for better diagnostics
                detail = None
                try:
                    detail = getattr(self.fetcher_service, "get_last_error", lambda: None)()
                except Exception:
                    detail = None
                return ProcessingResult(
                    url=source_url,
                    success=False,
                    error=(
                        f"Failed to fetch content from {source_url}. "
                        + (f"Detail: {detail}" if detail else "See server logs for details.")
                    ),
                    response_time=response_time,
                )

        except Exception as e:
            logger.error(
                "Unexpected error fetching source %s: %s", source_url, e, exc_info=True
            )
            return ProcessingResult(
                url=source_url,
                success=False,
                error=(
                    f"Unexpected error while fetching {source_url}: "
                    f"{type(e).__name__}: {e}"
                ),
                response_time=(datetime.now() - start_time).total_seconds(),
            )

    def _parse_configs(self, content: str) -> List[str]:
        """Parse configurations from raw content, with fallbacks.

        Tries direct line-by-line extraction first. If no configs are found,
        attempts to decode Base64-encoded subscriptions and re-parse. Finally,
        applies minimal heuristics to extract embedded configuration lines.

        Args:
            content: Raw content fetched from a source.

        Returns:
            A list of configuration share lines (vmess://, vless://, etc.).
        """
        try:
            text = (content or "").replace("\ufeff", "").strip()
            if not text:
                return []

            # Pass 1: direct extraction from lines
            configs: List[str] = []
            for line in text.splitlines():
                s = line.strip()
                if self._is_valid_config_line(s):
                    configs.append(s)
            if configs:
                return configs

            # Pass 2: whole-body Base64 decoding (common subscription format)
            decoded = self._try_b64_decode(text)
            if decoded:
                for line in decoded.splitlines():
                    s = line.strip()
                    if self._is_valid_config_line(s):
                        configs.append(s)
                if configs:
                    return configs

            # Pass 3: handle accidental Base64 with missing padding by adding '='
            if not decoded and self._looks_like_b64(text):
                padded = self._pad_b64(text)
                decoded2 = self._try_b64_decode(padded)
                if decoded2:
                    for line in decoded2.splitlines():
                        s = line.strip()
                        if self._is_valid_config_line(s):
                            configs.append(s)
                    if configs:
                        return configs

            # Fallback: scan inline tokens (e.g., pasted content with separators)
            tokens = [t for t in text.replace("\\n", "\n").split() if t]
            for t in tokens:
                if self._is_valid_config_line(t.strip()):
                    configs.append(t.strip())

            return configs

        except Exception as parse_error:
            logger.error("Failed to parse configs: %s", parse_error, exc_info=True)
            return []

    def _looks_like_b64(self, s: str) -> bool:
        try:
            import re
            s = s.strip()
            if not s or any(ch in s for ch in ("\n", "\r", "\t", " ")):
                # Multi-line or spaced content can still be Base64; allow
                s = re.sub(r"\s+", "", s)
            return re.fullmatch(r"[A-Za-z0-9+/=]+", s) is not None and len(s) >= 16
        except Exception:
            return False

    def _pad_b64(self, s: str) -> str:
        try:
            import re
            s = re.sub(r"\s+", "", s)
            missing = (-len(s)) % 4
            return s + ("=" * missing)
        except Exception:
            return s

    def _try_b64_decode(self, s: str) -> Optional[str]:
        try:
            import base64, re
            raw = re.sub(r"\s+", "", s)
            # Attempt URL-safe first, then standard
            for decoder in (base64.urlsafe_b64decode, base64.b64decode):
                try:
                    missing = (-len(raw)) % 4
                    data = decoder(raw + ("=" * missing))
                    text = data.decode("utf-8", errors="ignore")
                    if text and any(proto in text for proto in ("vmess://", "vless://", "trojan://", "ss://", "ssr://")):
                        return text
                except Exception:
                    continue
            return None
        except Exception:
            return None

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
        try:
            if source_url in self.sources:
                self.sources[source_url].add_performance_record(
                    success, config_count, response_time
                )
        except Exception as e:
            logger.error("Failed to update source performance for %s: %s", source_url, e, exc_info=True)

    def get_source_statistics(self) -> Dict[str, Any]:
        """Get source statistics.

        Returns:
            Statistics dictionary
        """
        try:
            total_sources = len(self.sources)
            active_sources = len(
                [s for s in self.sources.values() if not s.is_blacklisted]
            )
            blacklisted_sources = len(
                [s for s in self.sources.values() if s.is_blacklisted]
            )

            tier_counts = {}
            for source in self.sources.values():
                try:
                    tier = source.tier.value
                    tier_counts[tier] = tier_counts.get(tier, 0) + 1
                except Exception as e:
                    logger.error("Failed to get tier for source: %s", e)
                    continue

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
        except Exception as e:
            logger.error("Failed to get source statistics: %s", e, exc_info=True)
            return {
                "total_sources": 0,
                "active_sources": 0,
                "blacklisted_sources": 0,
                "tier_distribution": {},
                "average_reputation": 0.0,
                "top_sources": [],
            }

    def _get_top_sources(self, count: int) -> List[Dict[str, Any]]:
        """Get top performing sources.

        Args:
            count: Number of top sources to return

        Returns:
            List of top source information
        """
        try:
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
        except Exception as e:
            logger.error("Failed to get top sources: %s", e, exc_info=True)
            return []

    def blacklist_source(self, source_url: str, reason: str = "") -> None:
        """Blacklist a source.

        Args:
            source_url: Source URL to blacklist
            reason: Reason for blacklisting
        """
        try:
            if source_url in self.sources:
                self.sources[source_url].is_blacklisted = True
                self.sources[source_url].metadata["blacklist_reason"] = reason
                logger.warning("Blacklisted source %s: %s", source_url, reason)
        except Exception as e:
            logger.error("Failed to blacklist source %s: %s", source_url, e, exc_info=True)

    def whitelist_source(self, source_url: str) -> None:
        """Remove source from blacklist.

        Args:
            source_url: Source URL to whitelist
        """
        try:
            if source_url in self.sources:
                self.sources[source_url].is_blacklisted = False
                if "blacklist_reason" in self.sources[source_url].metadata:
                    del self.sources[source_url].metadata["blacklist_reason"]
                logger.info("Whitelisted source %s", source_url)
        except Exception as e:
            logger.error("Failed to whitelist source %s: %s", source_url, e, exc_info=True)
