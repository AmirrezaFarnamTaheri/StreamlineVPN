"""
L1 Application Cache
===================

In-memory application-level cache with LRU eviction.
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ...utils.logging import get_logger
from .models import CacheEntry, CacheStats

logger = get_logger(__name__)


class L1ApplicationCache:
    """L1 application-level cache with LRU eviction."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """Initialize L1 cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order = []
        self.stats = CacheStats()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from L1 cache."""
        start_time = time.perf_counter()

        if key in self.cache:
            entry = self.cache[key]

            # Check TTL
            if self._is_expired(entry):
                await self.delete(key)
                self.stats.misses += 1
            else:
                # Update access tracking
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                self._update_access_order(key)

                self.stats.hits += 1
                response_time = time.perf_counter() - start_time
                self._update_avg_response_time(response_time)

                return entry.value

        self.stats.misses += 1
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Set value in L1 cache."""
        if ttl is None:
            ttl = self.default_ttl

        # Evict if necessary
        if len(self.cache) >= self.max_size:
            await self._evict_lru()

        entry = CacheEntry(
            key=key,
            value=value,
            ttl=ttl,
            created_at=datetime.now(),
            tags=tags or [],
        )

        self.cache[key] = entry
        self._update_access_order(key)

    async def delete(self, key: str) -> bool:
        """Delete key from L1 cache."""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
            return True
        return False

    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate entries by tags."""
        invalidated = 0
        keys_to_delete = []

        for key, entry in self.cache.items():
            if any(tag in entry.tags for tag in tags):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            await self.delete(key)
            invalidated += 1

        self.stats.invalidations += invalidated
        return invalidated

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        return datetime.now() - entry.created_at > timedelta(seconds=entry.ttl)

    def _update_access_order(self, key: str) -> None:
        """Update access order for LRU tracking."""
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

    async def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if self.access_order:
            lru_key = self.access_order[0]
            await self.delete(lru_key)
            self.stats.evictions += 1

    def _update_avg_response_time(self, response_time: float) -> None:
        """Update average response time."""
        self.stats.total_requests += 1
        alpha = 0.1
        self.stats.avg_response_time = (
            alpha * response_time + (1 - alpha) * self.stats.avg_response_time
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        hit_rate = self.stats.hits / max(self.stats.total_requests, 1)
        return {
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "hit_rate": hit_rate,
            "evictions": self.stats.evictions,
            "invalidations": self.stats.invalidations,
            "size": len(self.cache),
            "max_size": self.max_size,
            "avg_response_time": self.stats.avg_response_time,
        }
