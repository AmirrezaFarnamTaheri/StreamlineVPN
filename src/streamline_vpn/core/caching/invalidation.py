"""
Cache Invalidation Service
=========================

Intelligent cache invalidation service with pattern-based targeting.
"""

from typing import Dict, Optional, Any

from ...utils.logging import get_logger
from .redis_client import RedisClusterClient

logger = get_logger(__name__)


class CacheInvalidationService:
    """Intelligent cache invalidation service."""

    def __init__(self):
        """Initialize cache invalidation service."""
        self.invalidation_patterns = {
            "server_update": [
                "server_rec:*",
                "server_health:*",
                "server_perf:*",
            ],
            "user_preference_change": [
                "user_pref:*",
                "server_rec:*",
                "user_stats:*",
            ],
            "performance_degradation": ["server_perf:*", "quality_pred:*"],
            "configuration_change": ["config:*", "server_rec:*"],
            "security_incident": ["*"],  # Invalidate all caches for security incidents
        }
        self.invalidation_stats = {
            "total_invalidations": 0,
            "pattern_invalidations": 0,
            "keys_invalidated": 0,
        }

    async def invalidate_cache_pattern(
        self,
        event_type: str,
        context: Optional[str] = None,
        redis_client: Optional[RedisClusterClient] = None,
    ) -> int:
        """Invalidate cache entries based on event type and context.

        Args:
            event_type: Type of event triggering invalidation
            context: Optional context for targeted invalidation
            redis_client: Redis client for L2 cache invalidation

        Returns:
            Number of keys invalidated
        """
        if event_type not in self.invalidation_patterns:
            logger.warning(f"Unknown invalidation event type: {event_type}")
            return 0

        patterns = self.invalidation_patterns[event_type]
        total_invalidated = 0

        for pattern in patterns:
            # Create specific pattern with context if provided
            specific_pattern = (
                pattern.replace("*", f"*{context}*") if context else pattern
            )

            # Invalidate L2 Redis cache
            if redis_client:
                invalidated = await self._invalidate_redis_pattern(
                    redis_client, specific_pattern
                )
                total_invalidated += invalidated

            self.invalidation_stats["pattern_invalidations"] += 1

        self.invalidation_stats["total_invalidations"] += 1
        self.invalidation_stats["keys_invalidated"] += total_invalidated

        logger.info(f"Invalidated {total_invalidated} keys for event {event_type}")
        return total_invalidated

    async def _invalidate_redis_pattern(
        self, redis_client: RedisClusterClient, pattern: str
    ) -> int:
        """Invalidate Redis keys matching pattern."""
        try:
            # Scan for keys matching pattern
            keys = await redis_client.scan(pattern, count=1000)

            # Delete matching keys
            invalidated = 0
            for key in keys:
                if await redis_client.delete(key):
                    invalidated += 1

            return invalidated

        except Exception as e:
            logger.error(f"Failed to invalidate Redis pattern {pattern}: {e}")
            return 0

    def get_invalidation_stats(self) -> Dict[str, Any]:
        """Get invalidation statistics."""
        return self.invalidation_stats.copy()
