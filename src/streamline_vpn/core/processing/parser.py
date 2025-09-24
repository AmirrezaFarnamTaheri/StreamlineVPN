"""
Configuration Parser
====================

Handles parsing of VPN configuration strings.
"""

from typing import Optional

from ...models.configuration import VPNConfiguration
from ...utils.logging import get_logger
from ..validation.protocols import ProtocolValidator

# Note: Parser imports moved to avoid circular dependencies
# Individual parsers are imported dynamically when needed

logger = get_logger(__name__)


class ConfigurationParser:
    """Parses VPN configuration strings into structured data."""

    def __init__(self):
        """Initialize parser."""
        self.protocol_validator = ProtocolValidator()
        self.protocol_patterns = {
            "vmess": r"vmess://([A-Za-z0-9+/=]+)",
            "vless": r"vless://",
            "trojan": r"trojan://",
            "ss": r"ss://([A-Za-z0-9+/=]+)",
            "ssr": r"ssr://([A-Za-z0-9+/=]+)",
            "http": r"http://",
            "socks5": r"socks5://",
            "tuic": r"tuic://",
        }

    def parse_configuration(self, config_string: str) -> Optional[VPNConfiguration]:
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
                    errors = self.protocol_validator.validate(config.to_dict(), config.protocol)
                    if errors:
                        logger.warning("Invalid configuration for protocol %s: %s", config.protocol, errors)
                        return None
                    return config
            except Exception as e:
                logger.debug("Failed to parse %s: %s", protocol_name, e)
                continue

        logger.debug("Could not parse configuration: %s...", config_string[:50])
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
            from .parsers.vmess import parse_vmess as _parse_vmess

            return _parse_vmess(config_string)
        elif protocol_name == "vless":
            from .parsers.vless import parse_vless as _parse_vless

            return _parse_vless(config_string)
        elif protocol_name == "trojan":
            from .parsers.trojan import parse_trojan as _parse_trojan

            return _parse_trojan(config_string)
        elif protocol_name == "ss":
            from .parsers.shadowsocks import parse_ss as _parse_ss

            return _parse_ss(config_string)
        elif protocol_name == "ssr":
            from .parsers.shadowsocksr import parse_ssr as _parse_ssr

            return _parse_ssr(config_string)
        elif protocol_name == "http":
            from .parsers.http import parse_http as _parse_http

            return _parse_http(config_string)
        elif protocol_name == "socks5":
            from .parsers.socks5 import parse_socks5 as _parse_socks5

            return _parse_socks5(config_string)
        elif protocol_name == "tuic":
            from .parsers.tuic import parse_tuic as _parse_tuic

            return _parse_tuic(config_string)

        return None

    # Protocol-specific parse methods now delegated to parsers package
    def _parse_vmess(self, config_string: str) -> Optional[VPNConfiguration]:
        from .parsers.vmess import parse_vmess as _parse_vmess

        return _parse_vmess(config_string)

    def _parse_vless(self, config_string: str) -> Optional[VPNConfiguration]:
        from .parsers.vless import parse_vless as _parse_vless

        return _parse_vless(config_string)

    def _parse_trojan(self, config_string: str) -> Optional[VPNConfiguration]:
        from .parsers.trojan import parse_trojan as _parse_trojan

        return _parse_trojan(config_string)

    def _parse_ss(self, config_string: str) -> Optional[VPNConfiguration]:
        from .parsers.shadowsocks import parse_ss as _parse_ss

        return _parse_ss(config_string)

    def _parse_ssr(self, config_string: str) -> Optional[VPNConfiguration]:
        from .parsers.shadowsocksr import parse_ssr as _parse_ssr

        return _parse_ssr(config_string)
