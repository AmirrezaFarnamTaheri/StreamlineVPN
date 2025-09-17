"""
Merger Processor
================

Processing logic for VPN configuration merging.
"""

from typing import Any, List

from ..models.configuration import VPNConfiguration
from ..utils.helpers import run_concurrently
from ..utils.logging import get_logger

logger = get_logger(__name__)


class MergerProcessor:
    """Handles VPN configuration processing logic."""

    def __init__(self, merger):
        """Initialize processor.

        Args:
            merger: Parent merger instance
        """
        self.merger = merger

    async def process_sources(
        self, sources: List[Any]
    ) -> tuple[List[VPNConfiguration], int]:
        """Process all sources and return configurations and success count.

        Args:
            sources: List of sources to process

        Returns:
            A tuple containing:
                - List of processed configurations
                - Count of successfully processed sources
        """
        logger.info("Processing %d sources", len(sources))

        # Create processing tasks
        tasks = [self._process_single_source(source) for source in sources]

        # Execute tasks concurrently
        results = await run_concurrently(tasks, limit=self.merger.max_concurrent)

        # Flatten results and count successes
        all_configs: List[VPNConfiguration] = []
        successful_sources_count = 0
        for configs, success in results:
            if success:
                successful_sources_count += 1
            if configs:
                all_configs.extend(configs)

        logger.info(
            f"Processed {len(all_configs)} configurations from "
            f"{successful_sources_count}/{len(sources)} successful sources"
        )
        return all_configs, successful_sources_count

    async def _process_single_source(
        self, source: Any
    ) -> tuple[List[VPNConfiguration], bool]:
        """Process a single source.

        Args:
            source: Source to process

        Returns:
            A tuple containing:
                - List of configurations from the source
                - Boolean indicating if the processing was successful
        """
        source_url = source.get("url") if isinstance(source, dict) else source
        if not source_url:
            logger.error("Skipping source with no URL: %s", source)
            return [], False

        try:
            # Fetch from source URL
            fetch_result = await self.merger.source_manager.fetch_source(source_url)
            if not fetch_result or not fetch_result.success:
                logger.warning(
                    "Failed to fetch or no content from source %s", source_url
                )
                try:
                    await self.merger.source_manager.update_source_performance(
                        source_url=source_url,
                        success=False,
                        config_count=0,
                        response_time=(
                            fetch_result.response_time if fetch_result else 0.0
                        ),
                    )
                except Exception as perf_error:
                    logger.error(
                        "Failed to update source performance for %s: %s",
                        source_url,
                        perf_error,
                    )
                return [], False

            # Parse each configuration line
            parsed_configs: List[VPNConfiguration] = []
            for line in fetch_result.configs:
                try:
                    parser = self.merger.config_processor.parser
                    cfg = parser.parse_configuration(line)
                    if cfg:
                        cfg.metadata["source"] = source_url
                        parsed_configs.append(cfg)
                except Exception as parse_error:
                    logger.debug(
                        "Failed to parse configuration line from %s: %s",
                        source_url,
                        parse_error,
                    )
                    continue

            # Update source performance
            try:
                await self.merger.source_manager.update_source_performance(
                    source_url=source_url,
                    success=True,
                    config_count=len(parsed_configs),
                    response_time=fetch_result.response_time,
                )
            except Exception as perf_error:
                logger.error(
                    "Failed to update source performance for %s: %s",
                    source_url,
                    perf_error,
                )

            return parsed_configs, True

        except Exception as e:
            logger.error(f"Error processing source {source_url}: {e}", exc_info=True)
            try:
                await self.merger.source_manager.update_source_performance(
                    source_url=source_url,
                    success=False,
                    config_count=0,
                    response_time=0.0,
                )
            except Exception as perf_error:
                logger.error(
                    "Failed to update source performance for %s: %s",
                    source_url,
                    perf_error,
                )
            return [], False

    async def deduplicate_configurations(
        self, configs: List[VPNConfiguration]
    ) -> List[VPNConfiguration]:
        """Deduplicate configurations.

        Args:
            configs: List of configurations to deduplicate

        Returns:
            List of unique configurations
        """
        logger.info("Deduplicating %d configurations", len(configs))

        unique_configs = self.merger.config_processor.deduplicate_configurations(
            configs
        )

        logger.info(f"Deduplicated to {len(unique_configs)} unique configurations")
        return unique_configs

    async def apply_enhancements(
        self, configs: List[VPNConfiguration]
    ) -> List[VPNConfiguration]:
        """Apply ML and geographic enhancements.

        Args:
            configs: List of configurations to enhance

        Returns:
            Enhanced configurations
        """
        logger.info("Applying enhancements to %d configurations", len(configs))

        # Apply ML quality prediction if available
        if hasattr(self.merger, "ml_predictor") and self.merger.ml_predictor:
            try:
                configs = await self.merger.ml_predictor.predict_and_sort(configs)
                logger.info("Applied ML quality prediction")
            except Exception as e:
                logger.warning("ML prediction failed: %s", e)

        # Apply geographic optimization if available
        if hasattr(self.merger, "geo_optimizer") and self.merger.geo_optimizer:
            try:
                configs = await self.merger.geo_optimizer.optimize_configurations(
                    configs
                )
                logger.info("Applied geographic optimization")
            except Exception as e:
                logger.warning("Geographic optimization failed: %s", e)

        return configs
