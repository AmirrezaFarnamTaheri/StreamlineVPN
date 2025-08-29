from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge, Summary, Info, generate_latest, CONTENT_TYPE_LATEST
import psutil
import time
import threading
import asyncio
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class MetricsSnapshot:
    """Snapshot of current metrics for reporting."""
    timestamp: datetime
    configs_processed: int
    sources_fetched: int
    active_connections: int
    memory_usage_bytes: int
    cpu_usage_percent: float
    processing_duration_avg: float
    error_rate: float
    cache_hit_rate: float
    source_reliability_avg: float

class MetricsCollector:
    """Comprehensive metrics collection for VPN Merger application."""
    
    def __init__(self, app_name: str = "vpn_merger", app_version: str = "2.0.0"):
        self.app_name = app_name
        self.app_version = app_version
        self.start_time = datetime.now()
        
        # Application info
        self.app_info = Info('vpn_merger_app', 'VPN Merger application information')
        self.app_info.info({
            'name': app_name,
            'version': app_version,
            'start_time': self.start_time.isoformat()
        })
        
        # Counters
        self.configs_processed = Counter(
            'vpn_merger_configs_processed_total',
            'Total configs processed',
            ['protocol', 'status', 'source']
        )
        
        self.sources_fetched = Counter(
            'vpn_merger_sources_fetched_total',
            'Total sources fetched',
            ['status', 'source_type', 'region']
        )
        
        self.errors_total = Counter(
            'vpn_merger_errors_total',
            'Total errors encountered',
            ['error_type', 'component', 'severity']
        )
        
        self.cache_operations = Counter(
            'vpn_merger_cache_operations_total',
            'Total cache operations',
            ['operation', 'cache_tier', 'result']
        )
        
        # Histograms
        self.processing_duration = Histogram(
            'vpn_merger_processing_duration_seconds',
            'Processing duration for different stages',
            ['stage', 'protocol'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
        )
        
        self.config_latency = Histogram(
            'vpn_merger_config_latency_ms',
            'Config connection latency',
            ['protocol', 'region'],
            buckets=[10, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
        )
        
        self.source_response_time = Histogram(
            'vpn_merger_source_response_time_seconds',
            'Source response time',
            ['source', 'status'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )
        
        self.http_request_duration = Histogram(
            'vpn_merger_http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint', 'status_code'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )
        
        # Gauges
        self.active_connections = Gauge(
            'vpn_merger_active_connections',
            'Number of active connections'
        )
        
        self.memory_usage = Gauge(
            'vpn_merger_memory_usage_bytes',
            'Memory usage in bytes'
        )
        
        self.cpu_usage = Gauge(
            'vpn_merger_cpu_usage_percent',
            'CPU usage percentage'
        )
        
        self.disk_usage = Gauge(
            'vpn_merger_disk_usage_bytes',
            'Disk usage in bytes'
        )
        
        self.queue_size = Gauge(
            'vpn_merger_queue_size',
            'Current queue size',
            ['queue_name']
        )
        
        self.cache_size = Gauge(
            'vpn_merger_cache_size',
            'Cache size in items',
            ['cache_tier']
        )
        
        self.source_count = Gauge(
            'vpn_merger_source_count',
            'Number of sources by status',
            ['status', 'tier']
        )
        
        # Summaries
        self.source_reliability = Summary(
            'vpn_merger_source_reliability',
            'Source reliability score',
            ['source', 'tier']
        )
        
        self.config_quality = Summary(
            'vpn_merger_config_quality',
            'Config quality score',
            ['protocol', 'source']
        )
        
        self.processing_throughput = Summary(
            'vpn_merger_processing_throughput',
            'Configs processed per second',
            ['stage']
        )
        
        # Internal state
        self._metrics_history: List[MetricsSnapshot] = []
        self._max_history_size = 1000
        self._lock = threading.Lock()
        
        # Start background metrics collection
        self._start_system_metrics()
        self._start_periodic_snapshot()
    
    def _start_system_metrics(self):
        """Collect system metrics in background thread."""
        def collect_system_metrics():
            while True:
                try:
                    process = psutil.Process()
                    
                    # Memory metrics
                    memory_info = process.memory_info()
                    self.memory_usage.set(memory_info.rss)
                    
                    # CPU metrics
                    cpu_percent = process.cpu_percent()
                    self.cpu_usage.set(cpu_percent)
                    
                    # Disk metrics
                    try:
                        disk_usage = psutil.disk_usage('.')
                        self.disk_usage.set(disk_usage.used)
                    except Exception as e:
                        logger.debug(f"Could not collect disk metrics: {e}")
                    
                    time.sleep(10)  # Collect every 10 seconds
                    
                except Exception as e:
                    logger.error(f"Error collecting system metrics: {e}")
                    time.sleep(30)  # Wait longer on error
        
        thread = threading.Thread(target=collect_system_metrics, daemon=True)
        thread.start()
        logger.info("System metrics collection started")
    
    def _start_periodic_snapshot(self):
        """Take periodic snapshots of metrics."""
        def take_snapshots():
            while True:
                try:
                    snapshot = self._create_snapshot()
                    with self._lock:
                        self._metrics_history.append(snapshot)
                        if len(self._metrics_history) > self._max_history_size:
                            self._metrics_history.pop(0)
                    
                    time.sleep(60)  # Take snapshot every minute
                    
                except Exception as e:
                    logger.error(f"Error taking metrics snapshot: {e}")
                    time.sleep(120)  # Wait longer on error
        
        thread = threading.Thread(target=take_snapshots, daemon=True)
        thread.start()
        logger.info("Periodic metrics snapshots started")
    
    def _create_snapshot(self) -> MetricsSnapshot:
        """Create a snapshot of current metrics."""
        # Get current values from Prometheus metrics
        # Note: This is a simplified approach - in production you might want to
        # use Prometheus client's built-in methods or custom collectors
        
        return MetricsSnapshot(
            timestamp=datetime.now(),
            configs_processed=0,  # Would need to track this separately
            sources_fetched=0,    # Would need to track this separately
            active_connections=0,  # Would need to track this separately
            memory_usage_bytes=psutil.Process().memory_info().rss,
            cpu_usage_percent=psutil.Process().cpu_percent(),
            processing_duration_avg=0.0,
            error_rate=0.0,
            cache_hit_rate=0.0,
            source_reliability_avg=0.0
        )
    
    # Public API methods
    
    def record_config(self, protocol: str, status: str, source: str = "unknown"):
        """Record config processing."""
        self.configs_processed.labels(protocol=protocol, status=status, source=source).inc()
    
    def record_source_fetch(self, status: str, source_type: str = "unknown", region: str = "unknown"):
        """Record source fetch operation."""
        self.sources_fetched.labels(status=status, source_type=source_type, region=region).inc()
    
    def record_error(self, error_type: str, component: str, severity: str = "error"):
        """Record an error."""
        self.errors_total.labels(error_type=error_type, component=component, severity=severity).inc()
    
    def record_cache_operation(self, operation: str, cache_tier: str, result: str):
        """Record cache operation."""
        self.cache_operations.labels(operation=operation, cache_tier=cache_tier, result=result).inc()
    
    def record_latency(self, protocol: str, latency_ms: float, region: str = "unknown"):
        """Record connection latency."""
        self.config_latency.labels(protocol=protocol, region=region).observe(latency_ms)
    
    def record_source_response_time(self, source: str, status: str, response_time: float):
        """Record source response time."""
        self.source_response_time.labels(source=source, status=status).observe(response_time)
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        self.http_request_duration.labels(method=method, endpoint=endpoint, status_code=status_code).observe(duration)
    
    def set_active_connections(self, count: int):
        """Set active connections count."""
        self.active_connections.set(count)
    
    def set_queue_size(self, queue_name: str, size: int):
        """Set queue size."""
        self.queue_size.labels(queue_name=queue_name).set(size)
    
    def set_cache_size(self, cache_tier: str, size: int):
        """Set cache size."""
        self.cache_size.labels(cache_tier=cache_tier).set(size)
    
    def set_source_count(self, status: str, tier: str, count: int):
        """Set source count."""
        self.source_count.labels(status=status, tier=tier).set(count)
    
    def observe_source_reliability(self, source: str, tier: str, reliability: float):
        """Observe source reliability score."""
        self.source_reliability.labels(source=source, tier=tier).observe(reliability)
    
    def observe_config_quality(self, protocol: str, source: str, quality: float):
        """Observe config quality score."""
        self.config_quality.labels(protocol=protocol, source=source).observe(quality)
    
    def observe_processing_throughput(self, stage: str, throughput: float):
        """Observe processing throughput."""
        self.processing_throughput.labels(stage=stage).observe(throughput)
    
    def time_stage(self, stage: str, protocol: str = "unknown"):
        """Context manager for timing processing stages."""
        return self.processing_duration.labels(stage=stage, protocol=protocol).time()
    
    def time_http_request(self, method: str, endpoint: str):
        """Context manager for timing HTTP requests."""
        return self.http_request_duration.labels(method=method, endpoint=endpoint, status_code=0).time()
    
    # Metrics export and reporting
    
    def get_metrics_prometheus(self) -> bytes:
        """Get metrics in Prometheus format."""
        return generate_latest()
    
    def get_metrics_json(self) -> Dict[str, Any]:
        """Get metrics in JSON format for API endpoints."""
        return {
            'app_info': {
                'name': self.app_name,
                'version': self.app_version,
                'start_time': self.start_time.isoformat(),
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
            },
            'current_metrics': {
                'active_connections': self.active_connections._value.get(),
                'memory_usage_bytes': self.memory_usage._value.get(),
                'cpu_usage_percent': self.cpu_usage._value.get(),
                'disk_usage_bytes': self.disk_usage._value.get()
            },
            'snapshots': len(self._metrics_history),
            'last_snapshot': self._metrics_history[-1].timestamp.isoformat() if self._metrics_history else None
        }
    
    def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history for the specified time period."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            recent_snapshots = [
                snapshot for snapshot in self._metrics_history
                if snapshot.timestamp >= cutoff
            ]
        
        return [
            {
                'timestamp': snapshot.timestamp.isoformat(),
                'memory_usage_bytes': snapshot.memory_usage_bytes,
                'cpu_usage_percent': snapshot.cpu_usage_percent,
                'active_connections': snapshot.active_connections,
                'configs_processed': snapshot.configs_processed,
                'sources_fetched': snapshot.sources_fetched
            }
            for snapshot in recent_snapshots
        ]
    
    def export_metrics_report(self, output_path: str = "metrics_report.json"):
        """Export comprehensive metrics report."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'app_info': {
                'name': self.app_name,
                'version': self.app_version,
                'start_time': self.start_time.isoformat(),
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
            },
            'current_metrics': self.get_metrics_json(),
            'history': self.get_metrics_history(hours=24),
            'summary': {
                'total_snapshots': len(self._metrics_history),
                'snapshot_interval_minutes': 1,
                'retention_hours': 24
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Metrics report exported to {output_path}")
        return output_path
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)."""
        # Note: This is a simplified reset - in production you might want to
        # implement a more sophisticated reset mechanism
        logger.warning("Metrics reset requested - this will clear all collected metrics")
        
        # Reset counters and gauges to initial values
        # Note: Prometheus client doesn't provide a direct reset method
        # This would need to be implemented based on your specific needs
        
        # Clear history
        with self._lock:
            self._metrics_history.clear()
        
        logger.info("Metrics reset completed")

# Global metrics instance
_metrics_collector: Optional[MetricsCollector] = None

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

def record_config(protocol: str, status: str, source: str = "unknown"):
    """Record config processing using global metrics collector."""
    get_metrics_collector().record_config(protocol, status, source)

def record_source_fetch(status: str, source_type: str = "unknown", region: str = "unknown"):
    """Record source fetch using global metrics collector."""
    get_metrics_collector().record_source_fetch(status, source_type, region)

def record_error(error_type: str, component: str, severity: str = "error"):
    """Record error using global metrics collector."""
    get_metrics_collector().record_error(error_type, component, severity)

def time_stage(stage: str, protocol: str = "unknown"):
    """Time processing stage using global metrics collector."""
    return get_metrics_collector().time_stage(stage, protocol)

