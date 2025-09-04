#!/usr/bin/env python3
"""
Performance Optimizer
====================

Comprehensive performance optimization module addressing:
- Efficient data structures
- Caching mechanisms
- Connection pooling
- Rate limiting
- Memory monitoring
"""

import asyncio
import gc
import hashlib
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from weakref import WeakValueDictionary

import aiohttp
from aiohttp import ClientTimeout, TCPConnector

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    memory_usage: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    connection_pool_size: int = 0
    active_connections: int = 0
    rate_limit_hits: int = 0
    processing_time: float = 0.0
    deduplication_saves: int = 0
    last_cleanup: float = field(default_factory=time.time)


class LRUCache:
    """Thread-safe LRU cache implementation."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, Any] = {}
        self.access_order = deque()
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.access_order.remove(key)
                self.access_order.append(key)
                return self.cache[key]
            return None
    
    async def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        async with self._lock:
            if key in self.cache:
                # Update existing
                self.access_order.remove(key)
            elif len(self.cache) >= self.max_size:
                # Remove least recently used
                oldest = self.access_order.popleft()
                del self.cache[oldest]
            
            self.cache[key] = value
            self.access_order.append(key)
    
    async def clear(self) -> None:
        """Clear cache."""
        async with self._lock:
            self.cache.clear()
            self.access_order.clear()
    
    def size(self) -> int:
        """Get cache size."""
        return len(self.cache)


class ConnectionPool:
    """Optimized HTTP connection pool with keep-alive and limits."""
    
    def __init__(self, 
                 max_connections: int = 100,
                 max_connections_per_host: int = 30,
                 keepalive_timeout: int = 30,
                 enable_cleanup_closed: bool = True):
        self.max_connections = max_connections
        self.max_connections_per_host = max_connections_per_host
        self.keepalive_timeout = keepalive_timeout
        self.enable_cleanup_closed = enable_cleanup_closed
        
        # Create optimized connector
        self.connector = TCPConnector(
            limit=max_connections,
            limit_per_host=max_connections_per_host,
            keepalive_timeout=keepalive_timeout,
            enable_cleanup_closed=enable_cleanup_closed,
            use_dns_cache=True,
            ttl_dns_cache=300,  # 5 minutes DNS cache
            family=0,  # Allow both IPv4 and IPv6
            ssl=False,  # Let aiohttp handle SSL
        )
        
        self.session: Optional[aiohttp.ClientSession] = None
        self._active_requests = 0
        self._lock = asyncio.Lock()
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            timeout = ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'VPN-Merger/1.0',
                    'Accept': 'text/plain, application/json',
                    'Connection': 'keep-alive'
                }
            )
        return self.session
    
    async def close(self) -> None:
        """Close connection pool."""
        if self.session and not self.session.closed:
            await self.session.close()
        if not self.connector.closed:
            await self.connector.close()
    
    async def get_active_connections(self) -> int:
        """Get number of active connections."""
        if self.session:
            return len(self.session.connector._conns)
        return 0


class RateLimiter:
    """Token bucket rate limiter for API calls."""
    
    def __init__(self, 
                 requests_per_second: float = 10.0,
                 burst_size: int = 20,
                 per_host_limit: Optional[Dict[str, float]] = None):
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.per_host_limit = per_host_limit or {}
        
        # Global rate limiter
        self._tokens = burst_size
        self._last_update = time.time()
        self._lock = asyncio.Lock()
        
        # Per-host rate limiters
        self._host_limiters: Dict[str, Dict[str, Any]] = {}
    
    async def acquire(self, host: Optional[str] = None) -> bool:
        """Acquire permission to make a request."""
        async with self._lock:
            current_time = time.time()
            
            # Update global tokens
            time_passed = current_time - self._last_update
            self._tokens = min(
                self.burst_size,
                self._tokens + time_passed * self.requests_per_second
            )
            self._last_update = current_time
            
            # Check global limit
            if self._tokens < 1:
                return False
            
            # Check per-host limit if specified
            if host and host in self.per_host_limit:
                if not await self._check_host_limit(host, current_time):
                    return False
            
            # Consume token
            self._tokens -= 1
            return True
    
    async def _check_host_limit(self, host: str, current_time: float) -> bool:
        """Check per-host rate limit."""
        if host not in self._host_limiters:
            self._host_limiters[host] = {
                'tokens': self.burst_size,
                'last_update': current_time
            }
        
        limiter = self._host_limiters[host]
        time_passed = current_time - limiter['last_update']
        host_rps = self.per_host_limit[host]
        
        limiter['tokens'] = min(
            self.burst_size,
            limiter['tokens'] + time_passed * host_rps
        )
        limiter['last_update'] = current_time
        
        if limiter['tokens'] < 1:
            return False
        
        limiter['tokens'] -= 1
        return True


class MemoryMonitor:
    """Memory usage monitoring and optimization."""
    
    def __init__(self, 
                 max_memory_mb: int = 512,
                 cleanup_threshold: float = 0.8,
                 monitoring_interval: float = 30.0):
        self.max_memory_mb = max_memory_mb
        self.cleanup_threshold = cleanup_threshold
        self.monitoring_interval = monitoring_interval
        
        self._memory_history = deque(maxlen=100)
        self._last_cleanup = time.time()
        self._lock = asyncio.Lock()
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback to basic memory info
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    
    async def check_memory_pressure(self) -> bool:
        """Check if memory pressure requires cleanup."""
        current_memory = self.get_memory_usage()
        
        async with self._lock:
            self._memory_history.append(current_memory)
            
            # Check if we need cleanup
            if (current_memory > self.max_memory_mb * self.cleanup_threshold or
                time.time() - self._last_cleanup > self.monitoring_interval):
                return True
        
        return False
    
    async def force_cleanup(self) -> Dict[str, Any]:
        """Force memory cleanup and return cleanup stats."""
        async with self._lock:
            before_memory = self.get_memory_usage()
            
            # Force garbage collection
            collected = gc.collect()
            
            after_memory = self.get_memory_usage()
            self._last_cleanup = time.time()
            
            return {
                'before_mb': before_memory,
                'after_mb': after_memory,
                'freed_mb': before_memory - after_memory,
                'objects_collected': collected
            }


class OptimizedDataStructures:
    """Optimized data structures for better performance."""
    
    def __init__(self):
        # Use sets for O(1) lookups instead of lists
        self.processed_configs: Set[str] = set()
        self.duplicate_configs: Set[str] = set()
        
        # Use defaultdict for efficient counting
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.processing_times: Dict[str, float] = {}
        
        # Use WeakValueDictionary for automatic cleanup
        self.config_cache: WeakValueDictionary = WeakValueDictionary()
        
        # Use deque for efficient append/pop operations
        self.recent_configs = deque(maxlen=1000)
        self.processing_queue = deque()
    
    def add_processed_config(self, config: str) -> None:
        """Add processed configuration with deduplication."""
        config_hash = hashlib.md5(config.encode()).hexdigest()
        
        if config_hash in self.processed_configs:
            self.duplicate_configs.add(config_hash)
        else:
            self.processed_configs.add(config_hash)
            self.recent_configs.append(config)
    
    def is_duplicate(self, config: str) -> bool:
        """Check if configuration is duplicate."""
        config_hash = hashlib.md5(config.encode()).hexdigest()
        return config_hash in self.processed_configs
    
    def get_stats(self) -> Dict[str, Any]:
        """Get data structure statistics."""
        return {
            'processed_configs': len(self.processed_configs),
            'duplicate_configs': len(self.duplicate_configs),
            'recent_configs': len(self.recent_configs),
            'processing_queue': len(self.processing_queue),
            'cache_size': len(self.config_cache)
        }


class PerformanceOptimizer:
    """Main performance optimization coordinator."""
    
    def __init__(self, 
                 cache_size: int = 1000,
                 max_connections: int = 100,
                 requests_per_second: float = 10.0,
                 max_memory_mb: int = 512):
        
        # Initialize components
        self.cache = LRUCache(max_size=cache_size)
        self.connection_pool = ConnectionPool(max_connections=max_connections)
        self.rate_limiter = RateLimiter(requests_per_second=requests_per_second)
        self.memory_monitor = MemoryMonitor(max_memory_mb=max_memory_mb)
        self.data_structures = OptimizedDataStructures()
        
        # Performance metrics
        self.metrics = PerformanceMetrics()
        
        # Configuration cache
        self._config_cache: Dict[str, Any] = {}
        self._source_cache: Dict[str, List[str]] = {}
        
        logger.info("Performance optimizer initialized")
    
    async def get_optimized_session(self) -> aiohttp.ClientSession:
        """Get optimized HTTP session with rate limiting."""
        # Check rate limit
        if not await self.rate_limiter.acquire():
            self.metrics.rate_limit_hits += 1
            await asyncio.sleep(0.1)  # Brief delay
        
        return await self.connection_pool.get_session()
    
    async def cache_config(self, key: str, config: Any) -> None:
        """Cache configuration with automatic cleanup."""
        await self.cache.set(key, config)
        self.metrics.cache_hits += 1
    
    async def get_cached_config(self, key: str) -> Optional[Any]:
        """Get cached configuration."""
        result = await self.cache.get(key)
        if result is not None:
            self.metrics.cache_hits += 1
        else:
            self.metrics.cache_misses += 1
        return result
    
    async def optimize_data_processing(self, configs: List[str]) -> List[str]:
        """Optimize data processing with deduplication."""
        optimized_configs = []
        
        for config in configs:
            if not self.data_structures.is_duplicate(config):
                optimized_configs.append(config)
                self.data_structures.add_processed_config(config)
            else:
                self.metrics.deduplication_saves += 1
        
        return optimized_configs
    
    async def monitor_and_cleanup(self) -> Dict[str, Any]:
        """Monitor performance and perform cleanup if needed."""
        cleanup_stats = {}
        
        # Check memory pressure
        if await self.memory_monitor.check_memory_pressure():
            cleanup_stats = await self.memory_monitor.force_cleanup()
            
            # Clear old cache entries
            if self.cache.size() > 500:
                await self.cache.clear()
            
            # Clear old data structures
            if len(self.data_structures.recent_configs) > 500:
                # Keep only recent entries
                recent = list(self.data_structures.recent_configs)[-250:]
                self.data_structures.recent_configs.clear()
                self.data_structures.recent_configs.extend(recent)
        
        # Update metrics
        self.metrics.memory_usage = self.memory_monitor.get_memory_usage()
        self.metrics.connection_pool_size = await self.connection_pool.get_active_connections()
        
        return cleanup_stats
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        cache_hit_rate = 0.0
        total_cache_requests = self.metrics.cache_hits + self.metrics.cache_misses
        if total_cache_requests > 0:
            cache_hit_rate = self.metrics.cache_hits / total_cache_requests
        
        return {
            'memory_usage_mb': self.metrics.memory_usage,
            'cache_hit_rate': cache_hit_rate,
            'cache_size': self.cache.size(),
            'active_connections': self.metrics.connection_pool_size,
            'rate_limit_hits': self.metrics.rate_limit_hits,
            'deduplication_saves': self.metrics.deduplication_saves,
            'data_structures': self.data_structures.get_stats(),
            'processing_time': self.metrics.processing_time
        }
    
    async def cleanup(self) -> None:
        """Cleanup all resources."""
        await self.connection_pool.close()
        await self.cache.clear()
        logger.info("Performance optimizer cleaned up")


# Global performance optimizer instance
_performance_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get global performance optimizer instance."""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer


async def cleanup_performance_optimizer() -> None:
    """Cleanup global performance optimizer."""
    global _performance_optimizer
    if _performance_optimizer is not None:
        await _performance_optimizer.cleanup()
        _performance_optimizer = None
