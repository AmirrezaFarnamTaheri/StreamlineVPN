"""
VPN Subscription Merger
======================

Main orchestration class for VPN subscription merging and processing.
"""

import logging
from pathlib import Path

from ..models.configuration import VPNConfiguration
from .output import OutputManager
from .source_manager import SourceManager
from .source_processor import SourceProcessor

logger = logging.getLogger(__name__)

# Global configuration constants
DEFAULT_CONCURRENT_LIMIT = 50


class VPNSubscriptionMerger:
    """Main VPN subscription merger class with comprehensive processing capabilities.

    This class orchestrates the entire VPN subscription merging process,
    including source management, configuration processing, and output generation.

    Attributes:
        source_manager: Manages VPN subscription sources
        source_processor: Processes and validates configurations
        output_manager: Handles output formatting and file saving
        results: List of processed VPN configurations
    """

    def __init__(self, config_path: str | Path = "config/sources.unified.yaml"):
        """Initialize the VPN subscription merger.

        Args:
            config_path: Path to the configuration file
        """
        self.source_manager = SourceManager(config_path)
        self.source_processor = SourceProcessor()
        self.config_processor = self.source_processor.config_processor  # Alias for compatibility
        self.output_manager = OutputManager()
        self.results: list[VPNConfiguration] = []
        # Minimal stats expected by tests
        self.stats = {"total_sources": 0}

    async def run_comprehensive_merge(
        self, max_concurrent: int = DEFAULT_CONCURRENT_LIMIT
    ) -> list[VPNConfiguration]:
        """Run comprehensive merge operation with concurrency control.

        Args:
            max_concurrent: Maximum number of concurrent source processing tasks

        Returns:
            List of processed VPN configurations

        Raises:
            ValueError: If max_concurrent is invalid
        """
        if max_concurrent <= 0:
            raise ValueError("max_concurrent must be positive")

        logger.info("Starting comprehensive VPN subscription merge")

        # Get prioritized sources
        sources = self.source_manager.get_prioritized_sources()

        # Process sources using the source processor
        async with self.source_processor:
            self.results = await self.source_processor.process_sources(sources, max_concurrent)

        logger.info(f"Merge completed: {len(self.results)} valid configurations")
        return self.results

    async def run_quick_merge(self, max_sources: int = 10) -> list[VPNConfiguration]:
        """Run a quick merge with limited sources for testing.

        Args:
            max_sources: Maximum number of sources to process

        Returns:
            List of processed VPN configurations
        """
        logger.info(f"Starting quick merge with {max_sources} sources")

        # Get a subset of sources
        all_sources = self.source_manager.get_prioritized_sources()
        sources = all_sources[:max_sources]

        # Process sources with concurrency scaled to requested size
        scaled_concurrency = max(10, min(DEFAULT_CONCURRENT_LIMIT, int(max_sources)))
        async with self.source_processor:
            self.results = await self.source_processor.process_sources(
                sources, max_concurrent=scaled_concurrency
            )

        logger.info(f"Quick merge completed: {len(self.results)} valid configurations")
        return self.results

    async def validate_sources_only(self) -> dict[str, dict]:
        """Validate all sources without processing configurations.

        Returns:
            Dictionary mapping source URLs to validation results
        """
        logger.info("Starting source validation")

        sources = self.source_manager.get_all_sources()

        async with self.source_processor:
            validation_results = await self.source_processor.validate_sources(sources)

        # Count results
        accessible_count = sum(
            1 for result in validation_results.values() if result.get("accessible", False)
        )
        logger.info(f"Validation completed: {accessible_count}/{len(sources)} sources accessible")

        return validation_results

    def save_results(self, output_dir: str | Path | None = None) -> dict[str, str]:
        """Save results to various output formats.

        Args:
            output_dir: Directory to save output files (uses default if None)

        Returns:
            Dictionary mapping output types to file paths

        Raises:
            ValueError: If no results to save
        """
        if not self.results:
            raise ValueError("No results to save. Run merge operation first.")

        return self.output_manager.save_results(self.results, output_dir)

    def get_results(
        self, limit: int | None = None, min_quality: float = 0.0
    ) -> list[VPNConfiguration]:
        """Get processed results with optional filtering.

        Args:
            limit: Maximum number of results to return
            min_quality: Minimum quality score threshold

        Returns:
            Filtered list of VPN configurations
        """
        filtered_results = [r for r in self.results if r.quality_score >= min_quality]

        if limit:
            filtered_results = filtered_results[:limit]

        return filtered_results

    def get_processing_statistics(self) -> dict:
        """Get comprehensive processing statistics.

        Returns:
            Dictionary containing processing statistics
        """
        return self.source_processor.get_processing_statistics()

    def get_processing_summary(self) -> dict[str, int | float | str]:
        """Get a human-readable processing summary.

        Returns:
            Dictionary containing processing summary information
        """
        return self.source_processor.get_processing_summary()

    def get_source_statistics(self) -> dict:
        """Get source management statistics.

        Returns:
            Dictionary containing source statistics
        """
        return self.source_manager.get_statistics()

    def reset(self) -> None:
        """Reset the merger state."""
        self.results.clear()
        self.source_processor.reset_statistics()
        logger.info("Merger state reset")

    def add_custom_sources(self, sources: list[str]) -> None:
        """Add custom sources to the source manager.

        Args:
            sources: List of custom source URLs to add
        """
        self.source_manager.add_custom_sources(sources)
        logger.info(f"Added {len(sources)} custom sources")

    def remove_sources(self, sources: list[str]) -> None:
        """Remove sources from the source manager.

        Args:
            sources: List of source URLs to remove
        """
        self.source_manager.remove_sources(sources)
        logger.info(f"Removed {len(sources)} sources")

    def get_available_sources(self) -> list[str]:
        """Get all available sources.

        Returns:
            List of all available source URLs
        """
        return self.source_manager.get_all_sources()

    def get_prioritized_sources(self) -> list[str]:
        """Get prioritized sources.

        Returns:
            List of prioritized source URLs
        """
        return self.source_manager.get_prioritized_sources()

    def deduplicate(self, data: list[str]) -> list[str]:
        """Remove duplicate entries from a list.

        Args:
            data: List of strings to deduplicate

        Returns:
            Deduplicated list
        """
        seen = set()
        result = []
        for item in data:
            if item and item.strip() and item not in seen:
                seen.add(item)
                result.append(item)
        return result

    def score_and_sort(self, lines: list[str]) -> list[str]:
        """Score and sort configuration lines.

        Args:
            lines: List of configuration lines

        Returns:
            Sorted list of configuration lines
        """
        # Simple scoring based on line length (shorter = better)
        scored_lines = [(line, max(0.0, 100.0 - float(len(line)))) for line in lines if line]
        scored_lines.sort(key=lambda x: x[1], reverse=True)
        return [line for line, score in scored_lines]

    async def validate_sources(self, sources: list[str], min_score: float = 0.0) -> list[str]:
        """Validate sources and return valid ones.

        Args:
            sources: List of source URLs to validate
            min_score: Minimum reliability score threshold

        Returns:
            List of valid source URLs
        """
        try:
            async with self.source_processor:
                validation_results = await self.source_processor.validate_sources(sources)

            valid_sources = []
            for url, result in validation_results.items():
                if (
                    result.get("accessible", False)
                    and result.get("reliability_score", 0.0) >= min_score
                ):
                    valid_sources.append(url)

            return valid_sources
        except (ValueError, TypeError, RuntimeError) as e:
            logger.warning(f"Source validation failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during source validation: {e}")
            return []
