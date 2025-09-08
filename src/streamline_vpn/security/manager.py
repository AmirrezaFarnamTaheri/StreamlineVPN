"""
Security Manager
================

Security management system for StreamlineVPN.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

# Import moved to avoid circular dependencies
# from .threat_analyzer import ThreatAnalyzer
# from .validator import SecurityValidator
# from .pattern_analyzer import PatternAnalyzer
# from .rate_limiter import RateLimiter
# from .blocklist_manager import BlocklistManager
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SecurityManager:
    """Security management system."""

    def __init__(
        self,
        threat_analyzer=None,
        validator=None,
        pattern_analyzer=None,
        rate_limiter=None,
        blocklist_manager=None,
    ):
        """Initialize security manager."""
        # Lazy imports to avoid circular dependencies
        if threat_analyzer is None:
            from .threat_analyzer import ThreatAnalyzer
            threat_analyzer = ThreatAnalyzer()
        if validator is None:
            from .validator import SecurityValidator
            validator = SecurityValidator()
        if pattern_analyzer is None:
            from .pattern_analyzer import PatternAnalyzer
            pattern_analyzer = PatternAnalyzer()
        if rate_limiter is None:
            from .rate_limiter import RateLimiter
            rate_limiter = RateLimiter()
        if blocklist_manager is None:
            from .blocklist_manager import BlocklistManager
            blocklist_manager = BlocklistManager()
            
        self.threat_analyzer = threat_analyzer
        self.validator = validator
        self.pattern_analyzer = pattern_analyzer
        self.rate_limiter = rate_limiter
        self.blocklist_manager = blocklist_manager

    def analyze_configuration(self, config: str) -> Dict[str, Any]:
        """Analyze configuration for security threats.

        Args:
            config: Configuration string to analyze

        Returns:
            Security analysis results
        """
        try:
            # Treat empty or whitespace-only configs as unsafe
            if not isinstance(config, str) or not config.strip():
                return {
                    "threats": [],
                    "suspicious_patterns": [],
                    "url_analysis": {},
                    "risk_score": 1.0,
                    "is_safe": False,
                    "timestamp": datetime.now().isoformat(),
                }
            # Basic threat analysis
            threats = self.threat_analyzer.analyze(config)

            # Pattern matching
            suspicious_patterns = (
                self.pattern_analyzer.check_suspicious_patterns(config)
            )

            # URL validation
            url_analysis = self.pattern_analyzer.analyze_urls(
                config, self.blocklist_manager.blocked_domains, self.validator
            )

            # Overall risk score
            risk_score = self._calculate_risk_score(
                threats, suspicious_patterns, url_analysis
            )

            return {
                "threats": threats,
                "suspicious_patterns": suspicious_patterns,
                "url_analysis": url_analysis,
                "risk_score": risk_score,
                "is_safe": risk_score < 0.5,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Security analysis error: {e}")
            return {
                "threats": [],
                "suspicious_patterns": [],
                "url_analysis": {},
                "risk_score": 1.0,
                "is_safe": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def validate_source(self, source_url: str) -> Dict[str, Any]:
        """Validate source URL for security.

        Args:
            source_url: Source URL to validate

        Returns:
            Validation results
        """
        try:
            is_valid_url = self.validator.validate_url(source_url)
            is_blocked = self.blocklist_manager.is_domain_blocked(source_url)

            from urllib.parse import urlparse

            host_key = urlparse(source_url).hostname or source_url
            is_rate_limited = self.rate_limiter.check_rate_limit(host_key)

            domain_analysis = self.pattern_analyzer.analyze_domain(
                source_url, self.blocklist_manager.blocked_domains
            )

            is_safe = (
                is_valid_url
                and not is_blocked
                and not is_rate_limited
                and domain_analysis.get("is_safe", True)
            )

            return {
                "is_valid_url": is_valid_url,
                "is_blocked": is_blocked,
                "is_rate_limited": is_rate_limited,
                "domain_analysis": domain_analysis,
                "is_safe": is_safe,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Source validation error: {e}")
            return {
                "is_valid_url": False,
                "is_blocked": True,
                "is_rate_limited": False,
                "domain_analysis": {},
                "is_safe": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def block_ip(self, ip: str, reason: str = "") -> None:
        """Block an IP address.

        Args:
            ip: IP address to block
            reason: Reason for blocking
        """
        self.blocklist_manager.block_ip(ip, reason)

    def block_domain(self, domain: str, reason: str = "") -> None:
        """Block a domain.

        Args:
            domain: Domain to block
            reason: Reason for blocking
        """
        self.blocklist_manager.block_domain(domain, reason)

    def unblock_ip(self, ip: str) -> None:
        """Unblock an IP address.

        Args:
            ip: IP address to unblock
        """
        self.blocklist_manager.unblock_ip(ip)

    def unblock_domain(self, domain: str) -> None:
        """Unblock a domain.

        Args:
            domain: Domain to unblock
        """
        self.blocklist_manager.unblock_domain(domain)

    def get_security_statistics(self) -> Dict[str, Any]:
        """Get security statistics.

        Returns:
            Security statistics
        """
        blocklist_stats = self.blocklist_manager.get_blocklist_stats()
        rate_limit_stats = self.rate_limiter.get_rate_limit_stats()

        return {
            **blocklist_stats,
            "suspicious_patterns": len(
                self.pattern_analyzer.suspicious_patterns
            ),
            **rate_limit_stats,
        }

    def _calculate_risk_score(
        self,
        threats: List[Dict],
        suspicious_patterns: List[str],
        url_analysis: Dict[str, Any],
    ) -> float:
        """Calculate overall risk score.

        Args:
            threats: List of threats
            suspicious_patterns: List of suspicious patterns
            url_analysis: URL analysis results

        Returns:
            Risk score between 0 and 1
        """
        score = 0.0

        # Threats contribute to risk
        score += len(threats) * 0.3

        # Suspicious patterns contribute to risk
        score += len(suspicious_patterns) * 0.2

        # URL analysis contributes to risk
        if url_analysis.get("suspicious_urls"):
            score += len(url_analysis["suspicious_urls"]) * 0.1

        if url_analysis.get("blocked_urls"):
            score += len(url_analysis["blocked_urls"]) * 0.2

        # Cap at 1.0
        return min(score, 1.0)
