"""
Unified Source Validator
=======================

Consolidated source validation functionality that combines health checking,
accessibility testing, and reliability scoring for VPN configuration sources.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass

import aiohttp

logger = logging.getLogger(__name__)

# Validation constants
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_REDIRECTS = 5
DEFAULT_USER_AGENT = "VPN-Merger/2.0.0"
MIN_RELIABILITY_SCORE = 0.0
MAX_RELIABILITY_SCORE = 1.0

# Protocol patterns for detection
VPN_PROTOCOL_PATTERNS = {
    'vmess': 'vmess://',
    'vless': 'vless://',
    'trojan': 'trojan://',
    'shadowsocks': 'ss://',
    'shadowsocksr': 'ssr://',
    'http': 'http://',
    'https': 'https://',
    'socks': 'socks://',
    'socks5': 'socks5://',
    'hysteria': 'hysteria://',
    'tuic': 'tuic://'
}

# Reliability scoring weights
RELIABILITY_WEIGHTS = {
    'status_code': 0.3,
    'config_count': 0.4,
    'protocol_diversity': 0.2,
    'response_time': 0.1
}


@dataclass
class ValidationResult:
    """Result of source validation."""
    url: str
    accessible: bool
    status_code: int
    content_length: int
    estimated_configs: int
    protocols_found: List[str]
    reliability_score: float
    response_time: float
    error: Optional[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'url': self.url,
            'accessible': self.accessible,
            'status_code': self.status_code,
            'content_length': self.content_length,
            'estimated_configs': self.estimated_configs,
            'protocols_found': self.protocols_found,
            'reliability_score': self.reliability_score,
            'response_time': self.response_time,
            'error': self.error,
            'timestamp': self.timestamp.isoformat()
        }


class UnifiedSourceValidator:
    """Unified source validator with comprehensive health checking and reliability scoring.
    
    This class consolidates source validation functionality that was previously
    duplicated across multiple modules. It provides comprehensive validation
    including accessibility testing, content analysis, and reliability scoring.
    """
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT, max_redirects: int = DEFAULT_MAX_REDIRECTS):
        """Initialize the unified source validator.
        
        Args:
            timeout: Request timeout in seconds
            max_redirects: Maximum number of redirects to follow
        """
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.session: Optional[aiohttp.ClientSession] = None
        self.validation_history: List[ValidationResult] = []
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup_session()
    
    async def _initialize_session(self):
        """Initialize aiohttp session."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={'User-Agent': DEFAULT_USER_AGENT}
            )
    
    async def _cleanup_session(self):
        """Clean up aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def validate_source(self, url: str) -> ValidationResult:
        """Validate a single source URL with comprehensive health checks.
        
        Args:
            url: Source URL to validate
            
        Returns:
            ValidationResult with comprehensive validation data
            
        Raises:
            RuntimeError: If session is not initialized
        """
        if not self.session:
            raise RuntimeError("Validator session not initialized. Use async context manager.")
        
        if not url or not isinstance(url, str):
            return self._create_error_result(str(url) if url else 'unknown', 'Invalid URL')
        
        start_time = time.time()
        
        try:
            async with self.session.get(url, allow_redirects=True, max_redirects=self.max_redirects) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    content = await response.text()
                    estimated_configs = self._estimate_config_count(content)
                    protocols_found = self._detect_protocols(content)
                    reliability_score = self._calculate_reliability_score(
                        response.status, estimated_configs, protocols_found, response_time
                    )
                    
                    result = ValidationResult(
                        url=url,
                        accessible=True,
                        status_code=response.status,
                        content_length=len(content),
                        estimated_configs=estimated_configs,
                        protocols_found=protocols_found,
                        reliability_score=reliability_score,
                        response_time=response_time,
                        error=None,
                        timestamp=datetime.now()
                    )
                else:
                    result = self._create_error_result(url, f"HTTP {response.status}", response_time)
                
                # Store in history
                self.validation_history.append(result)
                
                return result
                
        except asyncio.TimeoutError:
            result = self._create_error_result(url, 'Request timeout', time.time() - start_time)
            self.validation_history.append(result)
            return result
        except Exception as e:
            logger.debug(f"Error validating source {url}: {e}")
            result = self._create_error_result(url, str(e), time.time() - start_time)
            self.validation_history.append(result)
            return result
    
    async def validate_multiple_sources(self, urls: List[str], max_concurrent: int = 10) -> List[ValidationResult]:
        """Validate multiple source URLs concurrently.
        
        Args:
            urls: List of source URLs to validate
            max_concurrent: Maximum number of concurrent validations
            
        Returns:
            List of ValidationResult objects
        """
        if not urls:
            return []
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def validate_with_semaphore(url: str) -> ValidationResult:
            async with semaphore:
                return await self.validate_source(url)
        
        tasks = [validate_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and convert to ValidationResult
        valid_results = []
        for result in results:
            if isinstance(result, ValidationResult):
                valid_results.append(result)
            else:
                logger.error(f"Validation failed with exception: {result}")
        
        return valid_results
    
    def _create_error_result(self, url: str, error: str, response_time: float = 0.0) -> ValidationResult:
        """Create a standardized error result.
        
        Args:
            url: Source URL
            error: Error message
            response_time: Response time (0.0 for errors)
            
        Returns:
            ValidationResult with error information
        """
        return ValidationResult(
            url=url,
            accessible=False,
            status_code=0,
            content_length=0,
            estimated_configs=0,
            protocols_found=[],
            reliability_score=0.0,
            response_time=response_time,
            error=error,
            timestamp=datetime.now()
        )
    
    def _estimate_config_count(self, content: str) -> int:
        """Estimate the number of VPN configurations in content.
        
        Args:
            content: Raw content to analyze
            
        Returns:
            Estimated number of configurations
        """
        if not content:
            return 0
        
        # Count lines that contain VPN protocol patterns
        lines = content.split('\n')
        config_count = 0
        
        for line in lines:
            line_lower = line.strip().lower()
            if any(pattern in line_lower for pattern in VPN_PROTOCOL_PATTERNS.values()):
                config_count += 1
        
        return config_count
    
    def _detect_protocols(self, content: str) -> List[str]:
        """Detect VPN protocols present in content.
        
        Args:
            content: Raw content to analyze
            
        Returns:
            List of detected protocol names
        """
        if not content:
            return []
        
        content_lower = content.lower()
        detected_protocols = []
        
        for protocol, pattern in VPN_PROTOCOL_PATTERNS.items():
            if pattern in content_lower:
                detected_protocols.append(protocol)
        
        return detected_protocols
    
    def _calculate_reliability_score(self, status_code: int, config_count: int, 
                                   protocols_found: List[str], response_time: float) -> float:
        """Calculate reliability score based on multiple factors.
        
        Args:
            status_code: HTTP status code
            config_count: Number of estimated configurations
            protocols_found: List of detected protocols
            response_time: Response time in seconds
            
        Returns:
            Reliability score between 0.0 and 1.0
        """
        # Status code score (200 = 1.0, 4xx = 0.5, 5xx = 0.0)
        status_score = 1.0 if status_code == 200 else (0.5 if 400 <= status_code < 500 else 0.0)
        
        # Config count score (more configs = higher score, capped at 1000)
        config_score = min(config_count / 1000.0, 1.0)
        
        # Protocol diversity score (more protocols = higher score, capped at 5)
        protocol_diversity_score = min(len(protocols_found) / 5.0, 1.0)
        
        # Response time score (faster = higher score, optimal < 1s)
        response_time_score = max(0.0, 1.0 - (response_time / 5.0))  # 5s = 0.0 score
        
        # Weighted combination
        final_score = (
            RELIABILITY_WEIGHTS['status_code'] * status_score +
            RELIABILITY_WEIGHTS['config_count'] * config_score +
            RELIABILITY_WEIGHTS['protocol_diversity'] * protocol_diversity_score +
            RELIABILITY_WEIGHTS['response_time'] * response_time_score
        )
        
        return max(MIN_RELIABILITY_SCORE, min(MAX_RELIABILITY_SCORE, final_score))
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get statistics about validation history.
        
        Returns:
            Dictionary with validation statistics
        """
        if not self.validation_history:
            return {
                'total_validations': 0,
                'successful_validations': 0,
                'failed_validations': 0,
                'average_reliability_score': 0.0,
                'average_response_time': 0.0,
                'protocol_distribution': {},
                'error_distribution': {}
            }
        
        successful = [r for r in self.validation_history if r.accessible]
        failed = [r for r in self.validation_history if not r.accessible]
        
        # Protocol distribution
        protocol_counts = {}
        for result in successful:
            for protocol in result.protocols_found:
                protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1
        
        # Error distribution
        error_counts = {}
        for result in failed:
            error = result.error or 'Unknown'
            error_counts[error] = error_counts.get(error, 0) + 1
        
        return {
            'total_validations': len(self.validation_history),
            'successful_validations': len(successful),
            'failed_validations': len(failed),
            'average_reliability_score': sum(r.reliability_score for r in successful) / len(successful) if successful else 0.0,
            'average_response_time': sum(r.response_time for r in self.validation_history) / len(self.validation_history),
            'protocol_distribution': protocol_counts,
            'error_distribution': error_counts
        }
    
    def filter_by_reliability(self, min_score: float = 0.5) -> List[ValidationResult]:
        """Filter validation results by minimum reliability score.
        
        Args:
            min_score: Minimum reliability score threshold
            
        Returns:
            List of ValidationResult objects meeting the threshold
        """
        return [r for r in self.validation_history if r.reliability_score >= min_score]
    
    def get_top_sources(self, limit: int = 10) -> List[ValidationResult]:
        """Get top sources by reliability score.
        
        Args:
            limit: Maximum number of sources to return
            
        Returns:
            List of top ValidationResult objects
        """
        successful = [r for r in self.validation_history if r.accessible]
        sorted_results = sorted(successful, key=lambda x: x.reliability_score, reverse=True)
        return sorted_results[:limit]


# Backward compatibility aliases
SourceHealthChecker = UnifiedSourceValidator
SourceValidator = UnifiedSourceValidator
