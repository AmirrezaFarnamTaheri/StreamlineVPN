"""
Pattern Analyzer
================

Security pattern analysis and detection functionality.
"""

import re
from typing import Dict, List, Any
from datetime import datetime

from ..utils.logging import get_logger

logger = get_logger(__name__)


class PatternAnalyzer:
    """Security pattern analyzer for configuration validation."""

    def __init__(self):
        """Initialize pattern analyzer."""
        self.suspicious_patterns = [
            r"<script",
            r"javascript:",
            r"eval\s*\(",
            r"exec\s*\(",
            r"__import__",
            r"subprocess",
            r"os\.system",
            r"rm\s+-rf",
            r"wget\s+",
            r"curl\s+",
            r"nc\s+",
            r"netcat",
            r"bash\s+",
            r"sh\s+",
            r"powershell",
            r"cmd\s+",
            r"ftp\s+",
            r"telnet\s+",
            r"ssh\s+",
            r"scp\s+",
            r"rsync\s+",
        ]

    def check_suspicious_patterns(self, config: str) -> List[str]:
        """Check for suspicious patterns in configuration.

        Args:
            config: Configuration string

        Returns:
            List of matched suspicious patterns
        """
        matched_patterns = []

        for pattern in self.suspicious_patterns:
            if re.search(pattern, config, re.IGNORECASE):
                matched_patterns.append(pattern)

        return matched_patterns

    def analyze_urls(
        self, config: str, blocked_domains: set, validator
    ) -> Dict[str, List[str]]:
        """Analyze URLs in configuration.

        Args:
            config: Configuration string
            blocked_domains: Set of blocked domains
            validator: URL validator instance

        Returns:
            URL analysis results
        """
        # Extract URLs from configuration
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, config)

        analysis = {
            "url_count": len(urls),
            "suspicious_urls": [],
            "blocked_urls": [],
            "valid_urls": [],
        }

        for url in urls:
            if self._is_blocked(url, blocked_domains):
                analysis["blocked_urls"].append(url)
            elif not validator.validate_url(url):
                analysis["suspicious_urls"].append(url)
            else:
                analysis["valid_urls"].append(url)

        return analysis

    def analyze_domain(self, url: str, blocked_domains: set) -> Dict[str, Any]:
        """Analyze domain for security.

        Args:
            url: URL to analyze
            blocked_domains: Set of blocked domains

        Returns:
            Domain analysis results
        """
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.hostname or ""

            # Check if domain is blocked
            is_blocked = any(blocked in domain for blocked in blocked_domains)

            # Check for suspicious TLDs
            suspicious_tlds = [".tk", ".ml", ".ga", ".cf"]
            has_suspicious_tld = any(
                domain.endswith(tld) for tld in suspicious_tlds
            )

            # Check for IP addresses
            is_ip = re.match(r"^\d+\.\d+\.\d+\.\d+$", domain)

            return {
                "domain": domain,
                "is_blocked": is_blocked,
                "has_suspicious_tld": has_suspicious_tld,
                "is_ip": bool(is_ip),
                "is_safe": not is_blocked and not has_suspicious_tld,
            }

        except Exception as e:
            logger.error(f"Domain analysis error: {e}")
            return {
                "domain": "",
                "is_blocked": True,
                "has_suspicious_tld": False,
                "is_ip": False,
                "is_safe": False,
                "error": str(e),
            }

    def _is_blocked(self, url: str, blocked_domains: set) -> bool:
        """Check if URL is blocked.

        Args:
            url: URL to check
            blocked_domains: Set of blocked domains

        Returns:
            True if blocked, False otherwise
        """
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.hostname or ""

            # Check blocked domains
            if any(blocked in domain for blocked in blocked_domains):
                return True

            return False

        except Exception:
            return True  # Block if we can't parse the URL
