import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.monitoring.metrics_exporter import MetricsExporter


def test_exporter_formatters_basic():
    exporter = MetricsExporter()
    metrics = {"a": 1, "b": 2}

    js = exporter.export_to_json(metrics)
    assert "\n" in js and '"a": 1' in js

    csv = exporter.export_to_csv(metrics)
    assert "metric,value" in csv and "a,1" in csv

    yaml = exporter.export_to_yaml(metrics)
    assert "a: 1" in yaml and "b: 2" in yaml

    prom = exporter.export_to_prometheus(metrics)
    assert "# HELP" in prom and "a 1" in prom and "b 2" in prom


