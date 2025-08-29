import asyncio
import hashlib
import pickle
import time
from typing import Any, Optional, Union, Dict, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
import json
from pathlib import Path
import threading
from collections import OrderedDict

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    value: Any
    expires_at: datetime
    last_access: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return datetime.now() > self.expires_at
    
    def is_stale(self, max_age: Optional[timedelta] = None) -> bool:
        """Check if entry is stale based on age."""
        if max_age is None:
            return False
        return datetime.now() - self.last_access > max_age
    
    def touch(self):
        """Update last access time."""
        self.last_access = datetime.now()
        self.access_count += 1

@dataclass
class CacheStats:
    """Cache performance statistics."""
    l1_hits: int = 0
    l2_hits: int = 0
    misses: int = 0
    evictions: int = 0
    errors: int = 0
    total_operations: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate overall hit rate."""
        total = self.l1_hits + self.l2_hits + self.misses
        if total == 0:
            return 0.0
        return (self.l1_hits + self.l2_hits) / total
    
    @property
    def l1_hit_rate(self) -> float:
        """Calculate L1 cache hit rate."""
        total = self.l1_hits + self.l2_hits + self.misses
        if total == 0:
            return 0.0
        return self.l1_hits / total
    
    @property
    def l2_hit_rate(self) -> float:
        """Calculate L2 cache hit rate."""
        total = self.l1_hits + self.l2_hits + self.misses
        if total == 0:
            return 0.0
        return self.l2_hits / total

class MultiTierCache:
    """Multi-tier caching system with L1 (memory) and L2 (Redis) caches."""
    
    def __init__(self, redis_client=None, l1_max_size: int = 1000, 
                 l1_max_memory_mb: int = 100, default_ttl: int = 3600):
        self.l1_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.l1_max_size = l1_max_size
        self.l1_max_memory_mb = l1_max_memory_mb
        self.l1_current_memory_mb = 0
        self.default_ttl = default_ttl
        self.redis = redis_client
        self.stats = CacheStats()
        self._lock = threading.RLock()
        
        # Background cleanup
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup()
    
    def _start_cleanup(self):
        """Start background cleanup task."""
        async def cleanup_loop():
            while True:
                try:
                    await self._cleanup_expired()
                    await asyncio.sleep(60)  # Cleanup every minute
                except Exception as e:
                    logger.error(f"Cache cleanup error: {e}")
                    await asyncio.sleep(300)  # Wait longer on error
        
        try:
            loop = asyncio.get_event_loop()
            self._cleanup_task = loop.create_task(cleanup_loop())
        except RuntimeError:
            # No event loop, skip cleanup
            logger.warning("No event loop available, skipping cache cleanup")
    
    async def _cleanup_expired(self):
        """Remove expired entries from L1 cache."""
        with self._lock:
            expired_keys = [
                key for key, entry in self.l1_cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                entry = self.l1_cache.pop(key)
                self.l1_current_memory_mb -= entry.size_bytes / (1024 * 1024)
                self.stats.evictions += 1
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of a value in bytes."""
        try:
            # Try to serialize to get size estimate
            serialized = pickle.dumps(value)
            return len(serialized)
        except Exception:
            # Fallback to rough estimate
            return 1024  # 1KB default estimate
    
    def _add_to_l1(self, key: str, value: Any, ttl: int = None, tags: List[str] = None):
        """Add entry to L1 cache with LRU eviction."""
        if ttl is None:
            ttl = self.default_ttl
        
        # Calculate size
        size_bytes = self._estimate_size(value)
        size_mb = size_bytes / (1024 * 1024)
        
        # Check if we need to evict entries
        while (len(self.l1_cache) >= self.l1_max_size or 
               self.l1_current_memory_mb + size_mb > self.l1_max_memory_mb):
            
            if not self.l1_cache:
                logger.warning("Cache is empty but still over limits")
                break
            
            # Remove least recently used entry
            lru_key, lru_entry = self.l1_cache.popitem(last=False)
            self.l1_current_memory_mb -= lru_entry.size_bytes / (1024 * 1024)
            self.stats.evictions += 1
            
            logger.debug(f"Evicted L1 cache entry: {lru_key}")
        
        # Add new entry
        entry = CacheEntry(
            value=value,
            expires_at=datetime.now() + timedelta(seconds=ttl),
            size_bytes=size_bytes,
            tags=tags or []
        )
        
        self.l1_cache[key] = entry
        self.l1_current_memory_mb += size_mb
        
        # Move to end (most recently used)
        self.l1_cache.move_to_end(key)
    
    async def get(self, key: str, tier: str = 'all') -> Optional[Any]:
        """Get value from cache with tier selection."""
        self.stats.total_operations += 1
        
        # Check L1 first
        if tier in ('all', 'l1'):
            with self._lock:
                if key in self.l1_cache:
                    entry = self.l1_cache[key]
                    if not entry.is_expired():
                        entry.touch()
                        self.l1_cache.move_to_end(key)  # Move to MRU position
                        self.stats.l1_hits += 1
                        return entry.value
                    else:
                        # Remove expired entry
                        del self.l1_cache[key]
                        self.l1_current_memory_mb -= entry.size_bytes / (1024 * 1024)
        
        # Check L2 (Redis)
        if tier in ('all', 'l2') and self.redis:
            try:
                data = await self.redis.get(f"cache:{key}")
                if data:
                    self.stats.l2_hits += 1
                    value = pickle.loads(data)
                    
                    # Promote to L1 if tier is 'all'
                    if tier == 'all':
                        self._add_to_l1(key, value)
                    
                    return value
            except Exception as e:
                logger.error(f"Redis cache error: {e}")
                self.stats.errors += 1
        
        self.stats.misses += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = None, 
                  tier: str = 'all', tags: List[str] = None):
        """Set value in cache with tier selection."""
        if ttl is None:
            ttl = self.default_ttl
        
        # Add to L1
        if tier in ('all', 'l1'):
            self._add_to_l1(key, value, ttl, tags)
        
        # Add to L2 (Redis)
        if tier in ('all', 'l2') and self.redis:
            try:
                data = pickle.dumps(value)
                await self.redis.setex(f"cache:{key}", ttl, data)
            except Exception as e:
                logger.error(f"Redis cache set error: {e}")
                self.stats.errors += 1
    
    async def delete(self, key: str, tier: str = 'all'):
        """Delete entry from cache."""
        # Remove from L1
        if tier in ('all', 'l1'):
            with self._lock:
                if key in self.l1_cache:
                    entry = self.l1_cache.pop(key)
                    self.l1_current_memory_mb -= entry.size_bytes / (1024 * 1024)
        
        # Remove from L2
        if tier in ('all', 'l2') and self.redis:
            try:
                await self.redis.delete(f"cache:{key}")
            except Exception as e:
                logger.error(f"Redis cache delete error: {e}")
    
    async def clear(self, tier: str = 'all'):
        """Clear all cache entries."""
        # Clear L1
        if tier in ('all', 'l1'):
            with self._lock:
                self.l1_cache.clear()
                self.l1_current_memory_mb = 0
        
        # Clear L2
        if tier in ('all', 'l2') and self.redis:
            try:
                # Note: This is a simple approach - in production you might want
                # to use pattern-based deletion or maintain a key index
                logger.warning("L2 cache clear not implemented - use with caution")
            except Exception as e:
                logger.error(f"Redis cache clear error: {e}")
    
    async def get_many(self, keys: List[str], tier: str = 'all') -> Dict[str, Any]:
        """Get multiple values from cache."""
        results = {}
        
        # Try L1 first
        if tier in ('all', 'l1'):
            with self._lock:
                for key in keys:
                    if key in self.l1_cache:
                        entry = self.l1_cache[key]
                        if not entry.is_expired():
                            entry.touch()
                            self.l1_cache.move_to_end(key)
                            results[key] = entry.value
                            self.stats.l1_hits += 1
        
        # Try L2 for remaining keys
        if tier in ('all', 'l2') and self.redis:
            remaining_keys = [k for k in keys if k not in results]
            if remaining_keys:
                try:
                    # Use pipeline for efficiency
                    pipe = self.redis.pipeline()
                    for key in remaining_keys:
                        pipe.get(f"cache:{key}")
                    
                    values = await pipe.execute()
                    
                    for key, value in zip(remaining_keys, values):
                        if value:
                            parsed_value = pickle.loads(value)
                            results[key] = parsed_value
                            self.stats.l2_hits += 1
                            
                            # Promote to L1 if tier is 'all'
                            if tier == 'all':
                                self._add_to_l1(key, parsed_value)
                
                except Exception as e:
                    logger.error(f"Redis cache get_many error: {e}")
                    self.stats.errors += 1
        
        # Count misses
        self.stats.misses += len(keys) - len(results)
        self.stats.total_operations += len(keys)
        
        return results
    
    async def set_many(self, data: Dict[str, Any], ttl: int = None, 
                       tier: str = 'all', tags: List[str] = None):
        """Set multiple values in cache."""
        if ttl is None:
            ttl = self.default_ttl
        
        # Set in L1
        if tier in ('all', 'l1'):
            for key, value in data.items():
                self._add_to_l1(key, value, ttl, tags)
        
        # Set in L2
        if tier in ('all', 'l2') and self.redis:
            try:
                pipe = self.redis.pipeline()
                for key, value in data.items():
                    serialized = pickle.dumps(value)
                    pipe.setex(f"cache:{key}", ttl, serialized)
                
                await pipe.execute()
                
            except Exception as e:
                logger.error(f"Redis cache set_many error: {e}")
                self.stats.errors += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        with self._lock:
            l1_size = len(self.l1_cache)
            l1_memory_mb = self.l1_current_memory_mb
        
        return {
            'l1_cache': {
                'size': l1_size,
                'max_size': self.l1_max_size,
                'memory_mb': l1_memory_mb,
                'max_memory_mb': self.l1_max_memory_mb,
                'utilization_percent': (l1_size / self.l1_max_size) * 100 if self.l1_max_size > 0 else 0,
                'memory_utilization_percent': (l1_memory_mb / self.l1_max_memory_mb) * 100 if self.l1_max_memory_mb > 0 else 0
            },
            'l2_cache': {
                'available': self.redis is not None,
                'connected': self.redis is not None and hasattr(self.redis, 'ping')
            },
            'performance': {
                'total_operations': self.stats.total_operations,
                'hits': self.stats.l1_hits + self.stats.l2_hits,
                'misses': self.stats.misses,
                'hit_rate': self.stats.hit_rate,
                'l1_hit_rate': self.stats.l1_hit_rate,
                'l2_hit_rate': self.stats.l2_hit_rate,
                'evictions': self.stats.evictions,
                'errors': self.stats.errors
            }
        }
    
    def export_stats(self, output_path: str = "cache_stats.json"):
        """Export cache statistics to JSON file."""
        stats = self.get_stats()
        stats['exported_at'] = datetime.now().isoformat()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, default=str)
        
        logger.info(f"Cache statistics exported to {output_path}")
        return output_path
    
    def reset_stats(self):
        """Reset cache statistics."""
        self.stats = CacheStats()
        logger.info("Cache statistics reset")

