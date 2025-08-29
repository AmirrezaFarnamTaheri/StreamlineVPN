from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge
import psutil
import time
import threading


class MetricsCollector:
    """Comprehensive metrics collection compatible with Prometheus client."""

    def __init__(self):
        # Counters
        self.configs_processed = Counter(
            'vpn_merger_configs_processed_total',
            'Total configs processed',
            ['protocol', 'status']
        )

        self.sources_fetched = Counter(
            'vpn_merger_sources_fetched_total',
            'Total sources fetched',
            ['status']
        )

        # Histograms
        self.processing_duration = Histogram(
            'vpn_merger_processing_duration_seconds',
            'Processing duration',
            ['stage'],
            buckets=[.1, .5, 1, 2, 5, 10, 30, 60, 120, 300]
        )

        self.config_latency = Histogram(
            'vpn_merger_config_latency_ms',
            'Config connection latency',
            ['protocol'],
            buckets=[10, 50, 100, 200, 500, 1000, 2000, 5000]
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

        # Start background metrics collection
        self._start_system_metrics()

    def _start_system_metrics(self):
        def collect():
            proc = psutil.Process()
            while True:
                try:
                    self.memory_usage.set(proc.memory_info().rss)
                    self.cpu_usage.set(proc.cpu_percent())
                except Exception:
                    pass
                time.sleep(10)
        t = threading.Thread(target=collect, daemon=True)
        t.start()

    def record_config(self, protocol: str, status: str):
        self.configs_processed.labels(protocol=protocol, status=status).inc()

    def record_latency(self, protocol: str, latency_ms: float):
        self.config_latency.labels(protocol=protocol).observe(latency_ms)

    def time_stage(self, stage: str):
        return self.processing_duration.labels(stage=stage).time()

