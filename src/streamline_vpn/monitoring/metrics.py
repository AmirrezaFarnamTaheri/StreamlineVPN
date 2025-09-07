"""
VPN Monitoring and Metrics Collection
====================================

Comprehensive monitoring system with Prometheus metrics, structured logging,
and distributed tracing as outlined in the technical implementation report.

This module provides a unified interface to the modularized metrics system.
"""

from .metrics_service import (
    MetricsService,
    initialize_metrics,
    get_metrics,
    get_alerting_rules,
)
from .metrics_collector import VPNServerMetrics, MetricType, MetricLabel

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


# Legacy compatibility - maintain old interface
def initialize_metrics_legacy():
    """Legacy function for backward compatibility."""
    return initialize_metrics()


def get_metrics_legacy():
    """Legacy function for backward compatibility."""
    return get_metrics()


def get_alerting_rules_legacy():
    """Legacy function for backward compatibility."""
    return get_alerting_rules()
