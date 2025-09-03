"""
Configuration Processor
=====================

Handles VPN configuration parsing, validation, and deduplication.
"""

import logging
import re

from ..models.configuration import VPNConfiguration

logger = logging.getLogger(__name__)


class ConfigurationProcessor:
    """Configuration processing and deduplication with quality assessment.

    This class handles the parsing, validation, and deduplication of VPN configurations
    with comprehensive protocol detection and quality scoring.

    Attributes:
        processed_configs: Set of already processed configuration strings
        _protocol_patterns: Compiled regex patterns for protocol detection
    """

    def __init__(self):
        """Initialize the configuration processor."""
        self.processed_configs: set[str] = set()
        self._protocol_patterns = self._init_protocol_patterns()

    def _init_protocol_patterns(self) -> dict[str, str]:
        """Initialize protocol detection patterns.

        Returns:
            Dictionary mapping protocol names to regex patterns
        """
        return {
            "vmess": r"^vmess://",
            "vless": r"^vless://",
            "trojan": r"^trojan://",
            "shadowsocks": r"^(ss://|shadowsocks://)",
            "shadowsocksr": r"^ssr://",
            "hysteria": r"^hysteria(2)?://",
            "tuic": r"^tuic://",
        }

    def process_config(self, config: str, source_url: str | None = None) -> VPNConfiguration | None:
        """Process a single configuration with validation and deduplication.

        Args:
            config: Raw configuration string to process
            source_url: Optional source URL for tracking

        Returns:
            VPNConfiguration object if valid, None otherwise
        """
        if not config or not isinstance(config, str):
            return None

        config = config.strip()

        # Basic validation
        if not self._is_valid_config(config):
            return None

        # Deduplication
        if self._is_duplicate(config):
            return None

        # Parse protocol and extract basic info
        protocol = self._detect_protocol(config)
        host, port = self._extract_host_port(config)

        # Create result
        try:
            result = VPNConfiguration(
                config=config,
                protocol=protocol,
                host=host,
                port=port,
                source_url=source_url,
                quality_score=self._calculate_quality_score(config, protocol),
            )

            # Mark as processed
            self._mark_processed(config)

            return result

        except Exception as e:
            logger.debug(f"Failed to create VPNConfiguration for config: {e}")
            return None

    def _is_valid_config(self, config: str) -> bool:
        """Check if configuration is valid.

        Args:
            config: Configuration string to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        if not config:
            return False

        # Strip whitespace for validation
        config = config.strip()

        # Check minimum length (some valid configs can be short)
        if len(config) < 8:  # Minimum: protocol:// + at least 1 char
            return False

        # Check maximum length to prevent extremely long configs
        if len(config) > 10000:  # Maximum reasonable length
            return False

        # Check for basic protocol indicators
        valid_protocols = [
            "vmess://",
            "vless://",
            "trojan://",
            "ss://",
            "ssr://",
            "hysteria://",
            "tuic://",
            "hysteria2://",
        ]

        # Check if config starts with a valid protocol
        for proto in valid_protocols:
            if config.startswith(proto):
                # Ensure there's content after the protocol
                if len(config) <= len(proto):
                    return False
                return True

        return False

    def _is_duplicate(self, config: str) -> bool:
        """Check if configuration is duplicate.

        Args:
            config: Configuration string to check

        Returns:
            True if duplicate, False otherwise
        """
        # Strip whitespace for deduplication check
        stripped_config = config.strip()
        return stripped_config in self.processed_configs

    def _mark_processed(self, config: str) -> None:
        """Mark configuration as processed.

        Args:
            config: Configuration string to mark
        """
        # Store stripped config for consistent deduplication
        stripped_config = config.strip()
        self.processed_configs.add(stripped_config)

    def _detect_protocol(self, config: str) -> str:
        """Detect protocol from configuration using regex patterns.

        Args:
            config: Configuration string to analyze

        Returns:
            Detected protocol name or 'unknown'
        """
        # Strip whitespace for protocol detection
        config = config.strip()

        for protocol, pattern in self._protocol_patterns.items():
            if re.match(pattern, config, re.IGNORECASE):
                return protocol

        return "unknown"

    def _extract_host_port(self, config: str) -> tuple[str | None, int | None]:
        """Extract host and port from configuration.

        Args:
            config: Configuration string to parse

        Returns:
            Tuple of (host, port) or (None, None) if extraction fails
        """
        try:
            # This is a simplified extraction - in practice, you'd want more robust parsing
            if "://" in config:
                parts = config.split("://", 1)
                if len(parts) == 2:
                    # For now, return None - proper parsing would require protocol-specific logic
                    return None, None
            return None, None
        except Exception as e:
            logger.debug(f"Error extracting host/port from config: {e}")
            return None, None

    def _calculate_quality_score(self, config: str, protocol: str) -> float:
        """Calculate quality score for configuration.

        Args:
            config: Configuration string
            protocol: Detected protocol

        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.0

        # Protocol preference
        protocol_scores = {
            "vmess": 0.8,
            "vless": 0.9,
            "trojan": 0.85,
            "shadowsocks": 0.7,
            "shadowsocksr": 0.6,
            "hysteria": 0.75,
            "tuic": 0.8,
        }

        score += protocol_scores.get(protocol, 0.5)

        # Length bonus (longer configs often have more options)
        score += min(0.2, len(config) / 1000)

        return min(1.0, score)

    def get_processed_count(self) -> int:
        """Get count of processed configurations.

        Returns:
            Number of processed configurations
        """
        return len(self.processed_configs)

    def clear_processed(self) -> None:
        """Clear processed configurations cache."""
        self.processed_configs.clear()

    def get_protocol_distribution(self, configs: list[VPNConfiguration]) -> dict[str, int]:
        """Get distribution of protocols in configurations.

        Args:
            configs: List of VPN configurations to analyze

        Returns:
            Dictionary mapping protocol names to counts
        """
        distribution: dict[str, int] = {}
        for config in configs:
            protocol = config.protocol
            distribution[protocol] = distribution.get(protocol, 0) + 1
        return distribution

    def get_quality_distribution(self, configs: list[VPNConfiguration]) -> dict[str, int]:
        """Get distribution of quality scores in configurations.

        Args:
            configs: List of VPN configurations to analyze

        Returns:
            Dictionary mapping quality categories to counts
        """
        distribution = {
            "excellent": 0,  # 0.9-1.0
            "good": 0,  # 0.7-0.89
            "fair": 0,  # 0.5-0.69
            "poor": 0,  # 0.0-0.49
        }

        for config in configs:
            score = config.quality_score
            if score >= 0.9:
                distribution["excellent"] += 1
            elif score >= 0.7:
                distribution["good"] += 1
            elif score >= 0.5:
                distribution["fair"] += 1
            else:
                distribution["poor"] += 1

        return distribution

    def get_processing_stats(self) -> dict[str, int | float]:
        """Get comprehensive processing statistics.

        Returns:
            Dictionary containing processing statistics
        """
        return {
            "processed_count": self.get_processed_count(),
            "cache_size": len(self.processed_configs),
            "protocol_patterns": len(self._protocol_patterns),
        }
