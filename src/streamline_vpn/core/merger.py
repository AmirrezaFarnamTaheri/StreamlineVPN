"""
StreamlineVPN Merger
====================

Main orchestration class for VPN configuration merging.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from ..utils.logging import get_logger, log_performance
from .merger_base import BaseMerger
from .merger_processor import MergerProcessor
from .source_manager import SourceManager
from .config_processor import ConfigurationProcessor
from .output_manager import OutputManager
from ..security.manager import SecurityManager
from ..fetcher.service import FetcherService

logger = get_logger(__name__)


class StreamlineVPNMerger(BaseMerger):
    """Main StreamlineVPN merger class."""

    def __init__(
        self,
        config_path: str = "config/sources.yaml",
        cache_enabled: bool = True,
        max_concurrent: int = 50,
    ):
        """Initialize the StreamlineVPN merger.

        Args:
            config_path: Path to the configuration file
            cache_enabled: Whether to enable caching
            max_concurrent: Maximum concurrent processing tasks
        """
        super().__init__(config_path, cache_enabled, max_concurrent)

        # Initialize security manager
        self.security_manager = SecurityManager()

        # Initialize fetcher service
        self.fetcher_service = FetcherService(max_concurrent=max_concurrent)

        # Initialize core managers
        self.source_manager = SourceManager(
            self.config_path, self.security_manager, self.fetcher_service
        )
        self.config_processor = ConfigurationProcessor()
        self.output_manager = OutputManager()

        # Initialize processor
        self.processor = MergerProcessor(self)

        # Loaded source URLs
        self.sources: List[str] = []

        logger.info(
            f"StreamlineVPN merger initialized with config: {config_path}"
        )

    async def initialize(self):
        """Initialize the merger."""
        await super().initialize()
        await self.fetcher_service.initialize()

    async def shutdown(self):
        """Shutdown the merger and save performance data."""
        if self.source_manager:
            logger.info("Saving source performance data...")
            await self.source_manager.save_performance_data()
        await self.fetcher_service.close()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()

    def __del__(self):  # pragma: no cover - best-effort cleanup
        try:
            # Ensure fetcher session is closed to avoid unclosed session warnings
            import asyncio

            async def _close():
                try:
                    await self.fetcher_service.close()
                except Exception:
                    pass

            # Try to close regardless of loop state
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                loop.create_task(_close())
            else:
                try:
                    asyncio.run(_close())
                except Exception:
                    pass
        except Exception:
            pass

    async def process_all(
        self, output_dir: str = "output", formats: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Process all sources and generate outputs.

        Args:
            output_dir: Output directory for results
            formats: List of output formats to generate

        Returns:
            Dictionary with processing results and statistics
        """
        start_time = datetime.now()
        logger.info("Starting comprehensive VPN configuration processing...")

        try:
            # Load sources if not already loaded
            if not self.sources:
                await self._load_sources()

            if not self.sources:
                logger.warning("No sources found to process")
                return {"success": False, "error": "No sources found"}

            # Process sources using processor
            all_configs = await self.processor.process_sources(self.sources)

            # Deduplicate configurations
            unique_configs = await self.processor.deduplicate_configurations(
                all_configs
            )

            # Apply enhancements
            enhanced_configs = await self.processor.apply_enhancements(
                unique_configs
            )

            # Store results for downstream consumers (saving/statistics)
            self.results = enhanced_configs

            # Update statistics
            self._update_statistics(
                total_sources=len(self.sources),
                total_configs=len(self.results),
                processing_duration=(
                    datetime.now() - start_time
                ).total_seconds(),
            )

            # Generate outputs
            try:
                await self.save_results(output_dir, formats)
            except Exception as save_error:
                logger.error(f"Failed to save results: {save_error}")
                # Continue without failing the entire process

            # Log performance
            duration = (datetime.now() - start_time).total_seconds()
            log_performance(
                "process_all",
                duration,
                sources_processed=len(self.sources),
                configs_found=len(self.results),
            )

            return {
                "success": True,
                "sources_processed": len(self.sources),
                "configurations_found": len(self.results),
                "processing_duration": duration,
                "statistics": self.statistics.to_dict(),
            }

        except Exception as e:
            logger.error(f"Error in process_all: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "exception": e.__class__.__name__,
                "sources_processed": int(
                    len(self.sources) if self.sources else 0
                ),
                "configurations_found": 0,
            }

    async def _load_sources(self) -> None:
        """Load sources from configuration."""
        try:
            # Get active source URLs from source manager
            if self.source_manager is None:
                logger.warning("Source manager not initialized")
                self.sources = []
                return
            self.sources = await self.source_manager.get_active_sources()
            logger.info(f"Loaded {len(self.sources)} active sources")
        except Exception as e:
            logger.error(f"Error loading sources: {e}", exc_info=True)
            self.sources = []

    async def get_source_statistics(self) -> Dict[str, Any]:
        """Get source statistics.

        Returns:
            Source statistics dictionary
        """
        if not self.source_manager:
            return {}

        all_sources = self.source_manager.sources.values()

        return {
            "total_sources": len(all_sources),
            "enabled_sources": len([s for s in all_sources if s.enabled]),
            "disabled_sources": len([s for s in all_sources if not s.enabled]),
            "source_types": self._get_source_type_counts(all_sources),
            "source_tiers": self._get_source_tier_counts(all_sources),
        }

    def _get_source_type_counts(self, sources: List[Any]) -> Dict[str, int]:
        """Get counts by source type."""
        counts = {}
        for source in sources:
            # Assuming 'kind' or 'type' exists on the source object
            source_type = getattr(source, "kind", "unknown")
            counts[source_type] = counts.get(source_type, 0) + 1
        return counts

    def _get_source_tier_counts(self, sources: List[Any]) -> Dict[str, int]:
        """Get counts by source tier."""
        counts = {}
        for source in sources:
            tier_value = (
                source.tier.value
                if hasattr(source, "tier") and hasattr(source.tier, "value")
                else "unknown"
            )
            counts[tier_value] = counts.get(tier_value, 0) + 1
        return counts

    async def blacklist_source(
        self, source_url: str, reason: str = ""
    ) -> bool:
        """Blacklist a source.

        Args:
            source_url: URL of source to blacklist
            reason: Reason for blacklisting

        Returns:
            True if blacklisted successfully
        """
        try:
            if self.source_manager:
                self.source_manager.blacklist_source(source_url, reason)
                logger.info(f"Blacklisted source: {source_url} - {reason}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error blacklisting source {source_url}: {e}")
            return False

    async def whitelist_source(self, source_url: str) -> bool:
        """Remove source from blacklist.

        Args:
            source_url: URL of source to whitelist

        Returns:
            True if whitelisted successfully
        """
        try:
            if self.source_manager:
                self.source_manager.whitelist_source(source_url)
                logger.info(f"Whitelisted source: {source_url}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error whitelisting source {source_url}: {e}")
            return False

    def get_processing_summary(self) -> Dict[str, Any]:
        """Get processing summary.

        Returns:
            Processing summary dictionary
        """
        return {
            "total_sources": len(self.sources),
            "statistics": self.statistics.to_dict(),
            "cache_enabled": self.cache_enabled,
            "max_concurrent": self.max_concurrent,
        }

    async def get_configurations(self) -> List[Any]:
        """Get all configurations.
        
        Returns:
            List of VPN configurations
        """
        if hasattr(self, 'results') and self.results:
            return self.results
        return []

    async def get_all_configurations(self) -> List[Dict[str, Any]]:
        """Get all configurations as dictionaries.
        
        Returns:
            List of configuration dictionaries
        """
        try:
            configs = await self.get_configurations()
            return [config.to_dict() if hasattr(config, 'to_dict') else config for config in configs]
        except Exception as e:
            logger.error(f"Failed to get all configurations: {e}", exc_info=True)
            return []

    async def check_source_status(self, source_url: str) -> str:
        """Check the status of a specific source.
        
        Args:
            source_url: URL of the source to check
            
        Returns:
            Status string ('active', 'inactive', 'error', 'unknown')
        """
        try:
            # Check if source is in our sources list
            for source in self.sources:
                if hasattr(source, 'url') and source.url == source_url:
                    return "active"
            return "unknown"
        except Exception as e:
            logger.error(f"Failed to check source status for {source_url}: {e}", exc_info=True)
            return "error"

    async def count_source_configurations(self, source_url: str) -> int:
        """Count configurations from a specific source.
        
        Args:
            source_url: URL of the source to count
            
        Returns:
            Number of configurations from the source
        """
        try:
            configs = await self.get_configurations()
            count = 0
            for config in configs:
                if hasattr(config, 'source_url') and config.source_url == source_url:
                    count += 1
            return count
        except Exception as e:
            logger.error(f"Failed to count configurations for {source_url}: {e}", exc_info=True)
            return 0

    async def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            if hasattr(self, 'statistics') and self.statistics:
                return self.statistics.to_dict()
            return {
                "total_configs": len(await self.get_configurations()),
                "successful_sources": len(self.sources),
                "success_rate": 1.0,
                "avg_quality": 0.5,
                "last_update": None,
                "protocols": {},
                "locations": {}
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}", exc_info=True)
            return {}

    async def clear_cache(self) -> None:
        """Clear all caches."""
        try:
            if hasattr(self, 'cache_manager') and self.cache_manager:
                await self.cache_manager.clear()
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}", exc_info=True)

    async def save_results(self, output_dir: str, formats: Optional[List[str]] = None) -> None:
        """Save processing results to output directory.
        
        Args:
            output_dir: Output directory path
            formats: List of output formats
        """
        try:
            if hasattr(self, 'results') and self.results:
                await self.output_manager.save_configurations(
                    self.results, output_dir, formats
                )
                logger.info(f"Results saved to {output_dir}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}", exc_info=True)
