"""
Analytics Models and Data Structures
==================================

Data models and constants for the analytics dashboard system.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Constants
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8080
DEFAULT_UPDATE_INTERVAL = 30  # seconds
DEFAULT_HISTORY_LENGTH = 1000
DEFAULT_CHART_HEIGHT = 400
DEFAULT_CHART_WIDTH = 600

# Chart types
CHART_TYPES = {
    "line": "Line Chart",
    "bar": "Bar Chart",
    "pie": "Pie Chart",
    "gauge": "Gauge Chart",
    "scatter": "Scatter Plot",
}

# Color schemes
COLOR_SCHEMES = {
    "primary": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
    "secondary": ["#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3"],
    "qualitative": ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00"],
}


@dataclass
class DashboardMetrics:
    """Dashboard metrics data structure."""

    real_time_configs: int
    source_reliability: float
    geographic_distribution: dict[str, int]
    protocol_breakdown: dict[str, int]
    performance_trends: list[dict[str, Any]]
    cache_hit_rate: float
    error_rate: float
    last_updated: datetime


@dataclass
class ChartData:
    """Chart data structure."""

    chart_id: str
    chart_type: str  # 'line', 'bar', 'pie', 'map', 'gauge'
    title: str
    data: dict[str, Any]
    layout: dict[str, Any]
    last_updated: datetime


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""

    response_time: float
    throughput: float
    error_count: int
    success_rate: float
    timestamp: datetime


@dataclass
class GeographicData:
    """Geographic distribution data."""

    country: str
    config_count: int
    reliability_score: float
    last_updated: datetime


@dataclass
class ProtocolStats:
    """Protocol statistics."""

    protocol: str
    count: int
    percentage: float
    avg_quality: float
    timestamp: datetime
