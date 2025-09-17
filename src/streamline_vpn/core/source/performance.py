"""
Source performance tracking and analytics.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ...utils.logging import get_logger

logger = get_logger(__name__)


class SourcePerformance:
    """Tracks and analyzes source performance metrics."""

    def __init__(self, performance_data: Dict[str, Any]):
        self.performance_data = performance_data

    def update_source_performance(
        self,
        source_url: str,
        success: bool,
        response_time: float,
        config_count: int = 0,
    ) -> None:
        """Update performance metrics for a source."""
        if source_url not in self.performance_data:
            self.performance_data[source_url] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_response_time": 0.0,
                "avg_response_time": 0.0,
                "total_configs": 0,
                "last_success": None,
                "last_failure": None,
                "reputation_score": 1.0,
                "blacklisted": False,
            }

        data = self.performance_data[source_url]
        data["total_requests"] += 1

        if success:
            data["successful_requests"] += 1
            data["last_success"] = datetime.now().isoformat()
            data["total_configs"] += config_count
        else:
            data["failed_requests"] += 1
            data["last_failure"] = datetime.now().isoformat()

        # Update response time metrics
        data["total_response_time"] += response_time
        data["avg_response_time"] = data["total_response_time"] / data["total_requests"]

        # Calculate reputation score
        self._calculate_reputation_score(data)

    def _calculate_reputation_score(self, data: Dict[str, Any]) -> None:
        """Calculate reputation score based on performance metrics."""
        if data["total_requests"] == 0:
            data["reputation_score"] = 1.0
            return

        success_rate = data["successful_requests"] / data["total_requests"]

        # Base score from success rate
        base_score = success_rate

        # Penalty for slow response times
        if data["avg_response_time"] > 30.0:  # 30 seconds
            time_penalty = min(0.3, (data["avg_response_time"] - 30.0) / 100.0)
            base_score -= time_penalty

        # Bonus for high config count
        if data["total_configs"] > 0:
            config_bonus = min(0.2, data["total_configs"] / 1000.0)
            base_score += config_bonus

        # Ensure score is between 0 and 1
        data["reputation_score"] = max(0.0, min(1.0, base_score))

    def get_top_sources(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get top performing sources."""
        sources = []

        for url, data in self.performance_data.items():
            if data.get("blacklisted", False):
                continue

            if data["total_requests"] < 3:  # Need minimum requests for reliability
                continue

            sources.append(
                {
                    "url": url,
                    "reputation_score": data["reputation_score"],
                    "success_rate": data["successful_requests"]
                    / data["total_requests"],
                    "avg_response_time": data["avg_response_time"],
                    "total_configs": data["total_configs"],
                    "total_requests": data["total_requests"],
                }
            )

        # Sort by reputation score
        sources.sort(key=lambda x: x["reputation_score"], reverse=True)
        return sources[:count]

    def get_source_statistics(self) -> Dict[str, Any]:
        """Get overall source statistics."""
        total_sources = len(self.performance_data)
        active_sources = sum(
            1
            for data in self.performance_data.values()
            if not data.get("blacklisted", False)
        )
        blacklisted_sources = sum(
            1
            for data in self.performance_data.values()
            if data.get("blacklisted", False)
        )

        if total_sources == 0:
            return {
                "total_sources": 0,
                "active_sources": 0,
                "blacklisted_sources": 0,
                "avg_reputation_score": 0.0,
                "total_requests": 0,
                "total_configs": 0,
            }

        def _get(d: Dict[str, Any], key: str, default: Any) -> Any:
            try:
                return d.get(key, default)
            except Exception:
                return default

        total_requests = sum(
            _get(data, "total_requests", 0) for data in self.performance_data.values()
        )
        total_configs = sum(
            _get(data, "total_configs", 0) for data in self.performance_data.values()
        )
        avg_reputation = sum(
            _get(data, "reputation_score", 1.0)
            for data in self.performance_data.values()
        ) / max(total_sources, 1)

        # Build tier distribution if available in data
        tier_distribution: Dict[str, int] = {}
        for url, data in self.performance_data.items():
            tier = data.get("tier")
            if tier:
                tier_distribution[tier] = tier_distribution.get(tier, 0) + 1

        return {
            "total_sources": total_sources,
            "active_sources": active_sources,
            "blacklisted_sources": blacklisted_sources,
            "avg_reputation_score": round(avg_reputation, 3),
            "total_requests": total_requests,
            "total_configs": total_configs,
            "tier_distribution": tier_distribution,
        }

    def blacklist_source(self, source_url: str, reason: str = "") -> None:
        """Blacklist a source."""
        if source_url in self.performance_data:
            self.performance_data[source_url]["blacklisted"] = True
            self.performance_data[source_url]["blacklist_reason"] = reason
            logger.warning("Blacklisted source %s: %s", source_url, reason)

    def whitelist_source(self, source_url: str) -> None:
        """Remove source from blacklist."""
        if source_url in self.performance_data:
            self.performance_data[source_url]["blacklisted"] = False
            if "blacklist_reason" in self.performance_data[source_url]:
                del self.performance_data[source_url]["blacklist_reason"]
            logger.info("Whitelisted source %s", source_url)

    def cleanup_old_data(self, days: int = 30) -> None:
        """Clean up old performance data."""
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0

        for url, data in list(self.performance_data.items()):
            # Remove sources that haven't been used recently
            last_activity = None
            if data.get("last_success"):
                last_activity = datetime.fromisoformat(data["last_success"])
            elif data.get("last_failure"):
                last_activity = datetime.fromisoformat(data["last_failure"])

            if last_activity and last_activity < cutoff_date:
                del self.performance_data[url]
                cleaned_count += 1

        if cleaned_count > 0:
            logger.info("Cleaned up %d old source entries", cleaned_count)
