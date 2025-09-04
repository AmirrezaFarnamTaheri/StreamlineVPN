"""
Statistics Tracker
==================

Tracks processing statistics and performance metrics.
"""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class StatisticsTracker:
    """Tracks processing statistics and performance metrics."""

    def __init__(self):
        """Initialize statistics tracker."""
        self.processing_stats = {
            "total_sources": 0,
            "processed_sources": 0,
            "total_configs": 0,
            "valid_configs": 0,
            "duplicate_configs": 0,
            "start_time": None,
            "end_time": None,
        }
        self.source_processing_times: Dict[str, float] = {}
        self.error_counts: Dict[str, int] = {}

    def start_processing(self, total_sources: int) -> None:
        """Start tracking processing statistics.
        
        Args:
            total_sources: Total number of sources to process
        """
        self.processing_stats["start_time"] = datetime.now()
        self.processing_stats["total_sources"] = total_sources
        logger.info(f"Started processing {total_sources} sources")

    def end_processing(self) -> None:
        """End tracking processing statistics."""
        self.processing_stats["end_time"] = datetime.now()
        logger.info("Processing completed")

    def record_source_processed(self, source_url: str, processing_time: float) -> None:
        """Record that a source was processed.
        
        Args:
            source_url: URL of the processed source
            processing_time: Time taken to process the source in seconds
        """
        self.processing_stats["processed_sources"] += 1
        self.source_processing_times[source_url] = processing_time

    def record_config_processed(self, is_valid: bool = True) -> None:
        """Record that a configuration was processed.
        
        Args:
            is_valid: Whether the configuration was valid
        """
        self.processing_stats["total_configs"] += 1
        if is_valid:
            self.processing_stats["valid_configs"] += 1
        else:
            self.processing_stats["duplicate_configs"] += 1

    def record_error(self, source_url: str) -> None:
        """Record an error for a source.
        
        Args:
            source_url: URL of the source that had an error
        """
        self.error_counts[source_url] = self.error_counts.get(source_url, 0) + 1

    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics.

        Returns:
            Dictionary containing processing statistics
        """
        stats = self.processing_stats.copy()
        
        # Calculate success rate
        if stats["total_sources"] > 0:
            stats["success_rate"] = stats["processed_sources"] / stats["total_sources"]
        else:
            stats["success_rate"] = 0.0

        # Calculate processing duration
        stats["processing_duration"] = (
            (stats["end_time"] - stats["start_time"]).total_seconds()
            if stats["start_time"] and stats["end_time"]
            else None
        )

        # Add performance metrics
        stats["avg_processing_time"] = (
            sum(self.source_processing_times.values()) / len(self.source_processing_times)
            if self.source_processing_times
            else 0.0
        )

        stats["error_count"] = sum(self.error_counts.values())
        stats["source_processing_times"] = self.source_processing_times.copy()
        stats["error_counts"] = self.error_counts.copy()

        return stats

    def get_processing_summary(self) -> Dict[str, Any]:
        """Get a human-readable processing summary.

        Returns:
            Dictionary containing processing summary information
        """
        stats = self.get_processing_statistics()

        return {
            "total_sources": stats["total_sources"],
            "processed_sources": stats["processed_sources"],
            "valid_configs": stats["valid_configs"],
            "duplicate_configs": stats["duplicate_configs"],
            "success_rate": f"{stats['success_rate']:.1%}",
            "processing_duration": (
                f"{stats['processing_duration']:.1f}s" if stats["processing_duration"] else "N/A"
            ),
            "avg_processing_time": f"{stats['avg_processing_time']:.2f}s",
            "error_count": stats["error_count"],
        }

    def reset_statistics(self) -> None:
        """Reset processing statistics."""
        self.processing_stats = {
            "total_sources": 0,
            "processed_sources": 0,
            "total_configs": 0,
            "valid_configs": 0,
            "duplicate_configs": 0,
            "start_time": None,
            "end_time": None,
        }
        self.source_processing_times.clear()
        self.error_counts.clear()
        logger.info("Statistics reset")
