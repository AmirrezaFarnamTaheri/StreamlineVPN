"""
Optimized VLESS Parser
=====================

High-performance VLESS protocol parser with async patterns and
zero-copy parsing.
"""

import re
from typing import Dict, Optional, Any
from urllib.parse import parse_qs

from ....models.configuration import VPNConfiguration, Protocol
from ....utils.logging import get_logger

logger = get_logger(__name__)


class VLESSParser:
    """High-performance VLESS parser with async patterns and zero-copy
    parsing."""

    def __init__(self):
        """Initialize VLESS parser."""
        self.vless_pattern = re.compile(
            r"^vless://([^@]+)@([^:]+):(\d+)(\?.*)?$", re.IGNORECASE
        )
        self.performance_stats = {
            "parse_count": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
        }

    async def parse(self, uri: str) -> Optional[VPNConfiguration]:
        """Parse VLESS URI with optimized performance.

        Args:
            uri: VLESS URI string

        Returns:
            VPNConfiguration object or None if parsing fails
        """
        import time

        start_time = time.perf_counter()

        try:
            # Fast regex match
            match = self.vless_pattern.match(uri.strip())
            if not match:
                return None

            # Extract components
            uuid, host, port, query_string = match.groups()

            # Parse query parameters
            params = {}
            if query_string:
                query_part = query_string[1:]  # Remove '?'
                if '#' in query_part:
                    query_part = query_part.split('#', 1)[0]
                query_params = parse_qs(query_part)
                params = {k: v[0] for k, v in query_params.items()}

            # Validate and normalize port
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                logger.error(f"Invalid VLESS port: {port_int}")
                return None

            # Determine TLS usage and security details
            security = params.get("security", "tls").lower()

            # Create configuration
            config = VPNConfiguration(
                protocol=Protocol.VLESS,
                server=host,
                port=port_int,
                user_id=uuid,
                network=params.get("type", "tcp"),
                host=params.get("host", host),
                path=params.get("path", ""),
                tls=security == "tls",
                metadata={
                    "parser": "optimized_vless",
                    "version": "1.0",
                    "performance_optimized": True,
                    "security": security,
                    "sni": params.get("sni", host),
                    "alpn": params.get("alpn", ""),
                    "fingerprint": params.get("fp", ""),
                    "public_key": params.get("pbk", ""),
                    "short_id": params.get("sid", ""),
                    "spider_x": params.get("spx", ""),
                },
            )

            # Preserve original UUID for compatibility
            config.uuid = uuid
            config.security = security

            # Update performance stats
            parse_time = time.perf_counter() - start_time
            self._update_performance_stats(parse_time)

            logger.debug(f"VLESS config parsed in {parse_time*1000:.2f}ms")
            return config

        except Exception as e:
            logger.error(f"Failed to parse VLESS URI: {e}")
            return None

    def _update_performance_stats(self, parse_time: float) -> None:
        """Update performance statistics."""
        self.performance_stats["parse_count"] += 1
        self.performance_stats["total_time"] += parse_time
        total_time = self.performance_stats["total_time"]
        parse_count = self.performance_stats["parse_count"]
        self.performance_stats["avg_time"] = total_time / parse_count

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get parser performance statistics."""
        return self.performance_stats.copy()


# Global parser instance
_parser = VLESSParser()


async def parse_vless_async(uri: str) -> Optional[VPNConfiguration]:
    """Parse VLESS URI using high-performance parser.

    Args:
        uri: VLESS URI string

    Returns:
        VPNConfiguration object or None if parsing fails
    """
    return await _parser.parse(uri)


def get_vless_parser_stats() -> Dict[str, Any]:
    """Get VLESS parser performance statistics."""
    return _parser.get_performance_stats()
