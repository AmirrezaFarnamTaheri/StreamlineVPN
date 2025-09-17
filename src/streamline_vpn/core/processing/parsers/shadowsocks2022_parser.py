"""Optimized Shadowsocks 2022 Parser."""

import re
from typing import Any, Dict, Optional

from ....models.configuration import Protocol, VPNConfiguration
from ....utils.logging import get_logger

logger = get_logger(__name__)


class Shadowsocks2022Parser:
    """High-performance Shadowsocks 2022 parser."""

    def __init__(self):
        """Initialize Shadowsocks 2022 parser."""
        self.ss2022_pattern = re.compile(
            r"^ss://2022-([^:]+):([^@]+)@([^:]+):(\d+)(\?.*)?$", re.IGNORECASE
        )
        self.performance_stats = {
            "parse_count": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
        }

    async def parse(self, uri: str) -> Optional[VPNConfiguration]:
        """Parse Shadowsocks 2022 URI with optimized performance.

        Args:
            uri: SS2022 URI string

        Returns:
            VPNConfiguration object or None if parsing fails
        """
        import time

        start_time = time.perf_counter()

        try:
            # Fast regex match
            match = self.ss2022_pattern.match(uri.strip())
            if not match:
                return None

            # Extract components
            method, password, host, port, query_string = match.groups()

            # Query parameters are not used in this implementation.

            # Create configuration
            config = VPNConfiguration(
                server=host,
                port=int(port),
                protocol=Protocol.SHADOWSOCKS,
                password=password,
                encryption=method,
                metadata={
                    "parser": "optimized_ss2022",
                    "version": "1.0",
                    "performance_optimized": True,
                    "security_level": self._get_security_level(method),
                    "aead_support": self._supports_aead(method),
                    "method": method,
                },
            )

            # Update performance stats
            parse_time = time.perf_counter() - start_time
            self._update_performance_stats(parse_time)

            logger.debug("SS2022 config parsed in %.2fms", parse_time * 1000)
            return config

        except Exception as e:
            logger.error("Failed to parse SS2022 URI: %s", e)
            return None

    def _get_security_level(self, method: str) -> str:
        """Get security level for encryption method.

        Args:
            method: Encryption method

        Returns:
            Security level string
        """
        high_security_methods = [
            "aes-256-gcm",
            "chacha20-poly1305",
            "xchacha20-poly1305",
        ]

        medium_security_methods = ["aes-128-gcm", "chacha20-ietf-poly1305"]

        if method in high_security_methods:
            return "high"
        elif method in medium_security_methods:
            return "medium"
        else:
            return "standard"

    def _supports_aead(self, method: str) -> bool:
        """Check if method supports AEAD.

        Args:
            method: Encryption method

        Returns:
            True if AEAD is supported
        """
        aead_methods = [
            "aes-256-gcm",
            "aes-128-gcm",
            "chacha20-poly1305",
            "chacha20-ietf-poly1305",
            "xchacha20-poly1305",
        ]

        return method in aead_methods

    def _update_performance_stats(self, parse_time: float) -> None:
        """Update performance statistics."""
        self.performance_stats["parse_count"] += 1
        self.performance_stats["total_time"] += parse_time
        self.performance_stats["avg_time"] = (
            self.performance_stats["total_time"] / self.performance_stats["parse_count"]
        )

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get parser performance statistics."""
        return self.performance_stats.copy()


# Global parser instance
_parser = Shadowsocks2022Parser()


async def parse_ss2022_async(uri: str) -> Optional[VPNConfiguration]:
    """Parse Shadowsocks 2022 URI using high-performance parser.

    Args:
        uri: SS2022 URI string

    Returns:
        VPNConfiguration object or None if parsing fails
    """
    return await _parser.parse(uri)


def get_ss2022_parser_stats() -> Dict[str, Any]:
    """Get SS2022 parser performance statistics."""
    return _parser.get_performance_stats()
