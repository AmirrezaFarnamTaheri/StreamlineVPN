# Performance Tuning Guide

## Overview

This guide provides comprehensive performance tuning recommendations for the VPN Subscription Merger system. It covers system-level optimizations, application configuration, resource management, and monitoring strategies to achieve optimal performance.

## System Requirements

### Minimum Requirements

| Component | Minimum | Recommended | High Performance |
|-----------|---------|-------------|------------------|
| CPU | 2 cores | 4 cores | 8+ cores |
| RAM | 2GB | 8GB | 16GB+ |
| Storage | 10GB SSD | 50GB SSD | 100GB+ NVMe SSD |
| Network | 100 Mbps | 1 Gbps | 10 Gbps+ |

### Operating System Optimizations

#### Linux Kernel Tuning

```bash
# /etc/sysctl.conf
# Network optimizations
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_congestion_control = bbr

# File descriptor limits
fs.file-max = 2097152
fs.nr_open = 2097152

# Memory management
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# Apply changes
sysctl -p
```

#### File Descriptor Limits

```bash
# /etc/security/limits.conf
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768

# For systemd services
# /etc/systemd/system/vpn-merger.service
[Service]
LimitNOFILE=65536
LimitNPROC=32768
```

#### CPU Governor

```bash
# Set CPU governor to performance
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Make permanent
echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpufrequtils
```

## Application Configuration

### Concurrency Settings

#### Optimal Concurrency Calculation

```python
import os
import psutil

def calculate_optimal_concurrency():
    """Calculate optimal concurrency based on system resources."""
    
    # Get system information
    cpu_count = os.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    # Calculate optimal concurrency
    # Base: 2x CPU cores
    base_concurrency = cpu_count * 2
    
    # Memory factor: 1 additional per 2GB RAM
    memory_factor = int(memory_gb / 2)
    
    # Network factor: Assume 1 Gbps = 100 concurrent connections
    network_factor = 100
    
    # Calculate final concurrency
    optimal_concurrency = min(
        base_concurrency + memory_factor,
        network_factor,
        200  # Maximum limit
    )
    
    return max(optimal_concurrency, 10)  # Minimum 10

# Set optimal concurrency
optimal_concurrency = calculate_optimal_concurrency()
os.environ['VPN_CONCURRENT_LIMIT'] = str(optimal_concurrency)
```

#### Environment Variable Configuration

```bash
# High-performance configuration
export VPN_CONCURRENT_LIMIT=100
export VPN_BATCH_SIZE=20
export VPN_TIMEOUT=30
export VPN_MAX_RETRIES=3

# Memory optimization
export VPN_CHUNK_SIZE=2097152  # 2MB
export VPN_BLOOM_FILTER_SIZE=2000000
export VPN_SEMAPHORE_LIMIT=50

# Cache optimization
export VPN_CACHE_ENABLED=true
export VPN_CACHE_TTL=7200  # 2 hours
export VPN_REDIS_URL="redis://localhost:6379/0"
```

### Memory Management

#### Memory Pool Configuration

```python
import gc
import psutil
from typing import Dict, Any

class MemoryManager:
    """Advanced memory management for VPN Merger."""
    
    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_mb = max_memory_mb
        self.cleanup_threshold = 0.8  # 80% memory usage
        self.cleanup_interval = 30    # seconds
        
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def should_cleanup(self) -> bool:
        """Check if memory cleanup is needed."""
        current_memory = self.get_memory_usage()
        return current_memory > (self.max_memory_mb * self.cleanup_threshold)
    
    def force_cleanup(self) -> Dict[str, Any]:
        """Force memory cleanup and return statistics."""
        before_memory = self.get_memory_usage()
        
        # Force garbage collection
        collected = gc.collect()
        
        after_memory = self.get_memory_usage()
        
        return {
            'before_mb': before_memory,
            'after_mb': after_memory,
            'freed_mb': before_memory - after_memory,
            'objects_collected': collected
        }
    
    def monitor_memory(self):
        """Monitor memory usage and cleanup when needed."""
        if self.should_cleanup():
            cleanup_stats = self.force_cleanup()
            print(f"Memory cleanup: {cleanup_stats['freed_mb']:.2f}MB freed")
```

