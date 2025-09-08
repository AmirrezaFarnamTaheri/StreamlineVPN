"""
Configuration Processor (Refactored)
=====================================

Refactored configuration processing system for StreamlineVPN.
"""

import hashlib
from typing import Any, Dict, List, Optional

from ..models.configuration import VPNConfiguration
from ..utils.logging import get_logger
from .processing import (
    ConfigurationDeduplicator,
    ConfigurationParser,
    ConfigurationValidator,
)

logger = get_logger(__name__)


class ConfigurationProcessor:
    """Processor for parsing, validating, and deduplicating configs."""

    def __init__(self):
        """Initialize configuration processor."""
        self.parser = ConfigurationParser()
        self.validator = ConfigurationValidator()
        self.deduplicator = ConfigurationDeduplicator()
        # Simple stats tracking
        self._stats: Dict[str, Any] = {
            "parsed": 0,
            "validated": 0,
            "deduplicated": 0,
        }

    def parse_configurations(
        self, content: str, source_type: str = "mixed"
    ) -> List[Dict[str, Any]]:
        """Parse configurations from content.

        Args:
            content: Raw configuration content
            source_type: Type of source content

        Returns:
            List of parsed configuration dictionaries
        """
        configs = []

        # Split content into lines
        lines = content.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                config = self.parser.parse_configuration(line)
                if config:
                    configs.append(self._config_to_dict(config))
            except Exception as e:
                logger.debug(f"Failed to parse line: {e}")
                continue

        logger.info(
            f"Parsed {len(configs)} configurations from {source_type} source"
        )
        return configs

    def validate_configuration(
        self,
        config_data: Dict[str, Any],
        rules: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Validate a configuration.

        Args:
            config_data: Configuration data to validate
            rules: Optional validation rules

        Returns:
            True if valid
        """
        try:
            config = self._dict_to_config(config_data)
            is_valid, errors = self.validator.validate_configuration(
                config, rules
            )

            if is_valid:
                self._stats["validated"] += 1
            else:
                logger.debug(f"Invalid configuration: {', '.join(errors)}")

            return is_valid

        except Exception as e:
            logger.debug(f"Validation error: {e}")
            return False

    # Backwards compatibility wrapper expected by some tests
    def validate_config(self, config_data: Dict[str, Any]) -> bool:
        """Validate configuration data using default rules.

        This is a simple alias to :meth:`validate_configuration` kept for
        historical reasons where the shorter method name was used.
        """
        return self.validate_configuration(config_data)

    def deduplicate_configurations(
        self, configs: List[VPNConfiguration], strategy: str = "exact"
    ) -> List[VPNConfiguration]:
        unique = self.deduplicator.deduplicate_configurations(
            configs, strategy
        )
        self._stats["deduplicated"] += max(0, len(configs) - len(unique))
        return unique

    def generate_config_id(self, config_data: Dict[str, Any]) -> str:
        """Generate a unique ID for a configuration.

        Args:
            config_data: Configuration data

        Returns:
            Unique configuration ID
        """
        # Create a hash of the configuration content
        protocol = config_data.get("protocol", "")
        server = config_data.get("server", "")
        port = config_data.get("port", "")
        content = f"{protocol}:{server}:{port}"
        return hashlib.md5(content.encode()).hexdigest()[:8]

    # Backwards-compatibility: single-line async parse API expected by tests
    async def parse_config(
        self, config_line: str
    ) -> Optional[VPNConfiguration]:
        """Parse a single configuration line to a VPNConfiguration or None.

        The test suite expects this to be an async method returning None for
        invalid lines.
        """
        if not isinstance(config_line, str) or not config_line.strip():
            return None
        try:
            cfg = self.parser.parse_configuration(config_line.strip())
            if cfg:
                self._stats["parsed"] += 1
            return cfg
        except Exception:
            return None

    # Backwards-compatibility: internal hash helper expected by tests
    def _generate_config_hash(self, config_line: str) -> str:
        """Generate a stable hash for a raw configuration line."""
        if not isinstance(config_line, str):
            config_line = str(config_line)
        return hashlib.md5(config_line.encode("utf-8")).hexdigest()

    # Minimal statistics API expected by tests
    def get_statistics(self) -> Dict[str, Any]:
        return dict(self._stats)

    def process_configurations(
        self,
        content: str,
        source_type: str = "mixed",
        validation_rules: Optional[Dict[str, Any]] = None,
        deduplication_strategy: str = "exact",
    ) -> List[VPNConfiguration]:
        """Process configurations from content.

        Args:
            content: Raw configuration content
            source_type: Type of source content
            validation_rules: Optional validation rules
            deduplication_strategy: Deduplication strategy

        Returns:
            List of processed configurations
        """
        try:
            # Parse configurations
            configs_data = self.parse_configurations(content, source_type)

            # Convert to VPNConfiguration objects
            configs = []
            for config_data in configs_data:
                try:
                    config = self._dict_to_config(config_data)
                    configs.append(config)
                except Exception as e:
                    logger.debug(f"Failed to create configuration: {e}")
                    continue

            # Validate configurations
            if validation_rules:
                try:
                    configs = self.validator.validate_configurations(
                        configs, validation_rules
                    )
                except Exception as e:
                    logger.error(f"Configuration validation failed: {e}")
                    # Continue with unvalidated configs

            # Deduplicate configurations
            try:
                configs = self.deduplicate_configurations(
                    configs, deduplication_strategy
                )
            except Exception as e:
                logger.error(f"Configuration deduplication failed: {e}")
                # Continue with duplicated configs

            logger.info(f"Processed {len(configs)} valid configurations")
            return configs
        except Exception as e:
            logger.error(f"Failed to process configurations: {e}", exc_info=True)
            return []

    def _config_to_dict(self, config: VPNConfiguration) -> Dict[str, Any]:
        """Convert VPNConfiguration to dictionary.

        Args:
            config: VPN configuration

        Returns:
            Configuration dictionary
        """
        return {
            "id": config.id,
            "protocol": config.protocol.value,
            "server": config.server,
            "port": config.port,
            "user_id": config.user_id,
            "password": config.password,
            "encryption": config.encryption,
            "network": config.network,
            "path": config.path,
            "host": config.host,
            "tls": config.tls,
            "quality_score": config.quality_score,
            "source_url": config.source_url,
            "created_at": (
                config.created_at.isoformat() if config.created_at else None
            ),
            "metadata": config.metadata,
        }

    def _dict_to_config(self, config_data: Dict[str, Any]) -> VPNConfiguration:
        """Convert dictionary to VPNConfiguration.

        Args:
            config_data: Configuration dictionary

        Returns:
            VPN configuration
        """
        from datetime import datetime

        from ..models.configuration import Protocol

        try:
            # Handle protocol conversion safely
            protocol_value = config_data.get("protocol", "unknown")
            try:
                protocol = Protocol(protocol_value)
            except ValueError:
                logger.warning(f"Unknown protocol: {protocol_value}, using vmess")
                protocol = Protocol.VMESS

            # Handle created_at conversion safely
            created_at = None
            if config_data.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(config_data["created_at"])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid created_at format: {config_data.get('created_at')}")

            return VPNConfiguration(
                id=config_data.get("id", ""),
                protocol=protocol,
                server=config_data.get("server", ""),
                port=config_data.get("port", 0),
                user_id=config_data.get("user_id", ""),
                password=config_data.get("password", ""),
                encryption=config_data.get("encryption", ""),
                network=config_data.get("network", ""),
                path=config_data.get("path", ""),
                host=config_data.get("host", ""),
                tls=config_data.get("tls", False),
                quality_score=config_data.get("quality_score", 0.0),
                source_url=config_data.get("source_url", ""),
                created_at=created_at,
                metadata=config_data.get("metadata", {}),
            )
        except Exception as e:
            logger.error(f"Failed to convert dict to config: {e}")
            raise ValueError(f"Invalid configuration data: {e}")
