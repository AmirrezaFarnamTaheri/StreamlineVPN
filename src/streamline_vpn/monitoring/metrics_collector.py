"""
Metrics Collector
=================

Core metrics collection functionality for VPN monitoring.
"""

import time
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..utils.logging import get_logger

logger = get_logger(__name__)


class MetricType(Enum):
    """Metric types for monitoring."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricLabel:
    """Metric label for Prometheus."""

    name: str
    value: str


@dataclass
class VPNServerMetrics:
    """VPN server performance metrics."""

    server_id: str
    server_name: str
    protocol: str
    region: str
    active_connections: int
    total_connections: int
    bytes_uploaded: int
    bytes_downloaded: int
    avg_latency: float
    packet_loss_rate: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    last_updated: datetime


class MetricsCollector:
    """Core metrics collection functionality."""

    def __init__(self):
        """Initialize metrics collector."""
        self.metrics = {}
        self.collection_interval = 30  # seconds
        self.is_collecting = False
        self.collection_task = None

        # Initialize metric definitions
        self._initialize_metrics()

    def _initialize_metrics(self) -> None:
        """Initialize Prometheus metric definitions."""
        # VPN Connection Metrics
        self.metrics["vpn_connections_active"] = {
            "type": MetricType.GAUGE,
            "help": "Number of active VPN connections",
            "labels": ["server", "protocol", "region"],
            "values": {},
        }

        self.metrics["vpn_connections_total"] = {
            "type": MetricType.COUNTER,
            "help": "Total number of VPN connections",
            "labels": ["server", "protocol", "region", "status"],
            "values": {},
        }

        self.metrics["vpn_connection_latency_seconds"] = {
            "type": MetricType.HISTOGRAM,
            "help": "VPN connection latency distribution",
            "labels": ["server", "protocol"],
            "buckets": [0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0],
            "values": {},
        }

        self.metrics["vpn_bandwidth_bytes"] = {
            "type": MetricType.GAUGE,
            "help": "VPN bandwidth usage in bytes per second",
            "labels": ["server", "protocol", "direction"],
            "values": {},
        }

        self.metrics["vpn_packet_loss_rate"] = {
            "type": MetricType.GAUGE,
            "help": "VPN packet loss rate",
            "labels": ["server", "protocol"],
            "values": {},
        }

        # Server Performance Metrics
        self.metrics["vpn_server_cpu_usage"] = {
            "type": MetricType.GAUGE,
            "help": "VPN server CPU usage percentage",
            "labels": ["server", "region"],
            "values": {},
        }

        self.metrics["vpn_server_memory_usage"] = {
            "type": MetricType.GAUGE,
            "help": "VPN server memory usage percentage",
            "labels": ["server", "region"],
            "values": {},
        }

        self.metrics["vpn_server_disk_usage"] = {
            "type": MetricType.GAUGE,
            "help": "VPN server disk usage percentage",
            "labels": ["server", "region"],
            "values": {},
        }

        # Cache Performance Metrics
        self.metrics["cache_hits_total"] = {
            "type": MetricType.COUNTER,
            "help": "Total cache hits",
            "labels": ["cache_level", "cache_type"],
            "values": {},
        }

        self.metrics["cache_misses_total"] = {
            "type": MetricType.COUNTER,
            "help": "Total cache misses",
            "labels": ["cache_level", "cache_type"],
            "values": {},
        }

        # ML Quality Prediction Metrics
        self.metrics["ml_predictions_total"] = {
            "type": MetricType.COUNTER,
            "help": "Total ML quality predictions",
            "labels": ["model_type", "prediction_grade"],
            "values": {},
        }

        self.metrics["ml_prediction_accuracy"] = {
            "type": MetricType.GAUGE,
            "help": "ML prediction accuracy",
            "labels": ["model_type"],
            "values": {},
        }

        # Error and Alert Metrics
        self.metrics["vpn_errors_total"] = {
            "type": MetricType.COUNTER,
            "help": "Total VPN errors",
            "labels": ["error_type", "server", "severity"],
            "values": {},
        }

        self.metrics["vpn_alerts_active"] = {
            "type": MetricType.GAUGE,
            "help": "Number of active VPN alerts",
            "labels": ["alert_type", "severity"],
            "values": {},
        }

    def update_connection_metrics(
        self, server_metrics: VPNServerMetrics
    ) -> None:
        """Update VPN connection metrics.

        Args:
            server_metrics: VPN server metrics
        """
        labels = {
            "server": server_metrics.server_name,
            "protocol": server_metrics.protocol,
            "region": server_metrics.region,
        }

        # Update active connections
        self._update_gauge(
            "vpn_connections_active", labels, server_metrics.active_connections
        )

        # Update latency histogram
        self._update_histogram(
            "vpn_connection_latency_seconds",
            labels,
            server_metrics.avg_latency,
        )

        # Update bandwidth metrics
        upload_labels = {**labels, "direction": "upload"}
        download_labels = {**labels, "direction": "download"}

        self._update_gauge(
            "vpn_bandwidth_bytes", upload_labels, server_metrics.bytes_uploaded
        )
        self._update_gauge(
            "vpn_bandwidth_bytes",
            download_labels,
            server_metrics.bytes_downloaded,
        )

        # Update packet loss rate
        self._update_gauge(
            "vpn_packet_loss_rate", labels, server_metrics.packet_loss_rate
        )

        # Update server performance metrics
        server_labels = {
            "server": server_metrics.server_name,
            "region": server_metrics.region,
        }

        self._update_gauge(
            "vpn_server_cpu_usage", server_labels, server_metrics.cpu_usage
        )
        self._update_gauge(
            "vpn_server_memory_usage",
            server_labels,
            server_metrics.memory_usage,
        )
        self._update_gauge(
            "vpn_server_disk_usage", server_labels, server_metrics.disk_usage
        )

    def update_cache_metrics(
        self, cache_level: str, cache_type: str, hits: int, misses: int
    ) -> None:
        """Update cache performance metrics.

        Args:
            cache_level: Cache level (L1, L2, L3)
            cache_type: Cache type (server_rec, quality_pred, etc.)
            hits: Number of cache hits
            misses: Number of cache misses
        """
        labels = {"cache_level": cache_level, "cache_type": cache_type}

        self._update_counter("cache_hits_total", labels, hits)
        self._update_counter("cache_misses_total", labels, misses)

    def update_ml_metrics(
        self, model_type: str, prediction_grade: str, accuracy: float
    ) -> None:
        """Update ML quality prediction metrics.

        Args:
            model_type: ML model type
            prediction_grade: Quality prediction grade
            accuracy: Model accuracy
        """
        prediction_labels = {
            "model_type": model_type,
            "prediction_grade": prediction_grade,
        }

        accuracy_labels = {"model_type": model_type}

        self._update_counter("ml_predictions_total", prediction_labels, 1)
        self._update_gauge("ml_prediction_accuracy", accuracy_labels, accuracy)

    def update_error_metrics(
        self, error_type: str, server: str, severity: str
    ) -> None:
        """Update error metrics.

        Args:
            error_type: Type of error
            server: Server where error occurred
            severity: Error severity level
        """
        labels = {
            "error_type": error_type,
            "server": server,
            "severity": severity,
        }

        self._update_counter("vpn_errors_total", labels, 1)

    def update_alert_metrics(
        self, alert_type: str, severity: str, count: int
    ) -> None:
        """Update alert metrics.

        Args:
            alert_type: Type of alert
            severity: Alert severity
            count: Number of active alerts
        """
        labels = {"alert_type": alert_type, "severity": severity}

        self._update_gauge("vpn_alerts_active", labels, count)

    def _update_gauge(
        self, metric_name: str, labels: Dict[str, str], value: float
    ) -> None:
        """Update gauge metric."""
        if metric_name not in self.metrics:
            return

        label_key = self._create_label_key(labels)
        self.metrics[metric_name]["values"][label_key] = {
            "labels": labels,
            "value": value,
            "timestamp": time.time(),
        }

    def _update_counter(
        self, metric_name: str, labels: Dict[str, str], increment: int
    ) -> None:
        """Update counter metric."""
        if metric_name not in self.metrics:
            return

        label_key = self._create_label_key(labels)

        if label_key not in self.metrics[metric_name]["values"]:
            self.metrics[metric_name]["values"][label_key] = {
                "labels": labels,
                "value": 0,
                "timestamp": time.time(),
            }

        self.metrics[metric_name]["values"][label_key]["value"] += increment
        self.metrics[metric_name]["values"][label_key][
            "timestamp"
        ] = time.time()

    def _update_histogram(
        self, metric_name: str, labels: Dict[str, str], value: float
    ) -> None:
        """Update histogram metric."""
        if metric_name not in self.metrics:
            return

        label_key = self._create_label_key(labels)

        if label_key not in self.metrics[metric_name]["values"]:
            self.metrics[metric_name]["values"][label_key] = {
                "labels": labels,
                "buckets": {},
                "count": 0,
                "sum": 0.0,
                "timestamp": time.time(),
            }

        entry = self.metrics[metric_name]["values"][label_key]
        buckets = sorted(self.metrics[metric_name].get("buckets", []))

        try:
            v = float(value)
        except (TypeError, ValueError):
            v = float("inf")

        is_finite = not (v != v or v == float("inf") or v == float("-inf"))

        if is_finite:
            # Increment all buckets that are >= value
            for bucket in buckets:
                if v <= bucket:
                    bucket_key = f"le_{bucket}"
                    entry["buckets"][bucket_key] = (
                        entry["buckets"].get(bucket_key, 0) + 1
                    )
            entry["sum"] += v

        # +Inf bucket counts all observations
        entry["buckets"]["le_+Inf"] = entry["buckets"].get("le_+Inf", 0) + 1
        entry["count"] += 1
        entry["timestamp"] = time.time()

    def _create_label_key(self, labels: Dict[str, str]) -> str:
        """Create stable unique key from labels."""
        if not isinstance(labels, dict):
            labels = {}
        norm_items = sorted(
            ((str(k), str(v)) for k, v in labels.items()), key=lambda kv: kv[0]
        )
        return "|".join(f"{k}={v}" for k, v in norm_items)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary for monitoring dashboard."""
        summary = {
            "total_metrics": len(self.metrics),
            "collection_active": self.is_collecting,
            "collection_interval": self.collection_interval,
            "metrics_by_type": {},
            "recent_updates": [],
        }

        # Count metrics by type
        for metric_name, metric_data in self.metrics.items():
            metric_type = metric_data["type"].value
            if metric_type not in summary["metrics_by_type"]:
                summary["metrics_by_type"][metric_type] = 0
            summary["metrics_by_type"][metric_type] += 1

        # Get recent updates
        current_time = time.time()
        for metric_name, metric_data in self.metrics.items():
            for label_key, value_data in metric_data["values"].items():
                if (
                    current_time - value_data["timestamp"] < 300
                ):  # Last 5 minutes
                    summary["recent_updates"].append(
                        {
                            "metric": metric_name,
                            "labels": value_data["labels"],
                            "value": value_data["value"],
                            "timestamp": value_data["timestamp"],
                        }
                    )

        return summary