#### Efficient Data Structures

```python
from collections import deque, defaultdict
from typing import Set, Dict, List
import hashlib

class OptimizedDataStructures:
    """Optimized data structures for better performance."""
    
    def __init__(self):
        # Use sets for O(1) lookups instead of lists
        self.processed_configs: Set[str] = set()
        self.duplicate_configs: Set[str] = set()
        
        # Use defaultdict for efficient counting
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.processing_times: Dict[str, float] = {}
        
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
```

### Caching Strategy

#### Multi-Level Caching

```python
import asyncio
import time
from typing import Any, Optional, Dict
from collections import OrderedDict

class MultiLevelCache:
    """Multi-level caching system for optimal performance."""
    
    def __init__(self, l1_size: int = 1000, l2_size: int = 10000):
        # L1: In-memory LRU cache (fastest)
        self.l1_cache = OrderedDict()
        self.l1_size = l1_size
        
        # L2: Redis cache (fast, persistent)
        self.l2_cache = None  # Redis connection
        self.l2_size = l2_size
        
        # Cache statistics
        self.stats = {
            'l1_hits': 0,
            'l1_misses': 0,
            'l2_hits': 0,
            'l2_misses': 0,
            'total_requests': 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback."""
        self.stats['total_requests'] += 1
        
        # Try L1 cache first
        if key in self.l1_cache:
            self.stats['l1_hits'] += 1
            # Move to end (most recently used)
            value = self.l1_cache.pop(key)
            self.l1_cache[key] = value
            return value
        
        self.stats['l1_misses'] += 1
        
        # Try L2 cache
        if self.l2_cache:
            try:
                value = await self.l2_cache.get(key)
                if value is not None:
                    self.stats['l2_hits'] += 1
                    # Promote to L1 cache
                    await self.set(key, value)
                    return value
                else:
                    self.stats['l2_misses'] += 1
            except Exception:
                pass
        
        return None
    
    async def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        # Set in L1 cache
        if key in self.l1_cache:
            self.l1_cache.pop(key)
        elif len(self.l1_cache) >= self.l1_size:
            # Remove least recently used
            self.l1_cache.popitem(last=False)
        
        self.l1_cache[key] = value
        
        # Set in L2 cache
        if self.l2_cache:
            try:
                await self.l2_cache.set(key, value, ex=3600)  # 1 hour TTL
            except Exception:
                pass
    
    def get_hit_rate(self) -> float:
        """Get cache hit rate."""
        total_hits = self.stats['l1_hits'] + self.stats['l2_hits']
        return total_hits / self.stats['total_requests'] if self.stats['total_requests'] > 0 else 0
```

#### Redis Configuration

```bash
# redis.conf optimizations
# Memory optimization
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence optimization
save 900 1
save 300 10
save 60 10000

# Network optimization
tcp-keepalive 60
timeout 300

# Performance optimization
tcp-backlog 511
databases 16
```

### Network Optimization

#### Connection Pooling

```python
import aiohttp
import asyncio
from typing import Optional

class OptimizedConnectionPool:
    """Optimized HTTP connection pool."""
    
    def __init__(self, 
                 max_connections: int = 100,
                 max_connections_per_host: int = 30,
                 keepalive_timeout: int = 30):
        
        self.max_connections = max_connections
        self.max_connections_per_host = max_connections_per_host
        self.keepalive_timeout = keepalive_timeout
        
        # Create optimized connector
        self.connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=max_connections_per_host,
            keepalive_timeout=keepalive_timeout,
            enable_cleanup_closed=True,
            use_dns_cache=True,
            ttl_dns_cache=300,  # 5 minutes DNS cache
            family=0,  # Allow both IPv4 and IPv6
        )
        
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
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
```

