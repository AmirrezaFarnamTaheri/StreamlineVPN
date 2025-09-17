"""
Security Validator
==================

Security validation utilities for StreamlineVPN.
"""

import concurrent.futures
import ipaddress
import re
import socket
from typing import Any, Dict
from urllib.parse import urlparse

from ..settings import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SecurityValidator:
    """Security validation utilities."""

    def __init__(self):
        """Initialize security validator."""
        settings = get_settings()
        s = settings.security
        self.safe_ports = s.safe_ports
        self.safe_protocols = s.safe_protocols
        self.safe_encryptions = s.safe_encryptions
        self.initialized = True
        self.is_initialized = True  # Added for test compatibility
        self.validation_rules: Dict[str, Any] = {}  # Added for test compatibility
        self.security_checks: Dict[str, Any] = {}  # Added for test compatibility

    # Convenience methods expected by tests
    def validate_ip_address(self, ip: str) -> bool:
        return self._is_valid_ip(ip)

    def validate_domain(self, domain: str) -> bool:
        return self._is_valid_domain(domain)

    def validate_uuid(self, value: str) -> bool:
        try:
            import uuid as _uuid

            _uuid.UUID(str(value))
            return True
        except Exception:
            return False

    def run_security_checks(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run security checks and return results with checks_passed field."""
        results = self.validate_configuration(config)
        results["checks_passed"] = results["is_valid"]
        results["checks_failed"] = not results[
            "is_valid"
        ]  # Added for test compatibility
        results["overall_score"] = results[
            "security_score"
        ]  # Added for test compatibility
        return results

    def validate_url(self, url: str) -> bool:
        """Validate URL for security.

        Args:
            url: URL to validate

        Returns:
            True if URL is safe, False otherwise
        """
        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in ["http", "https"]:
                return False

            # Check hostname
            if not parsed.hostname:
                return False

            # Check for suspicious patterns
            if self._has_suspicious_patterns(url):
                return False

            # Check for valid IP address
            if self._is_valid_ip(parsed.hostname):
                return True

            # Check for valid domain
            if self._is_valid_domain(parsed.hostname):
                return True

            return False

        except Exception as e:
            logger.debug("URL validation error: %s", e)
            return False

    def validate_port(self, port: int) -> bool:
        """Validate port for security.

        Args:
            port: Port number to validate

        Returns:
            True if port is safe, False otherwise
        """
        try:
            # Check if port is in valid range
            if not (1 <= port <= 65535):
                return False

            # Check if port is in safe ports list
            if port in self.safe_ports:
                return True

            # Check if port is in common VPN ranges
            if 1000 <= port <= 65535:
                return True

            return False

        except Exception:
            return False

    def validate_protocol(self, protocol: str) -> bool:
        """Validate protocol for security.

        Args:
            protocol: Protocol to validate

        Returns:
            True if protocol is safe, False otherwise
        """
        return protocol.lower() in self.safe_protocols

    def validate_encryption(self, encryption: str) -> bool:
        """Validate encryption method for security.

        Args:
            encryption: Encryption method to validate

        Returns:
            True if encryption is safe, False otherwise
        """
        return encryption.lower() in self.safe_encryptions

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate VPN configuration for security.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Validation results
        """
        results = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "security_score": 1.0,
        }

        try:
            # Validate server
            if "server" in config:
                if not self._is_valid_server(config["server"]):
                    results["errors"].append("Invalid server address")
                    results["is_valid"] = False

            # Validate port
            if "port" in config:
                if not self.validate_port(config["port"]):
                    results["errors"].append(
                        f"Invalid or unsafe port: {config['port']}"
                    )
                    results["is_valid"] = False
                else:
                    if config["port"] not in self.safe_ports:
                        results["warnings"].append(
                            f"Port {config['port']} may not be optimal"
                        )
                        results["security_score"] -= 0.1

            # Validate protocol
            if "protocol" in config:
                if not self.validate_protocol(config["protocol"]):
                    results["errors"].append(f"Unsafe protocol: {config['protocol']}")
                    results["is_valid"] = False

            # Validate encryption
            if "encryption" in config:
                if not self.validate_encryption(config["encryption"]):
                    results["warnings"].append(
                        "Encryption method may not be secure: "
                        f"{config['encryption']}"
                    )
                    results["security_score"] -= 0.2

            # Validate TLS
            if config.get("tls", False):
                results["security_score"] += 0.1

            # Check for suspicious fields
            suspicious_fields = ["script", "command", "exec", "eval"]
            for field in suspicious_fields:
                if field in config:
                    results["errors"].append(f"Suspicious field detected: {field}")
                    results["is_valid"] = False

            # Ensure security score is between 0 and 1
            results["security_score"] = max(0.0, min(1.0, results["security_score"]))

        except Exception as e:
            results["errors"].append(f"Validation error: {e}")
            results["is_valid"] = False

        return results

    def _has_suspicious_patterns(self, url: str) -> bool:
        """Check for suspicious patterns in URL.

        Args:
            url: URL to check

        Returns:
            True if suspicious patterns found, False otherwise
        """
        suspicious_patterns = [
            r"<script",
            r"javascript:",
            r"vbscript:",
            r"data:",
            r"file:",
            r"ftp:",
            r"telnet:",
            r"ssh:",
            r"rm\s+-rf",
            r"del\s+/s",
            r"format\s+",
            r"eval\s*\(",
            r"exec\s*\(",
            r"__import__",
            r"subprocess",
            r"os\.system",
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True

        return False

    def _is_valid_ip(self, hostname: str) -> bool:
        """Check if hostname is a valid IP address.

        Args:
            hostname: Hostname to check

        Returns:
            True if valid IP, False otherwise
        """
        try:
            ipaddress.ip_address(hostname)
            return True
        except ValueError:
            return False

    def _is_valid_domain(self, hostname: str) -> bool:
        """Check if hostname is a valid domain."""
        if not hostname:
            return False
        host = hostname.strip().lower()
        # Allow localhost and local domains
        if host in ["localhost", "127.0.0.1", "::1"]:
            return True
        if "." not in host:
            return False

        domain_pattern = (
            r"^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?"
            r"(\.[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?)+$"
        )
        if not re.match(domain_pattern, host):
            return False

        settings = get_settings()
        if any(host.endswith(tld) for tld in settings.security.suspicious_tlds):
            return False

        # Best-effort DNS: if resolution fails or times out, treat syntactically
        # valid domains as acceptable (avoid hard network dependency in validation).
        exe = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            future = exe.submit(socket.getaddrinfo, host, None)
            infos = future.result(timeout=2)
        except concurrent.futures.TimeoutError:
            # Timeout: avoid blocking; consider domain acceptable
            exe.shutdown(wait=False, cancel_futures=True)
            return True
        except Exception:
            # DNS resolution failed: consider domain acceptable (syntactic check passed)
            exe.shutdown(wait=True)
            return True
        else:
            exe.shutdown(wait=True)
            any_public = False
            for _, _, _, _, sockaddr in infos:
                ip = sockaddr[0]
                ip_obj = ipaddress.ip_address(ip)
                if (
                    ip_obj.is_private
                    or ip_obj.is_loopback
                    or ip_obj.is_link_local
                    or ip_obj.is_reserved
                    or ip_obj.is_multicast
                    or ip_obj.is_unspecified
                ):
                    continue
                any_public = True
            return any_public

    def _is_valid_server(self, server: str) -> bool:
        """Check if server address is valid.

        Args:
            server: Server address to check

        Returns:
            True if valid server, False otherwise
        """
        # Check if it's a valid IP
        if self._is_valid_ip(server):
            return True

        # Check if it's a valid domain
        if self._is_valid_domain(server):
            return True

        return False

    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics.

        Returns:
            Validation statistics
        """
        return {
            "safe_ports": len(self.safe_ports),
            "safe_protocols": len(self.safe_protocols),
            "safe_encryptions": len(self.safe_encryptions),
        }
