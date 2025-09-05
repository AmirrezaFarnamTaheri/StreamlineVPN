"""
Security Manager
================

Security management system for StreamlineVPN.
"""

import re
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta

from .threat_analyzer import ThreatAnalyzer
from .validator import SecurityValidator
from .manager_utils import find_suspicious_patterns, analyze_urls_in_text, analyze_domain_info
from ..utils.logging import get_logger

logger = get_logger(__name__)

class SecurityManager:
    """Security management system."""
    
    def __init__(self):
        """Initialize security manager."""
        self.threat_analyzer = ThreatAnalyzer()
        self.validator = SecurityValidator()
        self.blocked_ips: Set[str] = set()
        self.blocked_domains: Set[str] = set()
        self.suspicious_patterns: List[str] = [
            r'<script',
            r'javascript:',
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__',
            r'subprocess',
            r'os\.system',
            r'rm\s+-rf',
            r'wget\s+',
            r'curl\s+',
            r'nc\s+',
            r'netcat',
            r'bash\s+',
            r'sh\s+',
            r'powershell',
            r'cmd\s+',
            r'ftp\s+',
            r'telnet\s+',
            r'ssh\s+',
            r'scp\s+',
            r'rsync\s+'
        ]
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.max_requests_per_minute = 60
    
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
            suspicious_patterns = self._check_suspicious_patterns(config)
            
            # URL validation
            url_analysis = self._analyze_urls(config)
            
            # Overall risk score
            risk_score = self._calculate_risk_score(threats, suspicious_patterns, url_analysis)
            
            return {
                "threats": threats,
                "suspicious_patterns": suspicious_patterns,
                "url_analysis": url_analysis,
                "risk_score": risk_score,
                "is_safe": risk_score < 0.5,
                "timestamp": datetime.now().isoformat()
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
                "timestamp": datetime.now().isoformat()
            }
    
    def validate_source(self, source_url: str) -> Dict[str, Any]:
        """Validate source URL for security.
        
        Args:
            source_url: Source URL to validate
            
        Returns:
            Validation results
        """
        try:
            # Basic URL validation
            is_valid_url = self.validator.validate_url(source_url)
            
            # Check if blocked
            is_blocked = self._is_blocked(source_url)
            
            # Check rate limiting
            is_rate_limited = self._check_rate_limit(source_url)
            
            # Domain analysis
            domain_analysis = self._analyze_domain(source_url)
            
            # Overall validation
            is_safe = is_valid_url and not is_blocked and not is_rate_limited and domain_analysis.get("is_safe", True)
            
            return {
                "is_valid_url": is_valid_url,
                "is_blocked": is_blocked,
                "is_rate_limited": is_rate_limited,
                "domain_analysis": domain_analysis,
                "is_safe": is_safe,
                "timestamp": datetime.now().isoformat()
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
                "timestamp": datetime.now().isoformat()
            }
    
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
    
    def get_security_statistics(self) -> Dict[str, Any]:
        """Get security statistics.
        
        Returns:
            Security statistics
        """
        return {
            "blocked_ips": len(self.blocked_ips),
            "blocked_domains": len(self.blocked_domains),
            "suspicious_patterns": len(self.suspicious_patterns),
            "rate_limits": len(self.rate_limits),
            "max_requests_per_minute": self.max_requests_per_minute
        }
    
    def _check_suspicious_patterns(self, config: str) -> List[str]:
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
    
    def _analyze_urls(self, config: str) -> Dict[str, Any]:
        """Analyze URLs in configuration.
        
        Args:
            config: Configuration string
            
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
            "valid_urls": []
        }
        
        for url in urls:
            if self._is_blocked(url):
                analysis["blocked_urls"].append(url)
            elif not self.validator.validate_url(url):
                analysis["suspicious_urls"].append(url)
            else:
                analysis["valid_urls"].append(url)
        
        return analysis
    
    def _analyze_domain(self, url: str) -> Dict[str, Any]:
        """Analyze domain for security.
        
        Args:
            url: URL to analyze
            
        Returns:
            Domain analysis results
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.hostname or ""
            
            # Check if domain is blocked
            is_blocked = any(blocked in domain for blocked in self.blocked_domains)
            
            # Check for suspicious TLDs
            suspicious_tlds = ['.tk', '.ml', '.ga', '.cf']
            has_suspicious_tld = any(domain.endswith(tld) for tld in suspicious_tlds)
            
            # Check for IP addresses
            is_ip = re.match(r'^\d+\.\d+\.\d+\.\d+$', domain)
            
            return {
                "domain": domain,
                "is_blocked": is_blocked,
                "has_suspicious_tld": has_suspicious_tld,
                "is_ip": bool(is_ip),
                "is_safe": not is_blocked and not has_suspicious_tld
            }
            
        except Exception as e:
            logger.error(f"Domain analysis error: {e}")
            return {
                "domain": "",
                "is_blocked": True,
                "has_suspicious_tld": False,
                "is_ip": False,
                "is_safe": False,
                "error": str(e)
            }
    
    def _is_blocked(self, url: str) -> bool:
        """Check if URL is blocked.
        
        Args:
            url: URL to check
            
        Returns:
            True if blocked, False otherwise
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.hostname or ""
            
            # Check blocked domains
            if any(blocked in domain for blocked in self.blocked_domains):
                return True
            
            # Check blocked IPs
            if domain in self.blocked_ips:
                return True
            
            return False
            
        except Exception:
            return True  # Block if we can't parse the URL
    
    def _check_rate_limit(self, source_url: str) -> bool:
        """Check if source is rate limited.
        
        Args:
            source_url: Source URL to check
            
        Returns:
            True if rate limited, False otherwise
        """
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old entries
        if source_url in self.rate_limits:
            self.rate_limits[source_url] = [
                timestamp for timestamp in self.rate_limits[source_url]
                if timestamp > minute_ago
            ]
        else:
            self.rate_limits[source_url] = []
        
        # Check rate limit
        if len(self.rate_limits[source_url]) >= self.max_requests_per_minute:
            return True
        
        # Add current request
        self.rate_limits[source_url].append(now)
        return False
    
    def _calculate_risk_score(
        self, 
        threats: List[Dict], 
        suspicious_patterns: List[str], 
        url_analysis: Dict[str, Any]
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

    # Thin wrappers delegating to submodules for readability
    def _check_suspicious_patterns(self, text: str) -> List[str]:
        return find_suspicious_patterns(text, self.suspicious_patterns)

    def _analyze_urls(self, text: str) -> Dict[str, List[str]]:
        return analyze_urls_in_text(text, self.blocked_domains, self.validator)

    def _analyze_domain(self, url: str) -> Dict[str, Any]:
        return analyze_domain_info(url, self.blocked_domains)
