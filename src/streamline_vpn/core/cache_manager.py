"""
Cache Manager
==============

Manages multi-tier caching for improved performance.
"""

import asyncio
import json
import pickle
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta

from ..utils.logging import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Multi-tier cache manager with L1 (memory), L2 (Redis), L3 (disk)."""

    def __init__(self, cache_dir: str = "cache"):
        """Initialize cache manager.

        Args:
            cache_dir: Cache directory path
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # L1: Memory cache
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.memory_cache_size = 1000
        self.memory_cache_hits = 0
        self.memory_cache_misses = 0
        
        # L2: Redis cache (optional)
        self.redis_client = None
        self.redis_enabled = False
        self._init_redis()
        
        # L3: Disk cache
        self.disk_cache_dir = self.cache_dir / "disk"
        self.disk_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache statistics
        self.stats = {
            'l1_hits': 0,
            'l1_misses': 0,
            'l2_hits': 0,
            'l2_misses': 0,
            'l3_hits': 0,
            'l3_misses': 0,
            'total_requests': 0
        }
        
        logger.info("Cache manager initialized")

    def _init_redis(self) -> None:
        """Prepare Redis client if library is available (connection deferred)."""
        try:
            import redis.asyncio as redis  # type: ignore
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=False,
            )
        except ImportError:
            self.redis_client = None
            logger.debug("Redis not available, using memory and disk cache only")
        except Exception as e:
            self.redis_client = None
            logger.debug(f"Redis client init failed: {e}")

    async def connect(self) -> None:
        """Establish Redis connection if possible."""
        if not self.redis_client:
            self.redis_enabled = False
            return
        try:
            await self.redis_client.ping()
            self.redis_enabled = True
            logger.info("Redis cache enabled")
        except Exception as e:
            self.redis_enabled = False
            logger.debug(f"Redis connection test failed: {e}")

    async def disconnect(self) -> None:
        """Close Redis client if enabled."""
        try:
            if self.redis_client:
                await self.redis_client.close()
        except Exception:
            pass

    def _generate_key(self, key: str) -> str:
        """Generate cache key with namespace.

        Args:
            key: Original key

        Returns:
            Namespaced key
        """
        return f"streamline:{hashlib.md5(key.encode()).hexdigest()}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (checks all tiers).

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        self.stats['total_requests'] += 1
        cache_key = self._generate_key(key)

        # Check L1 (Memory)
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if self._is_entry_valid(entry):
                self.stats['l1_hits'] += 1
                return entry['value']
            else:
                # Remove expired entry
                del self.memory_cache[cache_key]

        self.stats['l1_misses'] += 1

        # Check L2 (Redis)
        if self.redis_enabled:
            try:
                value = await self.redis_client.get(cache_key)
                if value:
                    deserialized = pickle.loads(value)
                    self.stats['l2_hits'] += 1
                    # Promote to L1
                    self._set_memory_cache(cache_key, deserialized)
                    return deserialized
            except Exception as e:
                logger.debug(f"Redis get error: {e}")

            self.stats['l2_misses'] += 1

        # Check L3 (Disk)
        disk_file = self.disk_cache_dir / f"{cache_key}.cache"
        if disk_file.exists():
            try:
                with open(disk_file, 'rb') as f:
                    entry = pickle.load(f)
                if self._is_entry_valid(entry):
                    self.stats['l3_hits'] += 1
                    # Promote to L1 and L2
                    self._set_memory_cache(cache_key, entry['value'])
                    if self.redis_enabled:
                        await self._set_redis_cache(cache_key, entry['value'], ttl=3600)
                    return entry['value']
                else:
                    # Remove expired file
                    disk_file.unlink()
            except Exception as e:
                logger.debug(f"Disk cache read error: {e}")

        self.stats['l3_misses'] += 1
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache (all tiers).

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        cache_key = self._generate_key(key)
        expiry = datetime.now() + timedelta(seconds=ttl)
        
        # Set in L1 (Memory)
        self._set_memory_cache(cache_key, value, expiry)
        
        # Set in L2 (Redis)
        if self.redis_enabled:
            await self._set_redis_cache(cache_key, value, ttl)
        
        # Set in L3 (Disk)
        await self._set_disk_cache(cache_key, value, expiry)

    def _set_memory_cache(self, key: str, value: Any, expiry: Optional[datetime] = None) -> None:
        """Set value in memory cache.

        Args:
            key: Cache key
            value: Value to cache
            expiry: Expiry time
        """
        if expiry is None:
            expiry = datetime.now() + timedelta(seconds=3600)
        
        # Check cache size and evict if necessary
        if len(self.memory_cache) >= self.memory_cache_size:
            self._evict_memory_cache()
        
        self.memory_cache[key] = {
            'value': value,
            'expiry': expiry,
            'created': datetime.now()
        }

    async def _set_redis_cache(self, key: str, value: Any, ttl: int) -> None:
        """Set value in Redis cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        try:
            serialized = pickle.dumps(value)
            await self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.debug(f"Redis set error: {e}")

    async def _set_disk_cache(self, key: str, value: Any, expiry: datetime) -> None:
        """Set value in disk cache.

        Args:
            key: Cache key
            value: Value to cache
            expiry: Expiry time
        """
        try:
            entry = {
                'value': value,
                'expiry': expiry,
                'created': datetime.now()
            }
            
            disk_file = self.disk_cache_dir / f"{key}.cache"
            with open(disk_file, 'wb') as f:
                pickle.dump(entry, f)
        except Exception as e:
            logger.debug(f"Disk cache write error: {e}")

    def _is_entry_valid(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is valid (not expired).

        Args:
            entry: Cache entry

        Returns:
            True if entry is valid
        """
        if 'expiry' not in entry:
            return True
        
        return datetime.now() < entry['expiry']

    def _evict_memory_cache(self) -> None:
        """Evict entries from memory cache using LRU strategy."""
        if not self.memory_cache:
            return
        
        # Remove oldest entries (simple LRU)
        sorted_entries = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1].get('created', datetime.min)
        )
        
        # Remove 20% of entries
        evict_count = max(1, len(sorted_entries) // 5)
        for key, _ in sorted_entries[:evict_count]:
            del self.memory_cache[key]

    async def invalidate(self, key: str) -> None:
        """Invalidate cache entry.

        Args:
            key: Cache key to invalidate
        """
        cache_key = self._generate_key(key)
        
        # Remove from L1
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]
        
        # Remove from L2
        if self.redis_enabled:
            try:
                await self.redis_client.delete(cache_key)
            except Exception as e:
                logger.debug(f"Redis delete error: {e}")
        
        # Remove from L3
        disk_file = self.disk_cache_dir / f"{cache_key}.cache"
        if disk_file.exists():
            try:
                disk_file.unlink()
            except Exception as e:
                logger.debug(f"Disk cache delete error: {e}")

    async def clear(self) -> None:
        """Clear all cache tiers."""
        # Clear L1
        self.memory_cache.clear()
        
        # Clear L2
        if self.redis_enabled:
            try:
                await self.redis_client.flushdb()
            except Exception as e:
                logger.debug(f"Redis flush error: {e}")
        
        # Clear L3
        try:
            for cache_file in self.disk_cache_dir.glob("*.cache"):
                cache_file.unlink()
        except Exception as e:
            logger.debug(f"Disk cache clear error: {e}")
        
        logger.info("All cache tiers cleared")

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Statistics dictionary
        """
        total_requests = self.stats['total_requests']
        if total_requests == 0:
            hit_rate = 0.0
        else:
            total_hits = (self.stats['l1_hits'] + self.stats['l2_hits'] + self.stats['l3_hits'])
            hit_rate = total_hits / total_requests
        
        return {
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'l1_hits': self.stats['l1_hits'],
            'l1_misses': self.stats['l1_misses'],
            'l2_hits': self.stats['l2_hits'],
            'l2_misses': self.stats['l2_misses'],
            'l3_hits': self.stats['l3_hits'],
            'l3_misses': self.stats['l3_misses'],
            'memory_cache_size': len(self.memory_cache),
            'redis_enabled': self.redis_enabled,
            'disk_cache_files': len(list(self.disk_cache_dir.glob("*.cache")))
        }

    async def cleanup_expired(self) -> None:
        """Clean up expired entries from all cache tiers."""
        # Clean L1
        expired_keys = []
        for key, entry in self.memory_cache.items():
            if not self._is_entry_valid(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        # Clean L3
        try:
            for cache_file in self.disk_cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        entry = pickle.load(f)
                    if not self._is_entry_valid(entry):
                        cache_file.unlink()
                except Exception:
                    # Remove corrupted files
                    cache_file.unlink()
        except Exception as e:
            logger.debug(f"Disk cache cleanup error: {e}")
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

    async def close(self) -> None:
        """Close cache manager and cleanup resources."""
        if self.redis_enabled and self.redis_client:
            try:
                await self.redis_client.close()
            except Exception as e:
                logger.debug(f"Redis close error: {e}")
        
        # Cleanup expired entries
        await self.cleanup_expired()
        
        logger.info("Cache manager closed")
