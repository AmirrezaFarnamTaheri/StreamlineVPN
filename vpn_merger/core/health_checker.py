"""
Source Health Checker
====================

Validates source accessibility and content quality.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Union

try:
    import aiohttp
except ImportError:
    aiohttp = None

logger = logging.getLogger(__name__)


class SourceHealthChecker:
    """Source validation and health checking with reliability scoring.
    
    This class provides asynchronous health checking for VPN sources,
    including accessibility validation, content analysis, and reliability scoring.
    
    Attributes:
        timeout: Request timeout in seconds
        session: aiohttp client session
    """
    
    def __init__(self, timeout: int = 30):
        """Initialize the health checker.
        
        Args:
            timeout: Request timeout in seconds
        """
        if timeout <= 0:
            raise ValueError("Timeout must be positive")
        
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry.
        
        Returns:
            Self instance with initialized session
            
        Raises:
            ImportError: If aiohttp is not available
        """
        if aiohttp is None:
            raise ImportError("aiohttp is required for source validation")
        
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def validate_source(self, url: str) -> Dict[str, Union[str, bool, int, float, List[str]]]:
        """Validate a single source URL with comprehensive health checks.
        
        Args:
            url: Source URL to validate
            
        Returns:
            Dictionary containing validation results
            
        Raises:
            RuntimeError: If session is not initialized
        """
        if not self.session:
            raise RuntimeError("Health checker session not initialized. Use async context manager.")
        
        if not url or not isinstance(url, str):
            return self._create_error_result(str(url) if url else 'unknown', 'Invalid URL')
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    estimated_configs = self._estimate_config_count(content)
                    protocols_found = self._detect_protocols(content)
                    
                    return {
                        'url': url,
                        'accessible': True,
                        'status_code': response.status,
                        'estimated_configs': estimated_configs,
                        'protocols_found': protocols_found,
                        'reliability_score': self._calculate_reliability_score(
                            response.status, estimated_configs, protocols_found
                        )
                    }
                else:
                    return self._create_error_result(url, f"HTTP {response.status}")
        except asyncio.TimeoutError:
            return self._create_error_result(url, 'Request timeout')
        except Exception as e:
            logger.debug(f"Error validating source {url}: {e}")
            return self._create_error_result(url, str(e))
    
    def _create_error_result(self, url: str, error: str) -> Dict[str, Union[str, bool, float]]:
        """Create a standardized error result.
        
        Args:
            url: Source URL
            error: Error message
            
        Returns:
            Dictionary containing error result
        """
        return {
            'url': url,
            'accessible': False,
            'error': error,
            'reliability_score': 0.0
        }
    
    def _estimate_config_count(self, content: str) -> int:
        """Estimate the number of configurations in content.
        
        Args:
            content: Raw content to analyze
            
        Returns:
            Estimated number of configurations
        """
        if not content:
            return 0
        
        # Count non-empty lines as potential configs
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        return len(lines)
    
    def _detect_protocols(self, content: str) -> List[str]:
        """Detect protocols in content with comprehensive pattern matching.
        
        Args:
            content: Raw content to analyze
            
        Returns:
            List of detected protocol names
        """
        if not content:
            return []
        
        protocols = []
        content_lower = content.lower()
        
        # Split content into lines and check each line for protocols
        lines = content_lower.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check each protocol independently for each line
            if line.startswith('ssr://') and 'shadowsocksr' not in protocols:
                protocols.append('shadowsocksr')
            if line.startswith('ss://') and 'shadowsocks' not in protocols:
                protocols.append('shadowsocks')
            if line.startswith('shadowsocks://') and 'shadowsocks' not in protocols:
                protocols.append('shadowsocks')
            if line.startswith('vmess://') and 'vmess' not in protocols:
                protocols.append('vmess')
            if line.startswith('vless://') and 'vless' not in protocols:
                protocols.append('vless')
            if line.startswith('trojan://') and 'trojan' not in protocols:
                protocols.append('trojan')
            if line.startswith('hysteria2://') and 'hysteria' not in protocols:
                protocols.append('hysteria')
            if line.startswith('hysteria://') and 'hysteria' not in protocols:
                protocols.append('hysteria')
            if line.startswith('tuic://') and 'tuic' not in protocols:
                protocols.append('tuic')
        
        return protocols
    
    def _calculate_reliability_score(self, status: int, config_count: int, protocols: List[str]) -> float:
        """Calculate reliability score for a source based on multiple factors.
        
        Args:
            status: HTTP status code
            config_count: Estimated number of configurations
            protocols: List of detected protocols
            
        Returns:
            Reliability score between 0.0 and 1.0
        """
        score = 0.0
        
        # Status code bonus
        if status == 200:
            score += 0.4
        
        # Config count bonus (normalized)
        if config_count > 0:
            score += min(0.3, config_count / 10000)  # Cap at 0.3
        
        # Protocol diversity bonus
        score += min(0.3, len(protocols) * 0.1)  # 0.1 per protocol, cap at 0.3
        
        return min(1.0, score)
    
    def get_health_summary(self, validation_results: List[Dict[str, Union[str, bool, int, float, List[str]]]]) -> Dict[str, Union[int, float]]:
        """Generate health summary from validation results.
        
        Args:
            validation_results: List of validation result dictionaries
            
        Returns:
            Dictionary containing health summary statistics
        """
        total_sources = len(validation_results)
        if total_sources == 0:
            return self._create_empty_summary()
        
        accessible_sources = [r for r in validation_results if r.get('accessible')]
        failed_sources = [r for r in validation_results if not r.get('accessible')]
        
        success_rate = len(accessible_sources) / total_sources
        average_reliability = sum(
            r.get('reliability_score', 0.0) for r in accessible_sources
        ) / max(len(accessible_sources), 1)
        
        # Calculate total estimated configs
        total_configs = sum(
            r.get('estimated_configs', 0) for r in accessible_sources
        )
        
        # Calculate protocol diversity
        all_protocols = set()
        for r in accessible_sources:
            protocols = r.get('protocols_found', [])
            if isinstance(protocols, list):
                all_protocols.update(protocols)
        protocol_diversity = len(all_protocols)
        
        return {
            'total_sources': total_sources,
            'accessible_sources': len(accessible_sources),
            'failed_sources': len(failed_sources),
            'success_rate': success_rate,
            'average_reliability': average_reliability,
            'total_configs': total_configs,
            'protocol_diversity': protocol_diversity
        }
    
    def _create_empty_summary(self) -> Dict[str, Union[int, float]]:
        """Create an empty summary for when there are no results.
        
        Returns:
            Dictionary containing empty summary
        """
        return {
            'total_sources': 0,
            'accessible_sources': 0,
            'failed_sources': 0,
            'success_rate': 0.0,
            'average_reliability': 0.0,
            'total_configs': 0,
            'protocol_diversity': 0
        }
    
    def get_validation_stats(self) -> Dict[str, Union[int, float]]:
        """Get validation statistics for this checker instance.
        
        Returns:
            Dictionary containing validation statistics
        """
        return {
            'timeout': self.timeout,
            'session_active': self.session is not None
        }
