"""
Redis Cluster Client
===================

Redis cluster client with connection pooling and failover.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any

from redis.asyncio.cluster import RedisCluster
from redis.cluster import ClusterNode
from redis.exceptions import RedisError

from ...utils.logging import get_logger
from .models import CacheStats

logger = get_logger(__name__)


class RedisClusterClient:
    """Redis cluster client with connection pooling and failover."""

    def __init__(
        self, nodes: List[Dict[str, Any]], max_connections: int = 100
    ):
        """Initialize Redis cluster client.

        Args:
            nodes: List of Redis node configurations
            max_connections: Maximum connections per node
        """
        startup_nodes = [
            ClusterNode(host=node["host"], port=int(node["port"]))
            for node in nodes
        ]
        self.client = RedisCluster(
            startup_nodes=startup_nodes, decode_responses=True
        )
        self.stats = CacheStats()

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis cluster."""
        start_time = time.perf_counter()

        try:
            value = await self.client.get(key)

            if value is not None:
                self.stats.hits += 1
            else:
                self.stats.misses += 1

            response_time = time.perf_counter() - start_time
            self._update_avg_response_time(response_time)

            return value

        except RedisError as e:
            logger.error(f"Redis GET failed for key {key}: {e}")
            self.stats.misses += 1
            return None

    async def set(
        self, key: str, value: str, ttl: Optional[int] = None
    ) -> bool:
        """Set value in Redis cluster."""
        try:
            success = await self.client.set(key, value, ex=ttl)
            return bool(success)

        except RedisError as e:
            logger.error(f"Redis SET failed for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis cluster."""
        try:
            deleted_count = await self.client.delete(key)
            return deleted_count > 0

        except RedisError as e:
            logger.error(f"Redis DELETE failed for key {key}: {e}")
            return False

    async def scan(self, pattern: str, count: int = 100) -> List[str]:
        """Scan keys matching pattern."""
        try:
            keys = []
            cursor = "0"
            while cursor != 0:
                cursor, new_keys = await self.client.scan(
                    cursor=cursor, match=pattern, count=count
                )
                keys.extend(new_keys)
            return keys

        except RedisError as e:
            logger.error(f"Redis SCAN failed for pattern {pattern}: {e}")
            return []

    def _update_avg_response_time(self, response_time: float) -> None:
        """Update average response time."""
        self.stats.total_requests += 1
        alpha = 0.1
        self.stats.avg_response_time = (
            alpha * response_time + (1 - alpha) * self.stats.avg_response_time
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cluster statistics."""
        hit_rate = self.stats.hits / max(self.stats.total_requests, 1)
        return {
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "hit_rate": hit_rate,
            "avg_response_time": self.stats.avg_response_time,
        }

    async def close(self):
        """Close the Redis client connections."""
        await self.client.close()
