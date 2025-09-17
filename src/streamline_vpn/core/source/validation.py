"""
Source validation and content parsing.
"""

import base64
import re
from typing import List, Optional

from ...utils.logging import get_logger

logger = get_logger(__name__)


class SourceValidation:
    """Validates source content and parses configurations."""

    def __init__(self):
        self.config_patterns = [
            r"^[A-Za-z0-9+/]+=*$",  # Base64 pattern
            r"^vmess://",  # VMess URL
            r"^vless://",  # VLess URL
            r"^ss://",  # Shadowsocks URL
            r"^ssr://",  # ShadowsocksR URL
            r"^trojan://",  # Trojan URL
            r"^hy2://",  # Hysteria2 URL
            r"^hysteria://",  # Hysteria URL
        ]

    def parse_configs(self, content: str) -> List[str]:
        """Parse configuration content and extract valid configs."""
        if not content or not content.strip():
            return []

        lines = content.strip().split("\n")
        valid_configs = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Check if line looks like a config
            if self._is_valid_config_line(line):
                valid_configs.append(line)

        logger.debug("Parsed %d valid configs from content", len(valid_configs))
        return valid_configs

    def _is_valid_config_line(self, line: str) -> bool:
        """Check if a line looks like a valid configuration."""
        if not line or len(line) < 10:
            return False

        # Check for URL patterns
        for pattern in self.config_patterns:
            if re.match(pattern, line):
                return True

        # Check for base64 content
        if self._looks_like_b64(line):
            try:
                decoded = self._try_b64_decode(line)
                if decoded and self._is_valid_config_line(decoded):
                    return True
            except Exception:
                pass

        # Check for JSON-like content
        if line.startswith("{") and line.endswith("}"):
            try:
                import json

                data = json.loads(line)
                if isinstance(data, dict) and any(
                    key in data
                    for key in ["server", "port", "protocol", "type", "ps", "name"]
                ):
                    return True
            except Exception:
                pass

        return False

    def _looks_like_b64(self, s: str) -> bool:
        """Check if string looks like base64."""
        if not s or len(s) < 4:
            return False

        # Check for base64 character set
        if not re.match(r"^[A-Za-z0-9+/=]+$", s):
            return False

        # Check length is multiple of 4
        if len(s) % 4 != 0:
            return False

        # Check for reasonable length
        if len(s) < 20 or len(s) > 10000:
            return False

        return True

    def _pad_b64(self, s: str) -> str:
        """Pad base64 string to proper length."""
        missing_padding = len(s) % 4
        if missing_padding:
            s += "=" * (4 - missing_padding)
        return s

    def _try_b64_decode(self, s: str) -> Optional[str]:
        """Try to decode base64 string."""
        try:
            # Pad if necessary
            padded = self._pad_b64(s)

            # Decode
            decoded = base64.b64decode(padded).decode("utf-8")

            # Check if decoded content looks like a config
            if len(decoded) > 10 and any(
                keyword in decoded.lower()
                for keyword in [
                    "server",
                    "port",
                    "protocol",
                    "vmess",
                    "vless",
                    "shadowsocks",
                ]
            ):
                return decoded

        except Exception as e:
            logger.debug("Base64 decode failed: %s", e)

        return None

    def validate_source_url(self, url: str) -> bool:
        """Validate source URL format.

        Relaxed to support test domains like new.test-server.example
        by relying on urllib.parse.
        """
        if not url or not isinstance(url, str):
            return False
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"}:
                return False
            return bool(parsed.netloc)
        except Exception:
            return False

    def validate_source_config(self, config: dict) -> tuple[bool, List[str]]:
        """Validate source configuration."""
        errors = []

        # Required fields: url (name optional for URL API)
        if "url" not in config or not config["url"]:
            errors.append("Missing required field: url")
        if "name" in config and not config["name"]:
            errors.append("Missing required field: name")

        # Validate URL
        if "url" in config and not self.validate_source_url(config["url"]):
            errors.append("Invalid URL format")

        # Validate type when provided
        if (
            "type" in config
            and config["type"]
            and config["type"] not in ["http", "https", "file", "subscription"]
        ):
            errors.append("Invalid source type")

        # Validate numeric fields
        numeric_fields = ["priority", "refresh_interval", "timeout", "retry_attempts"]
        for field in numeric_fields:
            if field in config:
                try:
                    value = int(config[field])
                    if value < 0:
                        errors.append(f"{field} must be non-negative")
                except (ValueError, TypeError):
                    errors.append(f"{field} must be a valid integer")

        return len(errors) == 0, errors
