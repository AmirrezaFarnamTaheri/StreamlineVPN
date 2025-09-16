import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.monitoring.metrics_exporter import MetricsExporter


def test_metrics_exporter_filter_metrics_basic():
    exporter = MetricsExporter()
    exporter.add_export_metadata("env", "test")
    metrics = {
        "requests_total": {"values": {"": {"value": 10}}},
        "latency_ms": {"values": {"": {"value": 120}}},
    }
    filt = exporter.filter_metrics(metrics, include=["requests_total"])  # type: ignore[arg-type]
    assert "requests_total" in filt and "latency_ms" not in filt


