#!/usr/bin/env python3
"""
VPN Merger Service Implementation
=================================

Service layer implementation for VPN merger functionality.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.interfaces import (
    SourceManagerInterface,
    SourceProcessorInterface,
    OutputManagerInterface,
    ConfigurationProcessorInterface
)
from ..core.merger import VPNSubscriptionMerger
from ..models.configuration import VPNConfiguration
from .base_service import BaseService

logger = logging.getLogger(__name__)


class VPNMergerService(BaseService):
    """Service implementation for VPN merger functionality."""
    
    def __init__(self, name: str = "vpn_merger", config: Optional[Dict[str, Any]] = None):
        """Initialize the VPN merger service.
        
        Args:
            name: Service name
            config: Service configuration
        """
        super().__init__(name, config)
        self.merger: Optional[VPNSubscriptionMerger] = None
        self.config_path = self.config.get("config_path", "config/sources.unified.yaml")
        self.max_concurrent = self.config.get("max_concurrent", 50)
        self.batch_size = self.config.get("batch_size", 10)
        
    async def _do_initialize(self) -> None:
        """Initialize the VPN merger service."""
        try:
            # Create merger instance
            self.merger = VPNSubscriptionMerger(config_path=self.config_path)
            
            # Update metrics
            self.update_metric("initialization_time", asyncio.get_event_loop().time())
            self.update_metric("config_path", str(self.config_path))
            self.update_metric("max_concurrent", self.max_concurrent)
            
            logger.info(f"VPN merger service initialized with config: {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize VPN merger service: {e}")
            raise
    
    async def _do_shutdown(self) -> None:
        """Shutdown the VPN merger service."""
        if self.merger:
            self.merger.reset()
            self.merger = None
        logger.info("VPN merger service shutdown")
    
    async def run_comprehensive_merge(self, max_concurrent: Optional[int] = None) -> List[VPNConfiguration]:
        """Run comprehensive merge operation.
        
        Args:
            max_concurrent: Maximum concurrent operations (uses service default if None)
            
        Returns:
            List of processed VPN configurations
        """
        if not self.merger:
            raise RuntimeError("Service not initialized")
        
        concurrent_limit = max_concurrent or self.max_concurrent
        
        try:
            logger.info(f"Starting comprehensive merge with {concurrent_limit} concurrent operations")
            
            # Update metrics
            self.update_metric("last_merge_start", asyncio.get_event_loop().time())
            self.update_metric("merge_count", self._metrics.get("merge_count", 0) + 1)
            
            results = await self.merger.run_comprehensive_merge(concurrent_limit)
            
            # Update metrics
            self.update_metric("last_merge_end", asyncio.get_event_loop().time())
            self.update_metric("last_merge_results_count", len(results))
            self.update_metric("total_configurations_processed", 
                             self._metrics.get("total_configurations_processed", 0) + len(results))
            
            logger.info(f"Comprehensive merge completed: {len(results)} configurations")
            return results
            
        except Exception as e:
            logger.error(f"Comprehensive merge failed: {e}")
            self.update_metric("merge_errors", self._metrics.get("merge_errors", 0) + 1)
            raise
    
    async def run_quick_merge(self, max_sources: int = 10) -> List[VPNConfiguration]:
        """Run quick merge operation.
        
        Args:
            max_sources: Maximum number of sources to process
            
        Returns:
            List of processed VPN configurations
        """
        if not self.merger:
            raise RuntimeError("Service not initialized")
        
        try:
            logger.info(f"Starting quick merge with {max_sources} sources")
            
            # Update metrics
            self.update_metric("last_quick_merge_start", asyncio.get_event_loop().time())
            self.update_metric("quick_merge_count", self._metrics.get("quick_merge_count", 0) + 1)
            
            results = await self.merger.run_quick_merge(max_sources)
            
            # Update metrics
            self.update_metric("last_quick_merge_end", asyncio.get_event_loop().time())
            self.update_metric("last_quick_merge_results_count", len(results))
            
            logger.info(f"Quick merge completed: {len(results)} configurations")
            return results
            
        except Exception as e:
            logger.error(f"Quick merge failed: {e}")
            self.update_metric("quick_merge_errors", self._metrics.get("quick_merge_errors", 0) + 1)
            raise
    
    async def validate_sources(self, sources: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """Validate sources.
        
        Args:
            sources: List of sources to validate (validates all if None)
            
        Returns:
            Dictionary mapping source URLs to validation results
        """
        if not self.merger:
            raise RuntimeError("Service not initialized")
        
        try:
            logger.info("Starting source validation")
            
            # Update metrics
            self.update_metric("last_validation_start", asyncio.get_event_loop().time())
            self.update_metric("validation_count", self._metrics.get("validation_count", 0) + 1)
            
            if sources is None:
                results = await self.merger.validate_sources_only()
            else:
                results = await self.merger.source_processor.validate_sources(sources)
            
            # Update metrics
            self.update_metric("last_validation_end", asyncio.get_event_loop().time())
            self.update_metric("last_validation_sources_count", len(results))
            
            # Count accessible sources
            accessible_count = sum(
                1 for result in results.values() 
                if result.get("accessible", False)
            )
            self.update_metric("last_validation_accessible_count", accessible_count)
            
            logger.info(f"Source validation completed: {accessible_count}/{len(results)} accessible")
            return results
            
        except Exception as e:
            logger.error(f"Source validation failed: {e}")
            self.update_metric("validation_errors", self._metrics.get("validation_errors", 0) + 1)
            raise
    
    async def save_results(self, results: List[VPNConfiguration], output_dir: Optional[Path] = None) -> Dict[str, str]:
        """Save results to various formats.
        
        Args:
            results: List of VPN configurations to save
            output_dir: Output directory (uses default if None)
            
        Returns:
            Dictionary mapping output types to file paths
        """
        if not self.merger:
            raise RuntimeError("Service not initialized")
        
        try:
            logger.info(f"Saving {len(results)} configurations")
            
            # Update metrics
            self.update_metric("last_save_start", asyncio.get_event_loop().time())
            self.update_metric("save_count", self._metrics.get("save_count", 0) + 1)
            
            # Set results in merger and save
            self.merger.results = results
            saved_files = self.merger.save_results(output_dir)
            
            # Update metrics
            self.update_metric("last_save_end", asyncio.get_event_loop().time())
            self.update_metric("last_save_files_count", len(saved_files))
            
            logger.info(f"Results saved to {len(saved_files)} files")
            return saved_files
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            self.update_metric("save_errors", self._metrics.get("save_errors", 0) + 1)
            raise
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics.
        
        Returns:
            Dictionary containing processing statistics
        """
        if not self.merger:
            return {}
        
        stats = self.merger.get_processing_statistics()
        stats.update(self._metrics)
        return stats
    
    def get_source_statistics(self) -> Dict[str, Any]:
        """Get source statistics.
        
        Returns:
            Dictionary containing source statistics
        """
        if not self.merger:
            return {}
        
        return self.merger.get_source_statistics()
    
    def get_available_sources(self) -> List[str]:
        """Get all available sources.
        
        Returns:
            List of available source URLs
        """
        if not self.merger:
            return []
        
        return self.merger.get_available_sources()
    
    def get_prioritized_sources(self) -> List[str]:
        """Get prioritized sources.
        
        Returns:
            List of prioritized source URLs
        """
        if not self.merger:
            return []
        
        return self.merger.get_prioritized_sources()
    
    def add_custom_sources(self, sources: List[str]) -> None:
        """Add custom sources.
        
        Args:
            sources: List of custom source URLs
        """
        if not self.merger:
            raise RuntimeError("Service not initialized")
        
        self.merger.add_custom_sources(sources)
        self.update_metric("custom_sources_added", 
                         self._metrics.get("custom_sources_added", 0) + len(sources))
        logger.info(f"Added {len(sources)} custom sources")
    
    def remove_sources(self, sources: List[str]) -> None:
        """Remove sources.
        
        Args:
            sources: List of source URLs to remove
        """
        if not self.merger:
            raise RuntimeError("Service not initialized")
        
        self.merger.remove_sources(sources)
        self.update_metric("sources_removed", 
                         self._metrics.get("sources_removed", 0) + len(sources))
        logger.info(f"Removed {len(sources)} sources")
    
    def get_results(self, limit: Optional[int] = None, min_quality: float = 0.0) -> List[VPNConfiguration]:
        """Get processed results with filtering.
        
        Args:
            limit: Maximum number of results to return
            min_quality: Minimum quality score threshold
            
        Returns:
            Filtered list of VPN configurations
        """
        if not self.merger:
            return []
        
        return self.merger.get_results(limit, min_quality)
    
    def reset(self) -> None:
        """Reset the service state."""
        if self.merger:
            self.merger.reset()
        
        # Reset metrics
        self._metrics.clear()
        self.update_metric("reset_count", self._metrics.get("reset_count", 0) + 1)
        
        logger.info("VPN merger service reset")
