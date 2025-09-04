"""
SSL Certificate Analysis for Source Validation
==============================================

Utilities for analyzing SSL certificates and security aspects of sources.
"""

import ssl
import socket
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from .quality_weights import SSL_SCORING_WEIGHTS


class SSLAnalyzer:
    """Analyzes SSL certificates and security aspects of sources."""
    
    def __init__(self):
        """Initialize the SSL analyzer."""
        self.scoring_weights = SSL_SCORING_WEIGHTS
    
    async def analyze_ssl_certificate(self, url: str) -> Dict[str, Any]:
        """Analyze SSL certificate for a given URL.
        
        Args:
            url: URL to analyze
            
        Returns:
            Dictionary containing SSL analysis results
        """
        parsed_url = urlparse(url)
        if parsed_url.scheme != 'https':
            return {
                "has_ssl": False,
                "ssl_score": 0.0,
                "certificate_info": {},
                "security_issues": ["Not HTTPS"],
            }
        
        try:
            hostname = parsed_url.hostname
            port = parsed_url.port or 443
            
            # Get certificate information
            cert_info = await self._get_certificate_info(hostname, port)
            
            # Calculate SSL score
            ssl_score = self._calculate_ssl_score(cert_info)
            
            return {
                "has_ssl": True,
                "ssl_score": ssl_score,
                "certificate_info": cert_info,
                "security_issues": self._identify_security_issues(cert_info),
            }
            
        except Exception as e:
            return {
                "has_ssl": False,
                "ssl_score": 0.0,
                "certificate_info": {},
                "security_issues": [f"SSL analysis failed: {str(e)}"],
            }
    
    async def _get_certificate_info(self, hostname: str, port: int) -> Dict[str, Any]:
        """Get certificate information for a hostname and port.
        
        Args:
            hostname: Hostname to check
            port: Port number
            
        Returns:
            Dictionary containing certificate information
        """
        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect and get certificate
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    
                    return {
                        "subject": dict(x[0] for x in cert.get('subject', [])),
                        "issuer": dict(x[0] for x in cert.get('issuer', [])),
                        "version": cert.get('version'),
                        "serial_number": cert.get('serialNumber'),
                        "not_before": cert.get('notBefore'),
                        "not_after": cert.get('notAfter'),
                        "cipher": cipher[0] if cipher else None,
                        "cipher_version": cipher[1] if cipher else None,
                        "cipher_bits": cipher[2] if cipher else None,
                    }
                    
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_ssl_score(self, cert_info: Dict[str, Any]) -> float:
        """Calculate SSL security score based on certificate information.
        
        Args:
            cert_info: Certificate information dictionary
            
        Returns:
            SSL security score (0.0 to 1.0)
        """
        if "error" in cert_info:
            return 0.0
        
        score = 0.0
        
        # Check for valid certificate
        if cert_info.get("not_before") and cert_info.get("not_after"):
            score += self.scoring_weights["valid_certificate"]
        
        # Check certificate expiry
        if self._is_certificate_long_term(cert_info):
            score += self.scoring_weights["long_expiry"]
        
        # Check encryption strength
        if self._has_strong_encryption(cert_info):
            score += self.scoring_weights["strong_encryption"]
        
        # Check for trusted CA
        if self._is_trusted_ca(cert_info):
            score += self.scoring_weights["trusted_ca"]
        
        return min(1.0, score)
    
    def _is_certificate_long_term(self, cert_info: Dict[str, Any]) -> bool:
        """Check if certificate has long-term validity.
        
        Args:
            cert_info: Certificate information
            
        Returns:
            True if certificate is valid for more than 30 days
        """
        try:
            not_after = cert_info.get("not_after")
            if not not_after:
                return False
            
            # Parse certificate expiry date
            expiry_date = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
            days_until_expiry = (expiry_date - datetime.now()).days
            
            return days_until_expiry > 30
            
        except Exception:
            return False
    
    def _has_strong_encryption(self, cert_info: Dict[str, Any]) -> bool:
        """Check if certificate uses strong encryption.
        
        Args:
            cert_info: Certificate information
            
        Returns:
            True if encryption is considered strong
        """
        cipher = cert_info.get("cipher", "").lower()
        cipher_bits = cert_info.get("cipher_bits", 0)
        
        # Check for strong cipher suites
        strong_ciphers = [
            "aes", "chacha20", "gcm", "ccm"
        ]
        
        has_strong_cipher = any(strong in cipher for strong in strong_ciphers)
        has_sufficient_bits = cipher_bits >= 128
        
        return has_strong_cipher and has_sufficient_bits
    
    def _is_trusted_ca(self, cert_info: Dict[str, Any]) -> bool:
        """Check if certificate is issued by a trusted CA.
        
        Args:
            cert_info: Certificate information
            
        Returns:
            True if issued by a known trusted CA
        """
        issuer = cert_info.get("issuer", {})
        organization = issuer.get("organizationName", "").lower()
        
        # List of known trusted CAs
        trusted_cas = [
            "digicert", "verisign", "comodo", "symantec", "godaddy",
            "globalsign", "entrust", "thawte", "geotrust", "rapidssl",
            "lets encrypt", "cloudflare", "amazon", "google", "microsoft"
        ]
        
        return any(ca in organization for ca in trusted_cas)
    
    def _identify_security_issues(self, cert_info: Dict[str, Any]) -> list[str]:
        """Identify security issues with the certificate.
        
        Args:
            cert_info: Certificate information
            
        Returns:
            List of security issues
        """
        issues = []
        
        if "error" in cert_info:
            issues.append(f"Certificate error: {cert_info['error']}")
            return issues
        
        # Check for expired certificate
        if not self._is_certificate_long_term(cert_info):
            issues.append("Certificate expires soon or is expired")
        
        # Check for weak encryption
        if not self._has_strong_encryption(cert_info):
            issues.append("Weak encryption detected")
        
        # Check for untrusted CA
        if not self._is_trusted_ca(cert_info):
            issues.append("Certificate not from trusted CA")
        
        # Check for self-signed certificate
        subject = cert_info.get("subject", {})
        issuer = cert_info.get("issuer", {})
        
        if subject == issuer:
            issues.append("Self-signed certificate detected")
        
        return issues