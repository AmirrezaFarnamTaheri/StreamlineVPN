"""
StreamlineVPN Merger (Refactored)
==================================

Refactored main orchestration class for VPN configuration merging.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models.configuration import VPNConfiguration
from ..models.processing_result import ProcessingResult, ProcessingStatistics
from ..utils.logging import get_logger, log_performance
from .merger_base import BaseMerger
from .merger_processor import MergerProcessor
from .source_manager import SourceManager
from .config_processor import ConfigurationProcessor
from .output_manager import OutputManager

logger = get_logger(__name__)


class StreamlineVPNMerger(BaseMerger):
    """Main StreamlineVPN merger class with comprehensive processing capabilities."""

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
        from ..security.manager import SecurityManager
        self.security_manager = SecurityManager()

        # Initialize core managers
        self.source_manager = SourceManager(self.config_path, self.security_manager)
        self.config_processor = ConfigurationProcessor()
        self.output_manager = OutputManager()

        # Initialize processor
        self.processor = MergerProcessor(self)

        # Loaded source URLs
        self.sources: List[str] = []

        logger.info(f"StreamlineVPN merger initialized with config: {config_path}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()

    async def process_all(
        self,
        output_dir: str = "output",
        formats: Optional[List[str]] = None
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
            unique_configs = await self.processor.deduplicate_configurations(all_configs)
            
            # Apply enhancements
            enhanced_configs = await self.processor.apply_enhancements(unique_configs)
            
            # Store results
            self.results = enhanced_configs
            
            # Update statistics
            self._update_statistics(
                total_sources=len(self.sources),
                total_configs=len(enhanced_configs),
                processing_duration=(datetime.now() - start_time).total_seconds()
            )

            # Generate outputs
            await self.save_results(output_dir, formats)

            # Log performance
            duration = (datetime.now() - start_time).total_seconds()
            log_performance("process_all", duration, 
                          sources_processed=len(self.sources),
                          configs_found=len(enhanced_configs))

            return {
                "success": True,
                "sources_processed": len(self.sources),
                "configurations_found": len(enhanced_configs),
                "processing_duration": duration,
                "statistics": self.statistics.to_dict()
            }

        except Exception as e:
            logger.error(f"Error in process_all: {e}")
            return {
                "success": False,
                "error": str(e),
                "sources_processed": len(self.sources) if self.sources else 0,
                "configurations_found": len(self.results)
            }

    async def _load_sources(self) -> None:
        """Load sources from configuration."""
        try:
            # Get active source URLs from source manager
            if self.source_manager is None:
                self.sources = []
                return
            self.sources = await self.source_manager.get_active_sources()
            logger.info(f"Loaded {len(self.sources)} active sources")
        except Exception as e:
            logger.error(f"Error loading sources: {e}")
            self.sources = []

    async def get_source_statistics(self) -> Dict[str, Any]:
        """Get source statistics.
        
        Returns:
            Source statistics dictionary
        """
        if not self.source_manager:
            return {}
        
        return {
            "total_sources": len(self.sources),
            "enabled_sources": len([s for s in self.sources if s.enabled]),
            "disabled_sources": len([s for s in self.sources if not s.enabled]),
            "source_types": self._get_source_type_counts(),
            "source_tiers": self._get_source_tier_counts()
        }

    def _get_source_type_counts(self) -> Dict[str, int]:
        """Get counts by source type."""
        counts = {}
        for source in self.sources:
            source_type = getattr(source, 'type', 'unknown')
            counts[source_type] = counts.get(source_type, 0) + 1
        return counts

    def _get_source_tier_counts(self) -> Dict[str, int]:
        """Get counts by source tier."""
        counts = {}
        for source in self.sources:
            source_tier = getattr(source, 'tier', 'unknown')
            counts[source_tier] = counts.get(source_tier, 0) + 1
        return counts

    async def blacklist_source(self, source_url: str, reason: str = "") -> bool:
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
            "total_configurations": len(self.results),
            "statistics": self.statistics.to_dict(),
            "cache_enabled": self.cache_enabled,
            "max_concurrent": self.max_concurrent
        }
