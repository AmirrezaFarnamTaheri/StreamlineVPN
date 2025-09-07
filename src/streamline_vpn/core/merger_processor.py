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
    ) -> List[VPNConfiguration]:
        """Process all sources and return configurations.

        Args:
            sources: List of sources to process

        Returns:
            List of processed configurations
        """
        logger.info(f"Processing {len(sources)} sources")

        # Create processing tasks
        tasks = [self._process_single_source(source) for source in sources]

        # Execute tasks concurrently
        results = await run_concurrently(
            tasks, limit=self.merger.max_concurrent
        )

        # Flatten results
        all_configs = []
        for configs in results:
            if configs:
                all_configs.extend(configs)

        logger.info(
            f"Processed {len(all_configs)} configurations from "
            f"{len(sources)} sources"
        )
        return all_configs

    async def _process_single_source(
        self, source: Any
    ) -> List[VPNConfiguration]:
        """Process a single source.

        Args:
            source: Source to process

        Returns:
            List of configurations from source
        """
        try:
            # Fetch from source URL
            fetch_result = await self.merger.source_manager.fetch_source(
                source
            )
            if not fetch_result or not fetch_result.success:
                logger.warning(
                    "Failed to fetch or no content from source " f"{source}"
                )
                # Update performance as failed
                await self.merger.source_manager.update_source_performance(
                    source_url=source,
                    success=False,
                    config_count=0,
                    response_time=(
                        fetch_result.response_time if fetch_result else 0.0
                    ),
                )
                return []

            # Parse each configuration line
            parsed_configs: List[VPNConfiguration] = []
            for line in fetch_result.configs:
                security_analysis = (
                    self.merger.security_manager.analyze_configuration(line)
                )
                if not security_analysis["is_safe"]:
                    logger.warning(
                        "Skipping unsafe configuration from "
                        f"{source}: {line}"
                    )
                    continue

                parser = self.merger.config_processor.parser
                cfg = parser.parse_configuration(line)
                if cfg:
                    parsed_configs.append(cfg)

            # Update source performance
            await self.merger.source_manager.update_source_performance(
                source_url=source,
                success=True,
                config_count=len(parsed_configs),
                response_time=fetch_result.response_time,
            )

            return parsed_configs

        except Exception as e:
            logger.error(
                f"Error processing source "
                f"{getattr(source, 'name', source)}: {e}"
            )
            try:
                await self.merger.source_manager.update_source_performance(
                    source_url=source,
                    success=False,
                    config_count=0,
                    response_time=0.0,
                )
            except Exception:
                pass
            return []

    async def deduplicate_configurations(
        self, configs: List[VPNConfiguration]
    ) -> List[VPNConfiguration]:
        """Deduplicate configurations.

        Args:
            configs: List of configurations to deduplicate

        Returns:
            List of unique configurations
        """
        logger.info(f"Deduplicating {len(configs)} configurations")

        unique_configs = (
            self.merger.config_processor.deduplicate_configurations(configs)
        )

        logger.info(
            f"Deduplicated to {len(unique_configs)} unique configurations"
        )
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
        logger.info(f"Applying enhancements to {len(configs)} configurations")

        # Apply ML quality prediction if available
        if hasattr(self.merger, "ml_predictor") and self.merger.ml_predictor:
            try:
                configs = await self.merger.ml_predictor.predict_and_sort(
                    configs
                )
                logger.info("Applied ML quality prediction")
            except Exception as e:
                logger.warning(f"ML prediction failed: {e}")

        # Apply geographic optimization if available
        if hasattr(self.merger, "geo_optimizer") and self.merger.geo_optimizer:
            try:
                configs = (
                    await self.merger.geo_optimizer.optimize_configurations(
                        configs
                    )
                )
                logger.info("Applied geographic optimization")
            except Exception as e:
                logger.warning(f"Geographic optimization failed: {e}")

        return configs
