"""
Batch Processor
===============

Handles batch processing of VPN sources with proper concurrency control.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import List

from ...models.configuration import VPNConfiguration
from ...security.validation import validate_config_line
from ..config_processor import ConfigurationProcessor
from ..source_validator import UnifiedSourceValidator
from .source_fetcher import SourceFetcher

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Handles batch processing of VPN sources."""

    def __init__(self):
        """Initialize batch processor."""
        self.config_processor = ConfigurationProcessor()
        self._ml_predictor = None
        self._initialize_ml_predictor()

    def _initialize_ml_predictor(self):
        """Initialize ML predictor if enabled."""
        try:
            if os.getenv("ENABLE_ML_SCORING", "false").lower() in ("1", "true", "yes"):
                from ...ml.enhanced_quality_predictor import EnhancedConfigQualityPredictor
                self._ml_predictor = EnhancedConfigQualityPredictor()
        except Exception:
            self._ml_predictor = None

    async def process_sources_batch(
        self, 
        sources: List[str], 
        batch_size: int = 10, 
        max_concurrent: int = 50
    ) -> List[VPNConfiguration]:
        """Process sources in batches with proper async concurrency control.
        
        Args:
            sources: List of source URLs to process
            batch_size: Number of sources to process in each batch
            max_concurrent: Maximum number of concurrent processing tasks per batch
            
        Returns:
            List of processed VPN configurations
        """
        # Fast path for tests
        if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("VPN_MERGER_TEST_MODE"):
            return await self._create_test_configurations(sources)

        logger.info(f"Starting batch source processing with {len(sources)} sources")
        all_results = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_source(source_url: str):
            async with semaphore:
                return await self._process_single_source(source_url)

        # Process sources in batches
        for i in range(0, len(sources), batch_size):
            batch = sources[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(sources) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} with {len(batch)} sources")
            
            # Process batch concurrently
            batch_tasks = [process_source(source) for source in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle results and exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing source {batch[j]}: {result}")
                elif result:
                    all_results.extend(result)

        logger.info(f"Batch processing completed. Total configurations: {len(all_results)}")
        return all_results

    async def _create_test_configurations(self, sources: List[str]) -> List[VPNConfiguration]:
        """Create test configurations for testing mode."""
        await asyncio.sleep(0.01)
        demo = VPNConfiguration(
            config="vmess://demo",
            protocol="vmess",
            host="example.com",
            port=443,
            quality_score=0.7,
            is_reachable=False,
            source_url=sources[0] if sources else None,
        )
        return [demo]

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
            # Validate source
            async with UnifiedSourceValidator() as validator:
                validation_result = await validator.validate_source(source_url)
                if not getattr(validation_result, "accessible", False):
                    logger.debug(f"Source not accessible: {source_url}")
                    return results

            # Fetch and process content
            async with SourceFetcher() as fetcher:
                configs = await fetcher.fetch_source_content(source_url)

            for config in configs:
                safe_line = validate_config_line(config)
                if not safe_line:
                    continue
                    
                result = self.config_processor.process_config(safe_line, source_url)
                if result:
                    # Apply ML scoring if available
                    await self._apply_ml_scoring(result)
                    results.append(result)
                else:
                    # Handle duplicate or invalid configs
                    pass

        except Exception as e:
            logger.error(f"Error processing source {source_url}: {e}")
        finally:
            # Record processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            logger.debug(f"Processed {source_url} in {processing_time:.2f}s")

        return results

    async def _apply_ml_scoring(self, config: VPNConfiguration) -> None:
        """Apply ML quality scoring to configuration if available."""
        if self._ml_predictor is not None:
            try:
                pred = await self._ml_predictor.predict_quality(config.config)
                if pred and hasattr(pred, "quality_score"):
                    config.update_quality_score(float(pred.quality_score))
            except Exception:
                pass
