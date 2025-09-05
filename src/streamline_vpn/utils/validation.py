"""
Validation Utilities
====================

Validation functions for URLs, configurations, and other data.
"""

import re
import urllib.parse
from typing import Optional, List, Dict, Any
from ..settings import get_settings
from .logging import get_logger
from ..security.validator import SecurityValidator

logger = get_logger(__name__)


# validate_url function moved to security.validator.SecurityValidator
# Use SecurityValidator.validate_url() instead


def validate_config_line(config_line: str) -> bool:
    """Validate VPN configuration line.
    
    Args:
        config_line: Configuration line to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    if not config_line or not isinstance(config_line, str):
        return False
    
    # Remove whitespace
    config_line = config_line.strip()
    
    if not config_line:
        return False
    
    # Check for suspicious content
    suspicious_patterns = [
        r'<script',
        r'</script>',
        r'javascript:',
        r'eval\s*\(',
        r'exec\s*\(',
        r'import\s+os',
        r'__import__',
        r'subprocess',
        r'os\.system',
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, config_line, re.IGNORECASE):
            logger.warning(f"Suspicious config pattern detected: {config_line[:100]}...")
            return False
    
    # Check for valid VPN protocol prefixes
    prefixes = get_settings().supported_protocol_prefixes
    return any(config_line.startswith(protocol) for protocol in prefixes)


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate VPN configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    if not isinstance(config, dict):
        return False
    
    required_fields = ['protocol', 'server', 'port']
    
    # Check required fields
    for field in required_fields:
        if field not in config:
            logger.warning(f"Missing required field: {field}")
            return False
    
    # Validate protocol
    valid_protocols = ['vmess', 'vless', 'trojan', 'ss', 'ssr', 'hysteria', 'hysteria2', 'tuic']
    if config['protocol'] not in valid_protocols:
        logger.warning(f"Invalid protocol: {config['protocol']}")
        return False
    
    # Validate server
    if not config['server'] or not isinstance(config['server'], str):
        logger.warning("Invalid server address")
        return False
    
    # Validate port
    try:
        port = int(config['port'])
        if not (1 <= port <= 65535):
            logger.warning(f"Invalid port: {port}")
            return False
    except (ValueError, TypeError):
        logger.warning(f"Invalid port type: {config['port']}")
        return False
    
    return True


def validate_source_metadata(metadata: Dict[str, Any]) -> bool:
    """Validate source metadata.
    
    Args:
        metadata: Source metadata dictionary
        
    Returns:
        True if metadata is valid, False otherwise
    """
    if not isinstance(metadata, dict):
        return False
    
    # Check required fields
    if 'url' not in metadata:
        return False
    
    # Validate URL
    validator = SecurityValidator()
    if not validator.validate_url(metadata['url']):
        return False
    
    # Validate optional fields
    if 'weight' in metadata:
        try:
            weight = float(metadata['weight'])
            if not (0 <= weight <= 1):
                logger.warning(f"Invalid weight: {weight}")
                return False
        except (ValueError, TypeError):
            logger.warning(f"Invalid weight type: {metadata['weight']}")
            return False
    
    if 'tier' in metadata:
        valid_tiers = ['premium', 'reliable', 'bulk', 'experimental']
        if metadata['tier'] not in valid_tiers:
            logger.warning(f"Invalid tier: {metadata['tier']}")
            return False
    
    return True


def sanitize_string(text: str, max_length: int = 1000) -> str:
    """Sanitize string input.
    
    Args:
        text: Text to sanitize
        max_length: Maximum length allowed
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return ""
    
    # Remove null bytes and control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
        logger.warning(f"Text truncated to {max_length} characters")
    
    return text.strip()


def validate_ip_address(ip: str) -> bool:
    """Validate IP address format.
    
    Args:
        ip: IP address to validate
        
    Returns:
        True if IP is valid, False otherwise
    """
    if not ip or not isinstance(ip, str):
        return False
    
    # IPv4 pattern
    ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    
    # IPv6 pattern (simplified)
    ipv6_pattern = r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
    
    return bool(re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip))


# Backwards-compatibility aliases expected by some tests
def is_valid_ip(ip: str) -> bool:
    return validate_ip_address(ip)


def validate_domain(domain: str) -> bool:
    """Validate domain name format.
    
    Args:
        domain: Domain name to validate
        
    Returns:
        True if domain is valid, False otherwise
    """
    if not domain or not isinstance(domain, str):
        return False
    
    # Domain pattern
    domain_pattern = (
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*'
        r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
    )
    
    return bool(re.match(domain_pattern, domain))


def is_valid_domain(domain: str) -> bool:
    return validate_domain(domain)
