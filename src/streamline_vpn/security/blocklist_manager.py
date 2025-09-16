"""
Blocklist Manager
=================

Blocklist management functionality for security.
"""

from typing import Set, Dict, Any

from ..utils.logging import get_logger

logger = get_logger(__name__)


class BlocklistManager:
    """Blocklist manager for IPs and domains."""

    def __init__(self):
        """Initialize blocklist manager."""
        # store reason mapping as tests expect dict-like access
        self.blocked_ips: Dict[str, str] = {}
        self.blocked_domains: Dict[str, str] = {}
        self.blocked_patterns: Dict[str, str] = {}

    def block_ip(self, ip: str, reason: str = "") -> None:
        """Block an IP address.

        Args:
            ip: IP address to block
            reason: Reason for blocking
        """
        self.blocked_ips[ip] = reason
        logger.warning(f"Blocked IP {ip}: {reason}")

    # Backwards-compat method names expected by tests
    def add_blocked_ip(self, ip: str, reason: str = "") -> None:
        self.block_ip(ip, reason)

    def block_domain(self, domain: str, reason: str = "") -> None:
        """Block a domain.

        Args:
            domain: Domain to block
            reason: Reason for blocking
        """
        self.blocked_domains[domain] = reason
        logger.warning(f"Blocked domain {domain}: {reason}")

    def add_blocked_domain(self, domain: str, reason: str = "") -> None:
        self.block_domain(domain, reason)

    def unblock_ip(self, ip: str) -> None:
        """Unblock an IP address.

        Args:
            ip: IP address to unblock
        """
        self.blocked_ips.pop(ip, None)
        logger.info(f"Unblocked IP {ip}")

    def unblock_domain(self, domain: str) -> None:
        """Unblock a domain.

        Args:
            domain: Domain to unblock
        """
        self.blocked_domains.pop(domain, None)
        logger.info(f"Unblocked domain {domain}")

    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked.

        Args:
            ip: IP address to check

        Returns:
            True if blocked, False otherwise
        """
        return ip in self.blocked_ips.keys()

    def is_domain_blocked(self, domain: str) -> bool:
        """Check if domain is blocked.

        Args:
            domain: Domain to check

        Returns:
            True if blocked, False otherwise
        """
        return any(blocked in domain for blocked in self.blocked_domains.keys())

    def is_pattern_blocked(self, text: str) -> bool:
        """Check if any blocked pattern matches the given text."""
        import fnmatch
        for pattern in self.blocked_patterns.keys():
            if fnmatch.fnmatch(text, pattern):
                return True
        return False

    def get_blocklist_stats(self) -> Dict[str, Any]:
        """Get blocklist statistics.

        Returns:
            Blocklist statistics
        """
        return {
            "blocked_ips": len(self.blocked_ips),
            "blocked_domains": len(self.blocked_domains),
            "total_blocked": len(self.blocked_ips) + len(self.blocked_domains),
        }

    def get_blocked_count(self) -> int:
        return len(self.blocked_ips) + len(self.blocked_domains) + len(self.blocked_patterns)

    def clear_blocklists(self) -> None:
        """Clear all blocklists."""
        self.blocked_ips.clear()
        self.blocked_domains.clear()
        logger.info("All blocklists cleared")

    def clear_all(self) -> None:
        self.blocked_ips.clear()
        self.blocked_domains.clear()
        self.blocked_patterns.clear()
        logger.info("Cleared all blocked items")

    # Additional compat helpers expected by tests
    def remove_blocked_ip(self, ip: str) -> None:
        self.unblock_ip(ip)

    def remove_blocked_domain(self, domain: str) -> None:
        self.unblock_domain(domain)

    def add_blocked_pattern(self, pattern: str, reason: str = "") -> None:
        self.blocked_patterns[pattern] = reason
        logger.warning(f"Blocked pattern {pattern}: {reason}")

    def remove_blocked_pattern(self, pattern: str) -> None:
        self.blocked_patterns.pop(pattern, None)
