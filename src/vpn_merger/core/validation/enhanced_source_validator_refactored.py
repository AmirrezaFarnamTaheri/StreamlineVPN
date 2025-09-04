"""
Enhanced Source Validator (Refactored)
======================================

Advanced source validation with quality scoring, historical tracking, and
comprehensive source analysis for VPN configuration sources.

This is a refactored version that uses modular components for better maintainability.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import aiohttp

from .quality_metrics import SourceQualityMetrics, ValidationResult
from .quality_weights import DEFAULT_TIMEOUT, DEFAULT_MAX_REDIRECTS, DEFAULT_USER_AGENT
from .protocol_analyzer import ProtocolAnalyzer
from .ssl_analyzer import SSLAnalyzer
from .content_analyzer import ContentAnalyzer

logger = logging.getLogger(__name__)


class EnhancedSourceValidator:
    """Enhanced source validator with modular components."""
    
    def __init__(self, cache_file: Optional[str] = None):
        """Initialize the enhanced source validator.
        
        Args:
            cache_file: Optional path to cache file for storing quality metrics
        """
        self.cache_file = Path(cache_file) if cache_file else Path("quality_metrics_cache.json")
        self.quality_metrics: Dict[str, SourceQualityMetrics] = {}
        
        # Initialize analyzers
        self.protocol_analyzer = ProtocolAnalyzer()
        self.ssl_analyzer = SSLAnalyzer()
        self.content_analyzer = ContentAnalyzer()
        
        # Load cached metrics
        self._load_cached_metrics()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._save_cached_metrics()
    
    async def validate_source(self, url: str) -> ValidationResult:
        """Validate a single source with comprehensive analysis.
        
        Args:
            url: Source URL to validate
            
        Returns:
            ValidationResult containing validation details
        """
        start_time = time.time()
        
        try:
            # Perform HTTP request
            response_data = await self._fetch_source(url)
            
            # Analyze content
            content_analysis = self.content_analyzer.analyze_content(
                response_data["content"], 
                response_data.get("content_type", "text/plain")
            )
            
            # Analyze protocols
            protocols_found, quality_indicators = self.protocol_analyzer.analyze_content(
                response_data["content"]
            )
            
            # Analyze SSL certificate
            ssl_analysis = await self.ssl_analyzer.analyze_ssl_certificate(url)
            
            # Calculate response time score
            response_time = time.time() - start_time
            response_time_score = self._calculate_response_time_score(response_time)
            
            # Calculate reliability score
            reliability_score = self._calculate_reliability_score(
                response_data["status_code"],
                response_time,
                ssl_analysis["ssl_score"],
                content_analysis["quality_score"]
            )
            
            # Create validation result
            result = ValidationResult(
                url=url,
                accessible=response_data["status_code"] == 200,
                response_time=response_time,
                status_code=response_data["status_code"],
                content_length=len(response_data["content"]),
                protocols_found=protocols_found,
                content_quality_indicators=quality_indicators,
                ssl_info=ssl_analysis,
                reliability_score=reliability_score,
                estimated_configs=content_analysis["estimated_configs"]
            )
            
            # Update quality metrics
            self._update_quality_metrics(url, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating source {url}: {e}")
            return ValidationResult(
                url=url,
                accessible=False,
                response_time=time.time() - start_time,
                status_code=0,
                content_length=0,
                protocols_found=set(),
                content_quality_indicators={},
                ssl_info={},
                error_message=str(e),
                reliability_score=0.0,
                estimated_configs=0
            )
    
    async def validate_multiple_sources_quality(self, urls: List[str]) -> List[SourceQualityMetrics]:
        """Validate multiple sources and return quality metrics.
        
        Args:
            urls: List of URLs to validate
            
        Returns:
            List of SourceQualityMetrics
        """
        tasks = [self.validate_source(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        quality_metrics = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error validating {urls[i]}: {result}")
                continue
            
            if isinstance(result, ValidationResult):
                metrics = self._create_quality_metrics(result)
                quality_metrics.append(metrics)
        
        return quality_metrics
    
    async def _fetch_source(self, url: str) -> Dict[str, Any]:
        """Fetch source content with proper error handling.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dictionary containing response data
        """
        timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        headers = {"User-Agent": DEFAULT_USER_AGENT}
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(url, headers=headers, max_redirects=DEFAULT_MAX_REDIRECTS) as response:
                    content = await response.text()
                    return {
                        "content": content,
                        "status_code": response.status,
                        "content_type": response.headers.get("content-type", "text/plain"),
                        "headers": dict(response.headers)
                    }
            except Exception as e:
                logger.error(f"Failed to fetch {url}: {e}")
                raise
    
    def _calculate_response_time_score(self, response_time: float) -> float:
        """Calculate response time score.
        
        Args:
            response_time: Response time in seconds
            
        Returns:
            Response time score (0.0 to 1.0)
        """
        if response_time <= 1.0:
            return 1.0
        elif response_time <= 3.0:
            return 0.8
        elif response_time <= 5.0:
            return 0.6
        elif response_time <= 10.0:
            return 0.4
        else:
            return 0.2
    
    def _calculate_reliability_score(
        self, 
        status_code: int, 
        response_time: float, 
        ssl_score: float, 
        content_quality: float
    ) -> float:
        """Calculate overall reliability score.
        
        Args:
            status_code: HTTP status code
            response_time: Response time in seconds
            ssl_score: SSL security score
            content_quality: Content quality score
            
        Returns:
            Reliability score (0.0 to 1.0)
        """
        # Base score from status code
        if status_code == 200:
            base_score = 1.0
        elif 200 <= status_code < 300:
            base_score = 0.8
        elif 300 <= status_code < 400:
            base_score = 0.6
        else:
            base_score = 0.0
        
        # Adjust based on other factors
        response_time_score = self._calculate_response_time_score(response_time)
        
        # Weighted combination
        reliability = (
            base_score * 0.4 +
            response_time_score * 0.2 +
            ssl_score * 0.2 +
            content_quality * 0.2
        )
        
        return max(0.0, min(1.0, reliability))
    
    def _update_quality_metrics(self, url: str, result: ValidationResult) -> None:
        """Update quality metrics for a source.
        
        Args:
            url: Source URL
            result: Validation result
        """
        if url not in self.quality_metrics:
            self.quality_metrics[url] = SourceQualityMetrics(
                url=url,
                quality_score=0.0,
                historical_reliability=0.0,
                ssl_certificate_score=0.0,
                response_time_score=0.0,
                content_quality_score=0.0,
                protocol_diversity_score=0.0,
                uptime_consistency_score=0.0,
                last_checked=datetime.now()
            )
        
        metrics = self.quality_metrics[url]
        
        # Update historical data
        metrics.update_historical_data(result.accessible, result.response_time)
        
        # Update individual scores
        metrics.ssl_certificate_score = result.ssl_info.get("ssl_score", 0.0)
        metrics.response_time_score = self._calculate_response_time_score(result.response_time)
        metrics.content_quality_score = sum(result.content_quality_indicators.values()) / max(1, len(result.content_quality_indicators))
        metrics.protocol_diversity_score = min(1.0, len(result.protocols_found) / 5.0)  # Normalize to 5 protocols
        metrics.uptime_consistency_score = metrics.historical_reliability
        
        # Update protocols and content indicators
        metrics.protocols_found.update(result.protocols_found)
        metrics.content_indicators.update(result.content_quality_indicators)
        metrics.ssl_info.update(result.ssl_info)
        
        # Calculate overall quality
        metrics.calculate_overall_quality()
    
    def _create_quality_metrics(self, result: ValidationResult) -> SourceQualityMetrics:
        """Create quality metrics from validation result.
        
        Args:
            result: Validation result
            
        Returns:
            SourceQualityMetrics object
        """
        return SourceQualityMetrics(
            url=result.url,
            quality_score=result.reliability_score,
            historical_reliability=result.reliability_score,
            ssl_certificate_score=result.ssl_info.get("ssl_score", 0.0),
            response_time_score=self._calculate_response_time_score(result.response_time),
            content_quality_score=sum(result.content_quality_indicators.values()) / max(1, len(result.content_quality_indicators)),
            protocol_diversity_score=min(1.0, len(result.protocols_found) / 5.0),
            uptime_consistency_score=result.reliability_score,
            last_checked=datetime.now(),
            protocols_found=result.protocols_found,
            content_indicators=result.content_quality_indicators,
            ssl_info=result.ssl_info
        )
    
    def _load_cached_metrics(self) -> None:
        """Load quality metrics from cache file."""
        try:
            if self.cache_file.exists():
                import json
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    for url, metrics_data in data.items():
                        self.quality_metrics[url] = SourceQualityMetrics.from_dict(metrics_data)
                logger.info(f"Loaded {len(self.quality_metrics)} cached quality metrics")
        except Exception as e:
            logger.warning(f"Failed to load cached metrics: {e}")
    
    async def _save_cached_metrics(self) -> None:
        """Save quality metrics to cache file."""
        try:
            import json
            data = {url: metrics.to_dict() for url, metrics in self.quality_metrics.items()}
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.quality_metrics)} quality metrics to cache")
        except Exception as e:
            logger.warning(f"Failed to save cached metrics: {e}")
    
    def get_quality_statistics(self) -> Dict[str, Any]:
        """Get quality statistics for all sources.
        
        Returns:
            Dictionary containing quality statistics
        """
        if not self.quality_metrics:
            return {"total_sources": 0}
        
        scores = [metrics.quality_score for metrics in self.quality_metrics.values()]
        
        return {
            "total_sources": len(self.quality_metrics),
            "average_quality": sum(scores) / len(scores),
            "max_quality": max(scores),
            "min_quality": min(scores),
            "high_quality_sources": sum(1 for score in scores if score >= 0.8),
            "medium_quality_sources": sum(1 for score in scores if 0.5 <= score < 0.8),
            "low_quality_sources": sum(1 for score in scores if score < 0.5),
        }
    
    def filter_by_quality(self, min_quality: float = 0.5) -> List[SourceQualityMetrics]:
        """Filter sources by minimum quality score.
        
        Args:
            min_quality: Minimum quality score threshold
            
        Returns:
            List of high-quality source metrics
        """
        return [
            metrics for metrics in self.quality_metrics.values()
            if metrics.quality_score >= min_quality
        ]
    
    def get_top_quality_sources(self, limit: int = 10) -> List[SourceQualityMetrics]:
        """Get top quality sources.
        
        Args:
            limit: Maximum number of sources to return
            
        Returns:
            List of top quality source metrics
        """
        sorted_metrics = sorted(
            self.quality_metrics.values(),
            key=lambda x: x.quality_score,
            reverse=True
        )
        return sorted_metrics[:limit]