class CacheManager:
    """Manager for multiple cache instances."""
    
    def __init__(self):
        self.caches: Dict[str, MultiTierCache] = {}
        self._lock = threading.RLock()
    
    def create_cache(self, name: str, **kwargs) -> MultiTierCache:
        """Create a new cache instance."""
        with self._lock:
            if name in self.caches:
                logger.warning(f"Cache '{name}' already exists, returning existing instance")
                return self.caches[name]
            
            cache = MultiTierCache(**kwargs)
            self.caches[name] = cache
            logger.info(f"Created cache '{name}'")
            return cache
    
    def get_cache(self, name: str) -> Optional[MultiTierCache]:
        """Get an existing cache instance."""
        return self.caches.get(name)
    
    def list_caches(self) -> List[str]:
        """List all cache names."""
        return list(self.caches.keys())
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches."""
        return {name: cache.get_stats() for name, cache in self.caches.items()}
    
    def clear_all(self, tier: str = 'all'):
        """Clear all caches."""
        for name, cache in self.caches.items():
            asyncio.create_task(cache.clear(tier))
        logger.info(f"Cleared all caches (tier: {tier})")

# Global cache manager instance
_cache_manager: Optional[CacheManager] = None

def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

def get_cache(name: str = "default") -> MultiTierCache:
    """Get a cache instance by name."""
    manager = get_cache_manager()
    cache = manager.get_cache(name)
    if cache is None:
        cache = manager.create_cache(name)
    return cache