#### Rate Limiting

```python
import asyncio
import time
from typing import Dict, Optional

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
```

## Database Optimization

### SQLite Optimization

```python
import sqlite3
import asyncio
from typing import List, Dict, Any

class OptimizedSQLite:
    """Optimized SQLite database operations."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
    
    async def connect(self):
        """Connect to database with optimizations."""
        self.connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0
        )
        
        # Enable optimizations
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute("PRAGMA cache_size=10000")
        self.connection.execute("PRAGMA temp_store=MEMORY")
        self.connection.execute("PRAGMA mmap_size=268435456")  # 256MB
    
    async def bulk_insert(self, table: str, data: List[Dict[str, Any]]):
        """Bulk insert for better performance."""
        if not data:
            return
        
        # Prepare statement
        columns = list(data[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        
        # Execute bulk insert
        values = [tuple(row[col] for col in columns) for row in data]
        self.connection.executemany(query, values)
        self.connection.commit()
    
    async def create_indexes(self):
        """Create optimized indexes."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_configs_host ON configs(host)",
            "CREATE INDEX IF NOT EXISTS idx_configs_protocol ON configs(protocol)",
            "CREATE INDEX IF NOT EXISTS idx_configs_quality ON configs(quality_score)",
            "CREATE INDEX IF NOT EXISTS idx_configs_created ON configs(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_sources_url ON sources(url)",
            "CREATE INDEX IF NOT EXISTS idx_sources_tier ON sources(tier)",
        ]
        
        for index_query in indexes:
            self.connection.execute(index_query)
        self.connection.commit()
```

## Monitoring and Profiling

### Performance Monitoring

```python
import time
import psutil
import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass, field
from collections import deque

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    timestamp: float = field(default_factory=time.time)
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    network_io: Dict[str, int] = field(default_factory=dict)
    disk_io: Dict[str, int] = field(default_factory=dict)
    active_connections: int = 0
    requests_per_second: float = 0.0
    response_time_ms: float = 0.0
    error_rate: float = 0.0

class PerformanceMonitor:
    """Real-time performance monitoring."""
    
    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.metrics_history = deque(maxlen=history_size)
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.response_times = deque(maxlen=100)
    
    def record_request(self, response_time_ms: float, is_error: bool = False):
        """Record a request."""
        self.request_count += 1
        if is_error:
            self.error_count += 1
        self.response_times.append(response_time_ms)
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        process = psutil.Process()
        
        # CPU and memory
        cpu_percent = process.cpu_percent()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # Network I/O
        net_io = psutil.net_io_counters()._asdict()
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
        
        # Calculate rates
        uptime = time.time() - self.start_time
        requests_per_second = self.request_count / uptime if uptime > 0 else 0
        error_rate = self.error_count / self.request_count if self.request_count > 0 else 0
        
        # Average response time
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        metrics = PerformanceMetrics(
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            network_io=net_io,
            disk_io=disk_io,
            active_connections=len(psutil.net_connections()),
            requests_per_second=requests_per_second,
            response_time_ms=avg_response_time,
            error_rate=error_rate
        )
        
        self.metrics_history.append(metrics)
        return metrics
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.metrics_history:
            return {}
        
        recent_metrics = list(self.metrics_history)[-100:]  # Last 100 samples
        
        return {
            'avg_cpu_percent': sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            'avg_memory_mb': sum(m.memory_mb for m in recent_metrics) / len(recent_metrics),
            'avg_requests_per_second': sum(m.requests_per_second for m in recent_metrics) / len(recent_metrics),
            'avg_response_time_ms': sum(m.response_time_ms for m in recent_metrics) / len(recent_metrics),
            'avg_error_rate': sum(m.error_rate for m in recent_metrics) / len(recent_metrics),
            'total_requests': self.request_count,
            'total_errors': self.error_count,
            'uptime_seconds': time.time() - self.start_time
        }
```

### Profiling Tools

