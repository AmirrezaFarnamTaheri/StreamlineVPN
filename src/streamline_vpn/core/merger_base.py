"""
Base Merger Class
=================

Base class for VPN configuration merging functionality.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any

from ..models.configuration import VPNConfiguration
from ..models.processing_result import ProcessingResult, ProcessingStatistics
from ..utils.logging import get_logger
from .source_manager import SourceManager
from .config_processor import ConfigurationProcessor
from .output_manager import OutputManager
from .cache_manager import CacheManager


logger = get_logger(__name__)


class BaseMerger:
    """Base merger class with common functionality."""

    def __init__(
        self,
        config_path: str = "config/sources.yaml",
        cache_enabled: bool = True,
        max_concurrent: int = 50,
    ):
        """Initialize base merger.

        Args:
            config_path: Path to configuration file
            cache_enabled: Whether to enable caching
            max_concurrent: Maximum concurrent operations
        """
        self.config_path = config_path
        self.cache_enabled = cache_enabled
        self.max_concurrent = max_concurrent

        # Initialize components
        self.source_manager: Optional[SourceManager] = None
        self.config_processor: Optional[ConfigurationProcessor] = None
        self.output_manager: Optional[OutputManager] = None
        self.cache_manager: Optional[CacheManager] = None

        # Statistics
        self.statistics = ProcessingStatistics()

        # Results
        self.results: List[VPNConfiguration] = []
        self.processing_results: List[ProcessingResult] = []

    async def initialize(self) -> None:
        """Initialize merger components."""
        if not all(
            [self.source_manager, self.config_processor, self.output_manager]
        ):
            raise RuntimeError(
                "Managers must be initialized before calling initialize"
            )

        if self.cache_enabled:
            from ..settings import get_settings

            settings = get_settings()
            self.cache_manager = CacheManager(redis_nodes=settings.redis.nodes)
            # The redis client is initialized in the constructor, no need to connect.

        logger.info("Merger components initialized")

    async def shutdown(self) -> None:
        """Shutdown merger components."""
        if self.cache_manager and hasattr(self.cache_manager, "disconnect"):
            try:
                await self.cache_manager.disconnect()
            except Exception as e:
                logger.error(f"Failed to disconnect from cache manager: {e}")
        logger.info("Merger components shutdown")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics.

        Returns:
            Statistics dictionary
        """
        return self.statistics.to_dict()

    async def get_configurations(self) -> List[VPNConfiguration]:
        """Get processed configurations.

        Returns:
            List of VPN configurations
        """
        return self.results.copy()

    async def clear_cache(self) -> None:
        """Clear all caches."""
        if self.cache_manager:
            # Clear all cache tiers
            if hasattr(self.cache_manager, "clear"):
                await self.cache_manager.clear()
        logger.info("Cache cleared")

    async def save_results(
        self, output_dir: str, formats: Optional[List[str]] = None
    ) -> None:
        """Save processing results.

        Args:
            output_dir: Output directory path
            formats: Output formats to generate
        """
        if not self.results:
            logger.warning("No results to save")
            return

        if not self.output_manager:
            raise RuntimeError("Output manager not initialized")

        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            if formats is None:
                formats = ["json", "clash", "singbox"]

            # Save configurations via async output manager API
            await self.output_manager.save_configurations(
                self.results,
                str(output_path),
                formats,
            )

            # Save statistics
            stats_file = output_path / "statistics.json"
            try:
                with open(stats_file, "w") as f:
                    f.write(self.statistics.to_json())
            except Exception as e:
                logger.error(f"Failed to save statistics: {e}")

            logger.info(f"Results saved to {output_dir}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}", exc_info=True)
            raise

    def save_results_sync(
        self, output_dir: str, formats: Optional[List[str]] = None
    ) -> None:
        """Synchronous wrapper to save results using the output manager."""
        if not self.results:
            logger.warning("No results to save")
            return
        if not self.output_manager:
            raise RuntimeError("Output manager not initialized")
        try:
            self.output_manager.save_configurations_sync(
                self.results, output_dir, formats
            )
        except Exception as e:
            logger.error(f"Failed to save results synchronously: {e}", exc_info=True)
            raise

    def _update_statistics(self, **kwargs) -> None:
        """Update statistics with new values.

        Args:
            **kwargs: Statistics to update
        """
        for key, value in kwargs.items():
            if hasattr(self.statistics, key):
                setattr(self.statistics, key, value)
