"""
Enhanced Monitoring Dashboard (Refactored)
==========================================

Real-time monitoring dashboard with comprehensive metrics visualization,
alerting, and system health monitoring.

This is a refactored version that uses modular components for better maintainability.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from aiohttp import web

from .health_monitor import get_health_monitor
from ..core.observers import get_event_bus
from ..core.performance_optimizer import PerformanceOptimizer
from .dashboard_handlers import DashboardHandlers
from .dashboard_metrics import DashboardMetrics

logger = logging.getLogger(__name__)


class MonitoringDashboard:
    """Enhanced monitoring dashboard with real-time metrics and alerting."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8082):
        """Initialize the monitoring dashboard.
        
        Args:
            host: Host address to bind to
            port: Port number to bind to
        """
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.start_time = time.time()
        
        # Initialize components
        self.health_monitor = get_health_monitor()
        self.event_bus = get_event_bus()
        self.performance_optimizer = PerformanceOptimizer()
        
        # Initialize modular components
        self.handlers = DashboardHandlers(self)
        self.metrics_collector = DashboardMetrics(self)
        
        # Metrics storage
        self.metrics_history: List[Dict[str, Any]] = []
        self.alerts: List[Dict[str, Any]] = []
        self.last_update = datetime.now()
        self.websocket_clients: List[web.WebSocketResponse] = []
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"Monitoring dashboard initialized on {host}:{port}")
    
    def _setup_routes(self) -> None:
        """Setup web application routes."""
        # Main dashboard
        self.app.router.add_get("/", self.handlers.handle_dashboard)
        
        # API endpoints
        self.app.router.add_get("/api/health", self.handlers.handle_health_api)
        self.app.router.add_get("/api/metrics", self.handlers.handle_metrics_api)
        self.app.router.add_get("/api/alerts", self.handlers.handle_alerts_api)
        self.app.router.add_get("/api/performance", self.handlers.handle_performance_api)
        self.app.router.add_get("/api/system", self.handlers.handle_system_api)
        self.app.router.add_get("/api/events", self.handlers.handle_events_api)
        
        # WebSocket for real-time updates
        self.app.router.add_get("/ws", self.handlers.handle_websocket)
        
        # Static files
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            self.app.router.add_static("/static", static_dir)
    
    async def start(self) -> None:
        """Start the monitoring dashboard."""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()
            
            logger.info(f"Monitoring dashboard started at http://{self.host}:{self.port}")
            
            # Start background tasks
            asyncio.create_task(self.metrics_collector.start_metrics_collection())
            asyncio.create_task(self._background_health_monitoring())
            
        except Exception as e:
            logger.error(f"Failed to start monitoring dashboard: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the monitoring dashboard."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        
        # Close all WebSocket connections
        for client in self.websocket_clients:
            await client.close()
        
        logger.info("Monitoring dashboard stopped")
    
    async def _background_health_monitoring(self) -> None:
        """Background task for health monitoring."""
        while True:
            try:
                await self._check_system_health()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _check_system_health(self) -> None:
        """Check overall system health and create alerts if needed."""
        try:
            health_data = await self.health_monitor.get_comprehensive_health()
            
            # Check for critical issues
            if health_data.get("overall_status") == "critical":
                await self.metrics_collector._create_alert(
                    "System Health Critical",
                    "System health status is critical",
                    "error"
                )
            elif health_data.get("overall_status") == "warning":
                await self.metrics_collector._create_alert(
                    "System Health Warning",
                    "System health status is warning",
                    "warning"
                )
            
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            await self.metrics_collector._create_alert(
                "Health Check Failed",
                f"Failed to check system health: {str(e)}",
                "error"
            )
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information.
        
        Returns:
            Dictionary containing system information
        """
        try:
            import platform
            import psutil
            
            return {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
                "python_version": platform.python_version(),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}
    
    def _get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage.
        
        Returns:
            Dictionary containing resource usage information
        """
        try:
            import psutil
            
            return {
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "memory_percent": psutil.virtual_memory().percent,
                "disk_total": psutil.disk_usage('/').total,
                "disk_free": psutil.disk_usage('/').free,
                "disk_percent": (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100,
            }
        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return {}
    
    def _get_uptime(self) -> Dict[str, Any]:
        """Get system and application uptime.
        
        Returns:
            Dictionary containing uptime information
        """
        try:
            import psutil
            
            boot_time = psutil.boot_time()
            current_time = time.time()
            system_uptime = current_time - boot_time
            app_uptime = current_time - self.start_time
            
            return {
                "system_uptime_seconds": system_uptime,
                "system_uptime_human": self._format_uptime(system_uptime),
                "application_uptime_seconds": app_uptime,
                "application_uptime_human": self._format_uptime(app_uptime),
                "boot_time": datetime.fromtimestamp(boot_time).isoformat(),
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting uptime: {e}")
            return {}
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format.
        
        Args:
            seconds: Uptime in seconds
            
        Returns:
            Formatted uptime string
        """
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _get_recent_events(self, limit: int = 50, event_type: str = None) -> Dict[str, Any]:
        """Get recent events from the event bus.
        
        Args:
            limit: Maximum number of events to return
            event_type: Optional event type filter
            
        Returns:
            Dictionary containing recent events
        """
        try:
            if hasattr(self.event_bus, 'get_recent_events'):
                events = self.event_bus.get_recent_events(limit, event_type)
            else:
                events = []
            
            return {
                "events": events,
                "total_count": len(events),
                "filtered_by_type": event_type,
            }
        except Exception as e:
            logger.error(f"Error getting recent events: {e}")
            return {"events": [], "total_count": 0, "error": str(e)}
    
    def get_dashboard_info(self) -> Dict[str, Any]:
        """Get comprehensive dashboard information.
        
        Returns:
            Dictionary containing dashboard information
        """
        return {
            "host": self.host,
            "port": self.port,
            "status": "running" if self.site else "stopped",
            "uptime": time.time() - self.start_time,
            "metrics_count": len(self.metrics_history),
            "alerts_count": len([alert for alert in self.alerts if alert.get("active", True)]),
            "websocket_clients": len(self.websocket_clients),
            "last_update": self.last_update.isoformat(),
        }
