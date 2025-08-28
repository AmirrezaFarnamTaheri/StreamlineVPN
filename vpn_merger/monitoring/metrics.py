from prometheus_client import Counter, Histogram, Gauge, start_http_server, CollectorRegistry
import time
import psutil
import threading


class VPNMergerMetrics:
    def __init__(self, port: int = 8001):
        self.registry = CollectorRegistry()
        self.sources_processed = Counter('vpn_sources_processed_total', 'Total number of sources processed', ['status'], registry=self.registry)
        self.configs_found = Counter('vpn_configs_found_total', 'Total number of configs found', ['protocol', 'source_type'], registry=self.registry)
        self.connection_tests = Counter('vpn_connection_tests_total', 'Total number of connection tests', ['result'], registry=self.registry)
        self.connection_test_duration = Histogram('vpn_connection_test_duration_seconds', 'Time spent testing connections', buckets=[0.1,0.5,1.0,2.0,5.0,10.0], registry=self.registry)
        self.config_quality_score = Histogram('vpn_config_quality_score', 'Quality scores of configurations', buckets=[0,10,20,30,40,50,60,70,80,90,100], registry=self.registry)
        self.memory_usage = Gauge('vpn_merger_memory_usage_bytes', 'Current memory usage', registry=self.registry)
        self.cpu_usage = Gauge('vpn_merger_cpu_usage_percent', 'Current CPU usage percent', registry=self.registry)
        self.active_configs = Gauge('vpn_active_configs_count', 'Number of active/working configs', registry=self.registry)
        start_http_server(port, registry=self.registry)
        self._start_system_metrics_collection()

    def _start_system_metrics_collection(self):
        def collect_system_metrics():
            while True:
                try:
                    process = psutil.Process()
                    self.memory_usage.set(process.memory_info().rss)
                    self.cpu_usage.set(process.cpu_percent())
                    time.sleep(10)
                except Exception:
                    time.sleep(10)
        threading.Thread(target=collect_system_metrics, daemon=True).start()

    def record_source_processed(self, success: bool):
        status = 'success' if success else 'failure'
        self.sources_processed.labels(status=status).inc()

    def record_config_found(self, protocol: str, source_type: str):
        self.configs_found.labels(protocol=protocol, source_type=source_type).inc()

    def record_connection_test(self, duration: float, success: bool):
        self.connection_tests.labels(result='success' if success else 'failure').inc()
        self.connection_test_duration.observe(duration)

    def record_quality_score(self, score: float):
        self.config_quality_score.observe(score)

    def set_active_configs(self, count: int):
        self.active_configs.set(count)


