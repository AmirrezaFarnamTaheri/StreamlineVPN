"""
Geographic Optimization Module for VPN Configuration Distribution
===============================================================

This module provides advanced geographic optimization capabilities for:
- Location-based configuration ranking
- Latency prediction and optimization
- Edge caching deployment
- Geographic load balancing
"""

from .geographic_optimizer import (
    GeographicOptimizer,
    GeoLocation,
    LatencyInfo,
    EdgeCache
)

__all__ = [
    'GeographicOptimizer',
    'GeoLocation',
    'LatencyInfo',
    'EdgeCache'
]
