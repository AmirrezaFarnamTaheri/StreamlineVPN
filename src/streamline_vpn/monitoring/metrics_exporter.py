"""
Metrics Exporter
================

Prometheus metrics export functionality.
"""

import time
from typing import Dict, Any

from .metrics_collector import MetricsCollector


class MetricsExporter:
    """Prometheus metrics exporter."""

    def __init__(self, collector: MetricsCollector):
        """Initialize metrics exporter.

        Args:
            collector: Metrics collector instance
        """
        self.collector = collector

    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        output = []

        for metric_name, metric_data in self.collector.metrics.items():
            metric_type = metric_data["type"].value
            help_text = metric_data["help"]

            # Add HELP line
            output.append(f"# HELP {metric_name} {help_text}")
            output.append(f"# TYPE {metric_name} {metric_type}")

            # Add metric values
            for label_key, value_data in metric_data["values"].items():
                labels = value_data["labels"]
                label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())

                if metric_type == "histogram":
                    # Export histogram buckets
                    for bucket_key, count in value_data["buckets"].items():
                        output.append(
                            f"{metric_name}_bucket{{{label_str},{bucket_key}}} {count}"
                        )

                    # Export count and sum
                    output.append(
                        f"{metric_name}_count{{{label_str}}} {value_data['count']}"
                    )
                    output.append(
                        f"{metric_name}_sum{{{label_str}}} {value_data['sum']}"
                    )
                else:
                    # Export simple metric
                    output.append(
                        f"{metric_name}{{{label_str}}} {value_data['value']}"
                    )

            output.append("")  # Empty line between metrics

        return "\n".join(output)
