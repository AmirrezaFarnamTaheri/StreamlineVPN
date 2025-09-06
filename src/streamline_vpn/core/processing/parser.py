"""
Configuration Parser
====================

Handles parsing of VPN configuration strings.
"""

from typing import Optional

from ...models.configuration import VPNConfiguration
from ...utils.logging import get_logger
from .parsers import (
    parse_vmess as _parse_vmess,
    parse_vless as _parse_vless,
    parse_trojan as _parse_trojan,
    parse_ss as _parse_ss,
    parse_ssr as _parse_ssr,
)

logger = get_logger(__name__)


class ConfigurationParser:
    """Parses VPN configuration strings into structured data."""

    def __init__(self):
        """Initialize parser."""
        self.protocol_patterns = {
            "vmess": r"vmess://([A-Za-z0-9+/=]+)",
            "vless": r"vless://",
            "trojan": r"trojan://",
            "ss": r"ss://([A-Za-z0-9+/=]+)",
            "ssr": r"ssr://([A-Za-z0-9+/=]+)",
        }

    def parse_configuration(
        self, config_string: str
    ) -> Optional[VPNConfiguration]:
        """Parse a single configuration string.

        Args:
            config_string: Configuration string to parse

        Returns:
            Parsed VPN configuration or None if parsing fails
        """
        config_string = config_string.strip()
        if not config_string:
            return None

        # Try each protocol
        for protocol_name, pattern in self.protocol_patterns.items():
            try:
                config = self._parse_protocol(config_string, protocol_name)
                if config:
                    return config
            except Exception as e:
                logger.debug(f"Failed to parse {protocol_name}: {e}")
                continue

        logger.debug(f"Could not parse configuration: {config_string[:50]}...")
        return None

    def _parse_protocol(
        self, config_string: str, protocol_name: str
    ) -> Optional[VPNConfiguration]:
        """Parse configuration for a specific protocol.

        Args:
            config_string: Configuration string
            protocol_name: Protocol name
            pattern: Regex pattern for the protocol

        Returns:
            Parsed configuration or None
        """
        if protocol_name == "vmess":
            return _parse_vmess(config_string)
        elif protocol_name == "vless":
            return _parse_vless(config_string)
        elif protocol_name == "trojan":
            return _parse_trojan(config_string)
        elif protocol_name == "ss":
            return _parse_ss(config_string)
        elif protocol_name == "ssr":
            return _parse_ssr(config_string)

        return None

    # Protocol-specific parse methods now delegated to parsers package
    def _parse_vmess(self, config_string: str) -> Optional[VPNConfiguration]:
        return _parse_vmess(config_string)

    def _parse_vless(self, config_string: str) -> Optional[VPNConfiguration]:
        return _parse_vless(config_string)

    def _parse_trojan(self, config_string: str) -> Optional[VPNConfiguration]:
        return _parse_trojan(config_string)

    def _parse_ss(self, config_string: str) -> Optional[VPNConfiguration]:
        return _parse_ss(config_string)

    def _parse_ssr(self, config_string: str) -> Optional[VPNConfiguration]:
        return _parse_ssr(config_string)
