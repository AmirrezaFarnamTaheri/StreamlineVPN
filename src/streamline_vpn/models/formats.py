"""
Output Format Models
====================

Defines output format enums and related models.
"""

from enum import Enum


class OutputFormat(Enum):
    """Supported output formats for VPN configurations."""

    RAW = "raw"
    JSON = "json"
    BASE64 = "base64"
    CSV = "csv"
    YAML = "yaml"
    CLASH = "clash"
    SINGBOX = "singbox"

    @classmethod
    def values(cls):
        """Get all format values."""
        return [f.value for f in cls]

    @classmethod
    def is_valid(cls, format_str: str) -> bool:
        """Check if format string is valid."""
        return format_str.lower() in cls.values()
