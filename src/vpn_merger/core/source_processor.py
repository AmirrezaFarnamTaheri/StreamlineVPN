"""
Source Processor
===============

Handles source fetching and processing operations for VPN configurations.
Refactored to use modular components for better maintainability.
"""

import logging
from typing import List

from ..models.configuration import VPNConfiguration
from .processing import BatchProcessor, StatisticsTracker

logger = logging.getLogger(__name__)


class SourceProcessor:
    """Handles source fetching and processing operations."""

    def __init__(self):
        """Initialize source processor."""
        self.batch_processor = BatchProcessor()
        self.statistics_tracker = StatisticsTracker()
        
        # Add config_processor for backward compatibility
        from .config_processor import ConfigurationProcessor
        self.config_processor = ConfigurationProcessor()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass

    async def process_sources_batch(
        self, sources: List[str], batch_size: int = 10, max_concurrent: int = 50
    ) -> List[VPNConfiguration]:
        """Process sources in batches with proper async concurrency control.
        
        Args:
            sources: List of source URLs to process
            batch_size: Number of sources to process in each batch
            max_concurrent: Maximum number of concurrent processing tasks per batch
            
        Returns:
            List of processed VPN configurations
        """
        self.statistics_tracker.start_processing(len(sources))
        
        try:
            results = await self.batch_processor.process_sources_batch(
                sources, batch_size, max_concurrent
            )
            return results
        finally:
            self.statistics_tracker.end_processing()

    async def process_sources(
        self, sources: List[str], max_concurrent: int = 50
    ) -> List[VPNConfiguration]:
        """Process multiple sources concurrently (legacy method - use process_sources_batch for better performance).

        Args:
            sources: List of source URLs to process
            max_concurrent: Maximum number of concurrent processing tasks

        Returns:
            List of processed VPN configurations
        """
        # Use the new batch processing method for better performance
        return await self.process_sources_batch(sources, batch_size=10, max_concurrent=max_concurrent)

    def get_processing_statistics(self) -> dict:
        """Get comprehensive processing statistics.

        Returns:
            Dictionary containing processing statistics
        """
        return self.statistics_tracker.get_processing_statistics()

    def get_processing_summary(self) -> dict:
        """Get a human-readable processing summary.

        Returns:
            Dictionary containing processing summary information
        """
        return self.statistics_tracker.get_processing_summary()

    def reset_statistics(self) -> None:
        """Reset processing statistics."""
        self.statistics_tracker.reset_statistics()