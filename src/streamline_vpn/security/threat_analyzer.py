"""
Threat Analyzer
===============

Threat analysis system for VPN configurations.
"""

import base64
import re
from datetime import datetime
from typing import Any, Dict, List

from ...utils.logging import get_logger

logger = get_logger(__name__)


class ThreatAnalyzer:
    """Threat analysis system."""

    def __init__(self):
        """Initialize threat analyzer."""
        self.malicious_patterns = [
            # Script injection patterns
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"data:text/html",
            r"data:application/javascript",
            # Command injection patterns
            r";\s*(rm|del|format|fdisk)",
            r"\|\s*(rm|del|format|fdisk)",
            r"&&\s*(rm|del|format|fdisk)",
            r"\|\|\s*(rm|del|format|fdisk)",
            # Code execution patterns
            r"eval\s*\(",
            r"exec\s*\(",
            r"__import__\s*\(",
            r"subprocess\s*\.",
            r"os\.system\s*\(",
            r"os\.popen\s*\(",
            # Network attack patterns
            r"nc\s+",
            r"netcat\s+",
            r"nmap\s+",
            r"wget\s+.*-O\s+",
            r"curl\s+.*-o\s+",
            r"ftp\s+",
            r"telnet\s+",
            r"ssh\s+.*-o\s+",
            # File system attack patterns
            r"rm\s+-rf",
            r"del\s+/s",
            r"format\s+",
            r"fdisk\s+",
            r"mkfs\s+",
            r"dd\s+if=",
            # PowerShell attack patterns
            r"powershell\s+",
            r"cmd\s+/c",
            r"cmd\s+/k",
            # SQL injection patterns
            r"union\s+select",
            r"drop\s+table",
            r"delete\s+from",
            r"insert\s+into",
            r"update\s+.*set",
            # XSS patterns
            r"on\w+\s*=",
            r"<iframe",
            r"<object",
            r"<embed",
            r"<form",
            # Path traversal patterns
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e%5c",
        ]

        self.suspicious_domains = [
            "malware.com",
            "virus.com",
            "phishing.com",
            "suspicious.com",
            "malicious.com",
        ]

        self.suspicious_ports = [
            22,  # SSH
            23,  # Telnet
            21,  # FTP
            25,  # SMTP
            53,  # DNS
            80,  # HTTP (can be suspicious in VPN configs)
            443,  # HTTPS (can be suspicious in VPN configs)
            3389,  # RDP
            5900,  # VNC
            8080,  # Alternative HTTP
            8443,  # Alternative HTTPS
        ]

    def analyze(self, config: str) -> List[Dict[str, Any]]:
        """Analyze configuration for threats.

        Args:
            config: Configuration string to analyze

        Returns:
            List of detected threats
        """
        threats = []

        try:
            # Check for malicious patterns
            pattern_threats = self._check_malicious_patterns(config)
            threats.extend(pattern_threats)

            # Check for suspicious URLs
            url_threats = self._check_suspicious_urls(config)
            threats.extend(url_threats)

            # Check for suspicious ports
            port_threats = self._check_suspicious_ports(config)
            threats.extend(port_threats)

            # Check for encoded content
            encoded_threats = self._check_encoded_content(config)
            threats.extend(encoded_threats)

            # Check for suspicious protocols
            protocol_threats = self._check_suspicious_protocols(config)
            threats.extend(protocol_threats)

        except Exception as e:
            logger.error(f"Threat analysis error: {e}")
            threats.append(
                {
                    "type": "analysis_error",
                    "severity": "high",
                    "description": f"Error during threat analysis: {e}",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return threats

    def _check_malicious_patterns(
        self, config: str
    ) -> List[Dict[str, Any]]:
        """Check for malicious patterns.

        Args:
            config: Configuration string

        Returns:
            List of detected pattern threats
        """
        threats = []

        for pattern in self.malicious_patterns:
            matches = re.finditer(
                pattern, config, re.IGNORECASE | re.MULTILINE
            )
            for match in matches:
                threats.append(
                    {
                        "type": "malicious_pattern",
                        "severity": "high",
                        "pattern": pattern,
                        "match": match.group(),
                        "position": match.start(),
                        "description": "Malicious pattern detected: "
                        f"{pattern}",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return threats

    def _check_suspicious_urls(self, config: str) -> List[Dict[str, Any]]:
        """Check for suspicious URLs.

        Args:
            config: Configuration string

        Returns:
            List of detected URL threats
        """
        threats = []

        # Extract URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, config)

        for url in urls:
            # Check for suspicious domains
            for suspicious_domain in self.suspicious_domains:
                if suspicious_domain in url.lower():
                    threats.append(
                        {
                            "type": "suspicious_url",
                            "severity": "high",
                            "url": url,
                            "reason": "Suspicious domain: "
                            f"{suspicious_domain}",
                            "description": "Suspicious URL detected: "
                            f"{url}",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

            # Check for suspicious TLDs
            suspicious_tlds = [".tk", ".ml", ".ga", ".cf", ".pw"]
            for tld in suspicious_tlds:
                if url.lower().endswith(tld):
                    threats.append(
                        {
                            "type": "suspicious_tld",
                            "severity": "medium",
                            "url": url,
                            "reason": f"Suspicious TLD: {tld}",
                            "description": "URL with suspicious TLD: "
                            f"{url}",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        return threats

    def _check_suspicious_ports(self, config: str) -> List[Dict[str, Any]]:
        """Check for suspicious ports.

        Args:
            config: Configuration string

        Returns:
            List of detected port threats
        """
        threats = []

        # Extract port numbers
        port_pattern = r":(\d{1,5})(?:\s|$|,|;|\)|]|})"
        ports = re.findall(port_pattern, config)

        for port_str in ports:
            try:
                port = int(port_str)
                if port in self.suspicious_ports:
                    threats.append(
                        {
                            "type": "suspicious_port",
                            "severity": "medium",
                            "port": port,
                            "reason": f"Suspicious port: {port}",
                            "description": "Suspicious port detected: "
                            f"{port}",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
            except ValueError:
                continue

        return threats

    def _check_encoded_content(self, config: str) -> List[Dict[str, Any]]:
        """Check for encoded content that might hide threats.

        Args:
            config: Configuration string

        Returns:
            List of detected encoding threats
        """
        threats = []

        # Check for base64 encoded content
        base64_pattern = r"[A-Za-z0-9+/]{20,}={0,2}"
        base64_matches = re.findall(base64_pattern, config)

        for match in base64_matches:
            try:
                # Decode and check for threats
                decoded = base64.b64decode(match).decode(
                    "utf-8", errors="ignore"
                )
                decoded_threats = self._check_malicious_patterns(decoded)

                if decoded_threats:
                    threats.append(
                        {
                            "type": "encoded_threat",
                            "severity": "high",
                            "encoding": "base64",
                            "original": match,
                            "decoded": decoded,
                            "threats": decoded_threats,
                            "description": (
                                "Encoded threat detected in base64 content"
                            ),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
            except Exception:
                continue

        # Check for URL encoded content
        url_encoded_pattern = r"%[0-9A-Fa-f]{2}"
        if re.search(url_encoded_pattern, config):
            threats.append(
                {
                    "type": "url_encoded_content",
                    "severity": "low",
                    "description": "URL encoded content detected",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return threats

    def _check_suspicious_protocols(
        self, config: str
    ) -> List[Dict[str, Any]]:
        """Check for suspicious protocols.

        Args:
            config: Configuration string

        Returns:
            List of detected protocol threats
        """
        threats = []

        # Check for suspicious protocol schemes
        suspicious_schemes = [
            "ftp://",
            "telnet://",
            "ssh://",
            "file://",
            "data:",
        ]

        for scheme in suspicious_schemes:
            if scheme in config.lower():
                threats.append(
                    {
                        "type": "suspicious_protocol",
                        "severity": "medium",
                        "scheme": scheme,
                        "description": f"Suspicious protocol scheme: {scheme}",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return threats

    def get_threat_statistics(self) -> Dict[str, Any]:
        """Get threat analysis statistics.

        Returns:
            Threat analysis statistics
        """
        return {
            "malicious_patterns": len(self.malicious_patterns),
            "suspicious_domains": len(self.suspicious_domains),
            "suspicious_ports": len(self.suspicious_ports),
            "total_patterns": (
                len(self.malicious_patterns)
                + len(self.suspicious_domains)
                + len(self.suspicious_ports)
            ),
        }
