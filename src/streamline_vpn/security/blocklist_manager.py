"""
Blocklist Manager
=================

Blocklist management functionality for security.
"""

from typing import Set, Dict, Any

from ...utils.logging import get_logger

logger = get_logger(__name__)


class BlocklistManager:
    """Blocklist manager for IPs and domains."""

    def __init__(self):
        """Initialize blocklist manager."""
        self.blocked_ips: Set[str] = set()
        self.blocked_domains: Set[str] = set()

    def block_ip(self, ip: str, reason: str = "") -> None:
        """Block an IP address.

        Args:
            ip: IP address to block
            reason: Reason for blocking
        """
        self.blocked_ips.add(ip)
        logger.warning(f"Blocked IP {ip}: {reason}")

    def block_domain(self, domain: str, reason: str = "") -> None:
        """Block a domain.

        Args:
            domain: Domain to block
            reason: Reason for blocking
        """
        self.blocked_domains.add(domain)
        logger.warning(f"Blocked domain {domain}: {reason}")

    def unblock_ip(self, ip: str) -> None:
        """Unblock an IP address.

        Args:
            ip: IP address to unblock
        """
        self.blocked_ips.discard(ip)
        logger.info(f"Unblocked IP {ip}")

    def unblock_domain(self, domain: str) -> None:
        """Unblock a domain.

        Args:
            domain: Domain to unblock
        """
        self.blocked_domains.discard(domain)
        logger.info(f"Unblocked domain {domain}")

    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked.

        Args:
            ip: IP address to check

        Returns:
            True if blocked, False otherwise
        """
        return ip in self.blocked_ips

    def is_domain_blocked(self, domain: str) -> bool:
        """Check if domain is blocked.

        Args:
            domain: Domain to check

        Returns:
            True if blocked, False otherwise
        """
        return any(blocked in domain for blocked in self.blocked_domains)

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

    def clear_blocklists(self) -> None:
        """Clear all blocklists."""
        self.blocked_ips.clear()
        self.blocked_domains.clear()
        logger.info("All blocklists cleared")
