"""
Source Processor
===============

Handles source fetching and processing operations for VPN configurations.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Union

import aiohttp

from ..models.configuration import VPNConfiguration
from .source_validator import UnifiedSourceValidator
from .config_processor import ConfigurationProcessor

logger = logging.getLogger(__name__)

# Processing constants
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1MB chunks for efficient processing


class SourceProcessor:
    """Handles source fetching and processing operations."""
    
    def __init__(self):
        """Initialize source processor."""
        self.config_processor = ConfigurationProcessor()
        self.session = None
        self.processing_stats = {
            'total_sources': 0,
            'processed_sources': 0,
            'total_configs': 0,
            'valid_configs': 0,
            'duplicate_configs': 0,
            'start_time': None,
            'end_time': None
        }
        self.source_processing_times: Dict[str, float] = {}
        self.error_counts: Dict[str, int] = {}
    
    async def __aenter__(self):
        """Async context manager entry."""
        timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def process_sources(self, sources: List[str], 
                            max_concurrent: int = 50) -> List[VPNConfiguration]:
        """Process multiple sources concurrently.
        
        Args:
            sources: List of source URLs to process
            max_concurrent: Maximum number of concurrent processing tasks
            
        Returns:
            List of processed VPN configurations
        """
        if not self.session:
            raise RuntimeError("Processor not initialized. Use async context manager.")
        
        self.processing_stats['start_time'] = datetime.now()
        self.processing_stats['total_sources'] = len(sources)
        
        logger.info(f"Starting source processing with {len(sources)} sources")
        
        # Process sources with concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_source(source_url: str):
            async with semaphore:
                return await self._process_single_source(source_url)
        
        # Create tasks for all sources
        tasks = [process_source(source) for source in sources]
        
        # Process with progress tracking
        results = []
        for coro in asyncio.as_completed(tasks):
            try:
                source_results = await coro
                if source_results:
                    results.extend(source_results)
            except Exception as e:
                logger.error(f"Error processing source: {e}")
        
        # Sort results by quality score
        results.sort(key=lambda x: x.quality_score, reverse=True)
        
        self.processing_stats['end_time'] = datetime.now()
        self.processing_stats['valid_configs'] = len(results)
        
        logger.info(f"Processing completed: {self.processing_stats['valid_configs']} valid configs from {self.processing_stats['processed_sources']} sources")
        
        return results
    
    async def _process_single_source(self, source_url: str) -> List[VPNConfiguration]:
        """Process a single source URL with error handling.
        
        Args:
            source_url: Source URL to process
            
        Returns:
            List of processed VPN configurations
        """
        start_time = datetime.now()
        results = []
        
        try:
            self.processing_stats['processed_sources'] += 1
            
            # Validate source
            async with UnifiedSourceValidator() as validator:
                validation_result = await validator.validate_source(source_url)
                # validation_result is a ValidationResult dataclass
                if not getattr(validation_result, 'accessible', False):
                    logger.debug(f"Source not accessible: {source_url}")
                    return results

            # Fetch and process content
            configs = await self._fetch_source_content(source_url)
            
            for config in configs:
                result = self.config_processor.process_config(config, source_url)
                if result:
                    results.append(result)
                    self.processing_stats['total_configs'] += 1
                else:
                    self.processing_stats['duplicate_configs'] += 1
                    
        except Exception as e:
            logger.error(f"Error processing source {source_url}: {e}")
            self.error_counts[source_url] = self.error_counts.get(source_url, 0) + 1
        finally:
            # Record processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            self.source_processing_times[source_url] = processing_time
        
        return results
    
    async def _fetch_source_content(self, source_url: str) -> List[str]:
        """Fetch content from source URL with error handling.
        
        Args:
            source_url: Source URL to fetch from
            
        Returns:
            List of configuration strings
        """
        # In test mode, avoid real network and simulate predictable work
        if os.environ.get('SKIP_NETWORK') or os.environ.get('VPN_MERGER_TEST_MODE'):
            # Simulate small I/O delay to allow concurrency to matter
            await asyncio.sleep(0.005)
            # Return a small batch of synthetic configs to process
            return [
                "vmess://test1",
                "vless://test2",
                "trojan://test3",
                "ss://dGVzdDp0ZXN0@host:8388#name",
            ]
        try:
            async with self.session.get(source_url) as response:
                if response.status == 200:
                    content = await response.text()
                    return [line.strip() for line in content.split('\n') if line.strip()]
                else:
                    logger.warning(f"Failed to fetch {source_url}: HTTP {response.status}")
                    return []
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {source_url}")
            return []
        except Exception as e:
            logger.error(f"Error fetching {source_url}: {e}")
            return []
    
    async def fetch_with_retry(self, source_url: str, max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[str]:
        """Fetch content with retry logic.
        
        Args:
            source_url: Source URL to fetch
            max_retries: Maximum number of retry attempts
            
        Returns:
            Fetched content or None if failed
        """
        for attempt in range(max_retries + 1):
            try:
                async with self.session.get(source_url) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 404:
                        logger.warning(f"Source not found: {source_url}")
                        return None
                    else:
                        logger.warning(f"HTTP {response.status} for {source_url}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {source_url} (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Error fetching {source_url} (attempt {attempt + 1}): {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
        
        logger.error(f"Failed to fetch {source_url} after {max_retries + 1} attempts")
        return None
    
    async def validate_sources(self, sources: List[str]) -> Dict[str, Dict]:
        """Validate multiple sources concurrently.
        
        Args:
            sources: List of source URLs to validate
            
        Returns:
            Dictionary mapping source URLs to validation results
        """
        async with UnifiedSourceValidator() as validator:
            tasks = [validator.validate_source(source) for source in sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            validation_results = {}
            for source, result in zip(sources, results):
                if isinstance(result, Exception):
                    validation_results[source] = {
                        'accessible': False,
                        'error': str(result),
                        'reliability_score': 0.0
                    }
                else:
                    # Convert ValidationResult to dict for callers
                    if hasattr(result, 'to_dict'):
                        validation_results[source] = result.to_dict()
                    else:
                        # Already a dict
                        validation_results[source] = dict(result)
            
            return validation_results
    
    def get_processing_statistics(self) -> Dict[str, Union[int, float, str, Dict]]:
        """Get comprehensive processing statistics.
        
        Returns:
            Dictionary containing processing statistics
        """
        return {
            **self.processing_stats,
            'source_processing_times': self.source_processing_times,
            'error_counts': self.error_counts,
            'success_rate': (
                self.processing_stats['processed_sources'] / self.processing_stats['total_sources']
            ) if self.processing_stats['total_sources'] > 0 else 0.0,
            'processing_duration': (
                (self.processing_stats['end_time'] - self.processing_stats['start_time']).total_seconds()
            ) if self.processing_stats['start_time'] and self.processing_stats['end_time'] else None
        }
    
    def get_processing_summary(self) -> Dict[str, Union[int, float, str]]:
        """Get a human-readable processing summary.
        
        Returns:
            Dictionary containing processing summary information
        """
        stats = self.get_processing_statistics()
        
        return {
            'total_sources': stats['total_sources'],
            'processed_sources': stats['processed_sources'],
            'valid_configs': stats['valid_configs'],
            'duplicate_configs': stats['duplicate_configs'],
            'success_rate': f"{stats['success_rate']:.1%}",
            'processing_duration': f"{stats['processing_duration']:.1f}s" if stats['processing_duration'] else 'N/A'
        }
    
    def reset_statistics(self) -> None:
        """Reset processing statistics."""
        self.processing_stats = {
            'total_sources': 0,
            'processed_sources': 0,
            'total_configs': 0,
            'valid_configs': 0,
            'duplicate_configs': 0,
            'start_time': None,
            'end_time': None
        }
        self.source_processing_times.clear()
        self.error_counts.clear()
