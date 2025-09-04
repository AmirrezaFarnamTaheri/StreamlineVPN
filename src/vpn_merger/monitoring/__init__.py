"""
Monitoring Module
================

Comprehensive monitoring and observability features for the VPN Merger system.
"""

from .health_monitor import SystemHealthMonitor, get_health_monitor, reset_health_monitor
from .dashboard import MonitoringDashboard
# Observability exports are intentionally minimal; detailed collectors are optional.
from .observability import init_observability, get_meter_if_any

__all__ = [
    # Health Monitoring
    "SystemHealthMonitor",
    "get_health_monitor",
    "reset_health_monitor",
    
    # Monitoring Dashboard
    "MonitoringDashboard",
    
    # Observability
    "init_observability",
    "get_meter_if_any",
]