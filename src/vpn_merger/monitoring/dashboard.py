"""
Enhanced Monitoring Dashboard
=============================

Real-time monitoring dashboard with comprehensive metrics visualization,
alerting, and system health monitoring.

This module now uses the refactored components for better maintainability.
"""

# Import the refactored dashboard
from .dashboard_refactored import MonitoringDashboard

# Re-export for backward compatibility
__all__ = ["MonitoringDashboard"]
