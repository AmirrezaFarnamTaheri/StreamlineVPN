"""
VPN Cache Service
================

Main VPN caching service with multi-level architecture.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any

from ...utils.logging import get_logger
from ...constants import (
    DEFAULT_CACHE_TTL,
    DEFAULT_L1_CACHE_SIZE,
    DEFAULT_CIRCUIT_BREAKER_THRESHOLD,
    DEFAULT_CIRCUIT_BREAKER_TIMEOUT,
)
from .l1_cache import L1ApplicationCache
from .redis_client import RedisClusterClient
from .invalidation import CacheInvalidationService

logger = get_logger(__name__)


class VPNCacheService:
    """Main VPN caching service with multi-level architecture."""
    
    def __init__(self, redis_nodes: List[Dict[str, str]], l1_cache_size: int = DEFAULT_L1_CACHE_SIZE):
        """Initialize VPN cache service.
        
        Args:
            redis_nodes: Redis cluster node configurations
            l1_cache_size: L1 cache size
        """
        self.l1_cache = L1ApplicationCache(max_size=l1_cache_size)
        self.redis_client = RedisClusterClient(redis_nodes)
        self.invalidation_service = CacheInvalidationService()
        self.circuit_breaker_threshold = DEFAULT_CIRCUIT_BREAKER_THRESHOLD
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = None
        self.circuit_breaker_timeout = DEFAULT_CIRCUIT_BREAKER_TIMEOUT
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        # Try L1 cache first
        value = await self.l1_cache.get(key)
        if value is not None:
            return value
        
        # Try L2 Redis cache
        if not self._is_circuit_breaker_open():
            try:
                redis_value = await self.redis_client.get(key)
                if redis_value is not None:
                    # Parse JSON value
                    try:
                        parsed_value = json.loads(redis_value)
                        # Store in L1 cache for faster access
                        await self.l1_cache.set(key, parsed_value, ttl=DEFAULT_CACHE_TTL)
                        return parsed_value
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse Redis value for key {key}")
                
                self._reset_circuit_breaker()
                
            except Exception as e:
                logger.error(f"Redis cache error for key {key}: {e}")
                self._record_circuit_breaker_failure()
        
        # L3 database fallback would be implemented here
        return None
    
    async def set(self, key: str, value: Any, ttl: int = DEFAULT_CACHE_TTL, tags: Optional[List[str]] = None) -> bool:
        """Set value in multi-level cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            tags: Optional tags for invalidation
            
        Returns:
            True if successful
        """
        try:
            # Set in L1 cache
            await self.l1_cache.set(key, value, ttl=ttl, tags=tags)
            
            # Set in L2 Redis cache
            if not self._is_circuit_breaker_open():
                try:
                    json_value = json.dumps(value)
                    success = await self.redis_client.set(key, json_value, ttl=ttl)
                    if success:
                        self._reset_circuit_breaker()
                        return True
                    else:
                        self._record_circuit_breaker_failure()
                        
                except Exception as e:
                    logger.error(f"Redis cache set error for key {key}: {e}")
                    self._record_circuit_breaker_failure()
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from all cache levels."""
        try:
            # Delete from L1 cache
            await self.l1_cache.delete(key)
            
            # Delete from L2 Redis cache
            if not self._is_circuit_breaker_open():
                try:
                    await self.redis_client.delete(key)
                    self._reset_circuit_breaker()
                except Exception as e:
                    logger.error(f"Redis cache delete error for key {key}: {e}")
                    self._record_circuit_breaker_failure()
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def cache_server_recommendations(self, user_id: str, region: str, recommendations: Dict[str, float]) -> bool:
        """Cache server recommendations with intelligent TTL.
        
        Args:
            user_id: User identifier
            region: Geographic region
            recommendations: Server recommendations with scores
            
        Returns:
            True if cached successfully
        """
        cache_key = f"server_rec:{user_id}:{region}"
        
        # Cache with 5-minute TTL for server recommendations
        return await self.set(
            key=cache_key,
            value=recommendations,
            ttl=DEFAULT_CACHE_TTL,
            tags=["server_rec", f"user:{user_id}", f"region:{region}"]
        )
    
    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cache entries for a user."""
        return await self.invalidation_service.invalidate_cache_pattern(
            event_type="user_preference_change",
            context=user_id,
            redis_client=self.redis_client
        )
    
    async def invalidate_server_cache(self, server_id: str) -> int:
        """Invalidate all cache entries for a server."""
        return await self.invalidation_service.invalidate_cache_pattern(
            event_type="server_update",
            context=server_id,
            redis_client=self.redis_client
        )
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self.circuit_breaker_failures < self.circuit_breaker_threshold:
            return False
        
        if self.circuit_breaker_last_failure is None:
            return False
        
        time_since_failure = time.time() - self.circuit_breaker_last_failure
        return time_since_failure < self.circuit_breaker_timeout
    
    def _record_circuit_breaker_failure(self) -> None:
        """Record circuit breaker failure."""
        self.circuit_breaker_failures += 1
        self.circuit_breaker_last_failure = time.time()
    
    def _reset_circuit_breaker(self) -> None:
        """Reset circuit breaker."""
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        return {
            "l1_cache": self.l1_cache.get_stats(),
            "l2_redis": self.redis_client.get_stats(),
            "invalidation": self.invalidation_service.get_invalidation_stats(),
            "circuit_breaker": {
                "failures": self.circuit_breaker_failures,
                "is_open": self._is_circuit_breaker_open(),
                "last_failure": self.circuit_breaker_last_failure
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Alias for get_cache_stats for backward compatibility."""
        return self.get_cache_stats()
    
    async def invalidate(self, key: str) -> bool:
        """Alias for delete for backward compatibility."""
        return await self.delete(key)


# Global cache service instance
_cache_service: Optional[VPNCacheService] = None


def initialize_cache_service(redis_nodes: List[Dict[str, str]], l1_cache_size: int = 1000) -> VPNCacheService:
    """Initialize global cache service."""
    global _cache_service
    _cache_service = VPNCacheService(redis_nodes, l1_cache_size)
    return _cache_service


def get_cache_service() -> Optional[VPNCacheService]:
    """Get global cache service instance."""
    return _cache_service
