"""
Content Analysis for Source Validation
======================================

Utilities for analyzing content quality and structure of VPN sources.
"""

import json
import re
from typing import Dict, Any, Tuple

from .quality_weights import CONTENT_QUALITY_INDICATORS


class ContentAnalyzer:
    """Analyzes content quality and structure of VPN sources."""
    
    def __init__(self):
        """Initialize the content analyzer."""
        self.quality_indicators = CONTENT_QUALITY_INDICATORS
    
    def analyze_content(self, content: str, content_type: str = "text/plain") -> Dict[str, Any]:
        """Analyze content for quality and structure.
        
        Args:
            content: Content to analyze
            content_type: MIME type of the content
            
        Returns:
            Dictionary containing content analysis results
        """
        analysis = {
            "content_length": len(content),
            "content_type": content_type,
            "quality_score": 0.0,
            "structure_analysis": {},
            "quality_indicators": {},
            "estimated_configs": 0,
            "format_detected": "unknown",
        }
        
        # Detect content format
        format_detected = self._detect_format(content)
        analysis["format_detected"] = format_detected
        
        # Analyze structure
        structure_analysis = self._analyze_structure(content, format_detected)
        analysis["structure_analysis"] = structure_analysis
        
        # Analyze quality indicators
        quality_indicators = self._analyze_quality_indicators(content, format_detected)
        analysis["quality_indicators"] = quality_indicators
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(quality_indicators)
        analysis["quality_score"] = quality_score
        
        # Estimate configuration count
        estimated_configs = self._estimate_config_count(content, format_detected)
        analysis["estimated_configs"] = estimated_configs
        
        return analysis
    
    def _detect_format(self, content: str) -> str:
        """Detect the format of the content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Detected format name
        """
        content = content.strip()
        
        # Check for JSON
        if content.startswith('{') or content.startswith('['):
            try:
                json.loads(content)
                return "json"
            except json.JSONDecodeError:
                pass
        
        # Check for YAML
        if any(line.strip().startswith(('- ', '  -', 'key:', 'value:')) for line in content.split('\n')):
            return "yaml"
        
        # Check for base64
        if self._is_base64_encoded(content):
            return "base64"
        
        # Check for plain text with protocols
        if any(protocol in content.lower() for protocol in ['vmess://', 'vless://', 'trojan://', 'ss://']):
            return "plain_protocols"
        
        # Check for CSV-like format
        if ',' in content and '\n' in content:
            return "csv"
        
        return "plain_text"
    
    def _is_base64_encoded(self, content: str) -> bool:
        """Check if content is base64 encoded.
        
        Args:
            content: Content to check
            
        Returns:
            True if content appears to be base64 encoded
        """
        try:
            import base64
            # Remove whitespace
            clean_content = re.sub(r'\s+', '', content)
            
            # Check if it's valid base64
            if len(clean_content) > 0 and len(clean_content) % 4 == 0:
                base64.b64decode(clean_content)
                return True
        except Exception:
            pass
        
        return False
    
    def _analyze_structure(self, content: str, format_detected: str) -> Dict[str, Any]:
        """Analyze the structure of the content.
        
        Args:
            content: Content to analyze
            format_detected: Detected format
            
        Returns:
            Dictionary containing structure analysis
        """
        structure = {
            "format": format_detected,
            "line_count": len(content.split('\n')),
            "has_headers": False,
            "has_metadata": False,
            "structure_complexity": "simple",
        }
        
        lines = content.split('\n')
        
        # Check for headers
        if format_detected == "json":
            try:
                data = json.loads(content)
                structure["has_headers"] = isinstance(data, dict) and len(data) > 0
                structure["has_metadata"] = any(key in str(data).lower() for key in ['name', 'description', 'version', 'author'])
            except Exception:
                pass
        
        elif format_detected == "yaml":
            structure["has_headers"] = any(line.strip().startswith('#') for line in lines[:5])
            structure["has_metadata"] = any('name:' in line.lower() or 'description:' in line.lower() for line in lines)
        
        elif format_detected == "plain_protocols":
            structure["has_headers"] = any(line.startswith('#') or line.startswith('//') for line in lines[:3])
        
        # Determine structure complexity
        if format_detected in ["json", "yaml"]:
            structure["structure_complexity"] = "complex"
        elif format_detected == "base64":
            structure["structure_complexity"] = "encoded"
        else:
            structure["structure_complexity"] = "simple"
        
        return structure
    
    def _analyze_quality_indicators(self, content: str, format_detected: str) -> Dict[str, bool]:
        """Analyze content for quality indicators.
        
        Args:
            content: Content to analyze
            format_detected: Detected format
            
        Returns:
            Dictionary of quality indicators
        """
        indicators = {
            "base64_encoded": format_detected == "base64",
            "json_format": format_detected == "json",
            "yaml_format": format_detected == "yaml",
            "multiple_protocols": False,
            "server_metadata": False,
            "configuration_completeness": False,
        }
        
        # Check for multiple protocols
        protocol_count = 0
        protocols = ['vmess://', 'vless://', 'trojan://', 'ss://', 'ssr://', 'http://', 'https://']
        for protocol in protocols:
            if protocol in content.lower():
                protocol_count += 1
        
        indicators["multiple_protocols"] = protocol_count > 1
        
        # Check for server metadata
        metadata_keywords = ['server', 'port', 'host', 'address', 'ip', 'domain']
        indicators["server_metadata"] = any(keyword in content.lower() for keyword in metadata_keywords)
        
        # Check for configuration completeness
        completeness_keywords = ['password', 'uuid', 'key', 'token', 'auth', 'method', 'cipher']
        indicators["configuration_completeness"] = any(keyword in content.lower() for keyword in completeness_keywords)
        
        return indicators
    
    def _calculate_quality_score(self, quality_indicators: Dict[str, bool]) -> float:
        """Calculate overall quality score based on indicators.
        
        Args:
            quality_indicators: Dictionary of quality indicators
            
        Returns:
            Quality score (0.0 to 1.0)
        """
        score = 0.0
        
        for indicator, weight in self.quality_indicators.items():
            if quality_indicators.get(indicator, False):
                score += weight
        
        return min(1.0, score)
    
    def _estimate_config_count(self, content: str, format_detected: str) -> int:
        """Estimate the number of configurations in content.
        
        Args:
            content: Content to analyze
            format_detected: Detected format
            
        Returns:
            Estimated number of configurations
        """
        if format_detected == "json":
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    return len(data)
                elif isinstance(data, dict):
                    # Look for common keys that might contain configs
                    config_keys = ['configs', 'servers', 'proxies', 'outbounds', 'inbounds']
                    for key in config_keys:
                        if key in data and isinstance(data[key], list):
                            return len(data[key])
                    return 1
            except Exception:
                pass
        
        elif format_detected == "yaml":
            # Count YAML list items
            lines = content.split('\n')
            list_items = sum(1 for line in lines if line.strip().startswith('- '))
            return max(1, list_items)
        
        elif format_detected == "plain_protocols":
            # Count protocol URLs
            protocols = ['vmess://', 'vless://', 'trojan://', 'ss://', 'ssr://']
            count = sum(content.lower().count(protocol) for protocol in protocols)
            return max(1, count)
        
        elif format_detected == "base64":
            try:
                import base64
                decoded = base64.b64decode(content).decode('utf-8')
                return self._estimate_config_count(decoded, self._detect_format(decoded))
            except Exception:
                pass
        
        # Fallback: estimate based on content length and separators
        separators = ['\n', '|', ';', ',']
        max_separator_count = max(content.count(sep) for sep in separators)
        return max(1, max_separator_count // 2)