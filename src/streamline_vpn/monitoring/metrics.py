"""
VPN Monitoring and Metrics Collection
====================================

Comprehensive monitoring system with Prometheus metrics, structured logging,
and distributed tracing as outlined in the technical implementation report.

This module provides a unified interface to the modularized metrics system.
"""

from .metrics_collector import MetricLabel, MetricType, VPNServerMetrics
from .metrics_service import (
    MetricsService,
    get_alerting_rules,
    get_metrics,
    initialize_metrics,
)

# Re-export main classes for backward compatibility
__all__ = [
    "MetricsService",
    "VPNServerMetrics",
    "MetricType",
    "MetricLabel",
    "initialize_metrics",
    "get_metrics",
    "get_alerting_rules",
]