#### CPU Profiling

```python
import cProfile
import pstats
import io
from contextlib import contextmanager

@contextmanager
def profile_function(func_name: str):
    """Profile a function's performance."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    try:
        yield
    finally:
        profiler.disable()
        
        # Generate report
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions
        
        print(f"Profile for {func_name}:")
        print(s.getvalue())

# Usage example
async def process_sources():
    with profile_function("process_sources"):
        # Your code here
        pass
```

#### Memory Profiling

```python
import tracemalloc
from contextlib import contextmanager

@contextmanager
def memory_profile():
    """Profile memory usage."""
    tracemalloc.start()
    
    try:
        yield
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"Current memory usage: {current / 1024 / 1024:.2f} MB")
        print(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")

# Usage example
async def process_large_dataset():
    with memory_profile():
        # Your code here
        pass
```

## Benchmarking

### Performance Benchmarks

```python
import asyncio
import time
import statistics
from typing import List, Dict, Any

class PerformanceBenchmark:
    """Performance benchmarking suite."""
    
    def __init__(self):
        self.results = {}
    
    async def benchmark_concurrent_processing(self, 
                                            sources: List[str], 
                                            concurrency_levels: List[int]) -> Dict[int, Dict[str, float]]:
        """Benchmark concurrent processing performance."""
        
        results = {}
        
        for concurrency in concurrency_levels:
            print(f"Benchmarking concurrency level: {concurrency}")
            
            # Run benchmark
            start_time = time.time()
            
            # Simulate processing with semaphore
            semaphore = asyncio.Semaphore(concurrency)
            
            async def process_source(source: str):
                async with semaphore:
                    # Simulate processing time
                    await asyncio.sleep(0.1)
                    return f"processed_{source}"
            
            tasks = [process_source(source) for source in sources]
            await asyncio.gather(*tasks)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            results[concurrency] = {
                'processing_time': processing_time,
                'throughput': len(sources) / processing_time,
                'efficiency': len(sources) / (processing_time * concurrency)
            }
        
        return results
    
    async def benchmark_memory_usage(self, data_sizes: List[int]) -> Dict[int, Dict[str, float]]:
        """Benchmark memory usage with different data sizes."""
        
        results = {}
        
        for size in data_sizes:
            print(f"Benchmarking memory usage with {size} items")
            
            # Measure memory before
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024
            
            # Create data
            data = [f"item_{i}" for i in range(size)]
            
            # Measure memory after
            memory_after = process.memory_info().rss / 1024 / 1024
            memory_used = memory_after - memory_before
            
            results[size] = {
                'memory_used_mb': memory_used,
                'memory_per_item_kb': (memory_used * 1024) / size
            }
        
        return results
    
    def generate_report(self) -> str:
        """Generate performance benchmark report."""
        report = []
        report.append("Performance Benchmark Report")
        report.append("=" * 50)
        
        for test_name, results in self.results.items():
            report.append(f"\n{test_name}:")
            report.append("-" * 30)
            
            for metric, value in results.items():
                if isinstance(value, dict):
                    report.append(f"  {metric}:")
                    for sub_metric, sub_value in value.items():
                        report.append(f"    {sub_metric}: {sub_value:.2f}")
                else:
                    report.append(f"  {metric}: {value:.2f}")
        
        return "\n".join(report)

# Usage example
async def run_benchmarks():
    benchmark = PerformanceBenchmark()
    
    # Benchmark concurrent processing
    sources = [f"source_{i}" for i in range(100)]
    concurrency_levels = [10, 25, 50, 100]
    
    concurrent_results = await benchmark.benchmark_concurrent_processing(sources, concurrency_levels)
    benchmark.results['concurrent_processing'] = concurrent_results
    
    # Benchmark memory usage
    data_sizes = [1000, 5000, 10000, 50000]
    memory_results = await benchmark.benchmark_memory_usage(data_sizes)
    benchmark.results['memory_usage'] = memory_results
    
    # Generate report
    report = benchmark.generate_report()
    print(report)
```

