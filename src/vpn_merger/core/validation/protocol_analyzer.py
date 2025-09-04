"""
Protocol Analysis for Source Validation
=======================================

Utilities for analyzing VPN protocols in source content.
"""

import base64
import json
import re
from typing import Dict, Set, Tuple

from .quality_weights import VPN_PROTOCOL_PATTERNS


class ProtocolAnalyzer:
    """Analyzes VPN protocols in source content."""
    
    def __init__(self):
        """Initialize the protocol analyzer."""
        self.protocol_patterns = VPN_PROTOCOL_PATTERNS
    
    def analyze_content(self, content: str) -> Tuple[Set[str], Dict[str, bool]]:
        """Analyze content for VPN protocols and quality indicators.
        
        Args:
            content: Content to analyze
            
        Returns:
            Tuple of (protocols_found, quality_indicators)
        """
        protocols_found = self._detect_protocols(content)
        quality_indicators = self._analyze_quality_indicators(content)
        
        return protocols_found, quality_indicators
    
    def _detect_protocols(self, content: str) -> Set[str]:
        """Detect VPN protocols in content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Set of detected protocol names
        """
        protocols_found = set()
        
        # Check for direct protocol patterns
        for protocol, pattern in self.protocol_patterns.items():
            if pattern in content.lower():
                protocols_found.add(protocol)
        
        # Check for base64 encoded protocols
        try:
            decoded_content = self._decode_base64_content(content)
            if decoded_content:
                for protocol, pattern in self.protocol_patterns.items():
                    if pattern in decoded_content.lower():
                        protocols_found.add(protocol)
        except Exception:
            pass
        
        # Check for JSON/YAML configurations
        protocols_found.update(self._detect_config_protocols(content))
        
        return protocols_found
    
    def _decode_base64_content(self, content: str) -> str:
        """Attempt to decode base64 content.
        
        Args:
            content: Content that might be base64 encoded
            
        Returns:
            Decoded content or empty string if decoding fails
        """
        try:
            # Remove whitespace and newlines
            clean_content = re.sub(r'\s+', '', content)
            
            # Try to decode
            decoded = base64.b64decode(clean_content).decode('utf-8')
            return decoded
        except Exception:
            return ""
    
    def _detect_config_protocols(self, content: str) -> Set[str]:
        """Detect protocols in configuration formats.
        
        Args:
            content: Content to analyze
            
        Returns:
            Set of detected protocol names
        """
        protocols_found = set()
        
        try:
            # Try JSON parsing
            if content.strip().startswith('{'):
                config = json.loads(content)
                protocols_found.update(self._extract_protocols_from_config(config))
        except Exception:
            pass
        
        # Check for YAML-like structures
        yaml_protocols = self._detect_yaml_protocols(content)
        protocols_found.update(yaml_protocols)
        
        return protocols_found
    
    def _extract_protocols_from_config(self, config: dict) -> Set[str]:
        """Extract protocols from configuration object.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Set of protocol names
        """
        protocols = set()
        
        # Common configuration keys that might contain protocol info
        protocol_keys = ['protocol', 'type', 'network', 'method']
        
        def search_dict(obj, depth=0):
            if depth > 10:  # Prevent infinite recursion
                return
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.lower() in protocol_keys and isinstance(value, str):
                        for protocol in self.protocol_patterns:
                            if protocol in value.lower():
                                protocols.add(protocol)
                    elif isinstance(value, (dict, list)):
                        search_dict(value, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, (dict, list)):
                        search_dict(item, depth + 1)
        
        search_dict(config)
        return protocols
    
    def _detect_yaml_protocols(self, content: str) -> Set[str]:
        """Detect protocols in YAML-like content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Set of detected protocol names
        """
        protocols = set()
        
        # Look for common YAML patterns
        lines = content.split('\n')
        for line in lines:
            line_lower = line.lower().strip()
            for protocol in self.protocol_patterns:
                if protocol in line_lower:
                    protocols.add(protocol)
        
        return protocols
    
    def _analyze_quality_indicators(self, content: str) -> Dict[str, bool]:
        """Analyze content for quality indicators.
        
        Args:
            content: Content to analyze
            
        Returns:
            Dictionary of quality indicators
        """
        indicators = {
            "base64_encoded": False,
            "json_format": False,
            "yaml_format": False,
            "multiple_protocols": False,
            "server_metadata": False,
            "configuration_completeness": False,
        }
        
        # Check for base64 encoding
        try:
            clean_content = re.sub(r'\s+', '', content)
            if len(clean_content) > 0 and len(clean_content) % 4 == 0:
                base64.b64decode(clean_content)
                indicators["base64_encoded"] = True
        except Exception:
            pass
        
        # Check for JSON format
        try:
            if content.strip().startswith('{') or content.strip().startswith('['):
                json.loads(content)
                indicators["json_format"] = True
        except Exception:
            pass
        
        # Check for YAML format
        if any(line.strip().startswith(('- ', '  -', 'key:', 'value:')) for line in content.split('\n')):
            indicators["yaml_format"] = True
        
        # Check for multiple protocols
        protocols_found = self._detect_protocols(content)
        indicators["multiple_protocols"] = len(protocols_found) > 1
        
        # Check for server metadata
        metadata_indicators = ['server', 'port', 'host', 'address', 'ip']
        indicators["server_metadata"] = any(indicator in content.lower() for indicator in metadata_indicators)
        
        # Check for configuration completeness
        completeness_indicators = ['password', 'uuid', 'key', 'token', 'auth']
        indicators["configuration_completeness"] = any(indicator in content.lower() for indicator in completeness_indicators)
        
        return indicators
    
    def estimate_config_count(self, content: str) -> int:
        """Estimate the number of configurations in content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Estimated number of configurations
        """
        # Count protocol occurrences
        total_configs = 0
        
        for protocol, pattern in self.protocol_patterns.items():
            count = content.lower().count(pattern)
            total_configs += count
        
        # If no direct protocols found, try to estimate from structure
        if total_configs == 0:
            # Look for common separators
            separators = ['\n', '|', ';', ',']
            max_count = 0
            for separator in separators:
                count = content.count(separator)
                max_count = max(max_count, count)
            
            # Estimate based on separators (conservative estimate)
            total_configs = max(1, max_count // 2)
        
        return total_configs