## Optimization Checklist

### System-Level Optimizations

- [ ] **CPU Governor**: Set to performance mode
- [ ] **File Descriptors**: Increase limits to 65536+
- [ ] **Network Buffers**: Optimize TCP buffer sizes
- [ ] **Memory Management**: Configure swap and dirty ratios
- [ ] **Disk I/O**: Use SSD storage for better performance

### Application-Level Optimizations

- [ ] **Concurrency**: Set optimal concurrent limit based on system resources
- [ ] **Memory Management**: Implement periodic cleanup and garbage collection
- [ ] **Caching**: Enable multi-level caching with Redis
- [ ] **Connection Pooling**: Use optimized HTTP connection pools
- [ ] **Rate Limiting**: Implement token bucket rate limiting

### Database Optimizations

- [ ] **Indexes**: Create appropriate indexes for queries
- [ ] **WAL Mode**: Enable Write-Ahead Logging for SQLite
- [ ] **Cache Size**: Increase database cache size
- [ ] **Bulk Operations**: Use bulk insert/update operations
- [ ] **Connection Pooling**: Implement database connection pooling

### Monitoring and Profiling

- [ ] **Performance Monitoring**: Implement real-time performance tracking
- [ ] **Memory Profiling**: Monitor memory usage and leaks
- [ ] **CPU Profiling**: Profile CPU usage and bottlenecks
- [ ] **Network Monitoring**: Track network I/O and latency
- [ ] **Error Tracking**: Monitor error rates and types

## Performance Targets

### Response Time Targets

| Operation | Target | Acceptable | Poor |
|-----------|--------|------------|------|
| Source Fetch | < 2s | < 5s | > 10s |
| Configuration Generation | < 100ms | < 500ms | > 1s |
| API Response | < 50ms | < 200ms | > 500ms |
| Database Query | < 10ms | < 50ms | > 100ms |

### Throughput Targets

| Operation | Target | Acceptable | Poor |
|-----------|--------|------------|------|
| Sources per Second | > 50 | > 20 | < 10 |
| Configurations per Second | > 1000 | > 500 | < 100 |
| API Requests per Second | > 1000 | > 500 | < 100 |
| Database Operations per Second | > 10000 | > 5000 | < 1000 |

### Resource Usage Targets

| Resource | Target | Acceptable | Poor |
|----------|--------|------------|------|
| CPU Usage | < 70% | < 85% | > 95% |
| Memory Usage | < 80% | < 90% | > 95% |
| Disk I/O | < 80% | < 90% | > 95% |
| Network I/O | < 70% | < 85% | > 95% |

## Troubleshooting Performance Issues

### Common Performance Problems

1. **High CPU Usage**
   - Check for inefficient algorithms
   - Profile CPU usage to identify bottlenecks
   - Consider increasing concurrency limits
   - Optimize data structures

2. **High Memory Usage**
   - Check for memory leaks
   - Implement periodic cleanup
   - Use more efficient data structures
   - Consider streaming processing

3. **Slow Network Operations**
   - Check connection pooling
   - Implement rate limiting
   - Use DNS caching
   - Optimize request batching

4. **Database Performance Issues**
   - Check for missing indexes
   - Optimize queries
   - Use bulk operations
   - Consider connection pooling

### Performance Debugging Tools

```bash
# System monitoring
htop                    # CPU and memory usage
iotop                   # Disk I/O monitoring
nethogs                 # Network usage by process
ss -tuln                # Network connections

# Application profiling
python -m cProfile script.py
python -m memory_profiler script.py
py-spy top --pid <pid>  # Real-time profiling

# Database analysis
sqlite3 database.db ".schema"
sqlite3 database.db "EXPLAIN QUERY PLAN SELECT * FROM table"
```

This comprehensive performance tuning guide provides all the tools and techniques needed to optimize the VPN Subscription Merger system for maximum performance across different deployment scenarios.
