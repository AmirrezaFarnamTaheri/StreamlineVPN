"""
Dashboard Metrics Collection
============================

Metrics collection and processing for the monitoring dashboard.
"""

import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DashboardMetrics:
    """Handles metrics collection and processing for the dashboard."""
    
    def __init__(self, dashboard):
        """Initialize metrics collector.
        
        Args:
            dashboard: Reference to the monitoring dashboard instance
        """
        self.dashboard = dashboard
        self.metrics_interval = 30  # seconds
        self.max_history = 1000  # maximum number of metrics to keep
    
    async def start_metrics_collection(self) -> None:
        """Start background metrics collection."""
        logger.info("Starting metrics collection")
        
        while True:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.metrics_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(self.metrics_interval)
    
    async def _collect_metrics(self) -> None:
        """Collect current system and application metrics."""
        try:
            current_time = datetime.now()
            
            # Collect system metrics
            system_metrics = self._get_system_metrics()
            
            # Collect application metrics
            app_metrics = await self._get_application_metrics()
            
            # Combine metrics
            combined_metrics = {
                "timestamp": current_time.isoformat(),
                "system": system_metrics,
                "application": app_metrics,
            }
            
            # Add to history
            self.dashboard.metrics_history.append(combined_metrics)
            
            # Trim history if too long
            if len(self.dashboard.metrics_history) > self.max_history:
                self.dashboard.metrics_history = self.dashboard.metrics_history[-self.max_history:]
            
            # Update last update time
            self.dashboard.last_update = current_time
            
            # Check for alerts
            await self._check_metrics_alerts(combined_metrics)
            
            # Broadcast to WebSocket clients
            await self._broadcast_metrics_update(combined_metrics)
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics.
        
        Returns:
            Dictionary containing system metrics
        """
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network_io = psutil.net_io_counters()
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "frequency": {
                        "current": cpu_freq.current if cpu_freq else 0,
                        "min": cpu_freq.min if cpu_freq else 0,
                        "max": cpu_freq.max if cpu_freq else 0,
                    }
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "usage_percent": memory.percent,
                    "swap_total": swap.total,
                    "swap_used": swap.used,
                    "swap_percent": swap.percent,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "usage_percent": (disk.used / disk.total) * 100,
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0,
                },
                "network": {
                    "bytes_sent": network_io.bytes_sent,
                    "bytes_recv": network_io.bytes_recv,
                    "packets_sent": network_io.packets_sent,
                    "packets_recv": network_io.packets_recv,
                },
                "process": {
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms,
                    "cpu_percent": process_cpu,
                    "num_threads": process.num_threads(),
                    "create_time": process.create_time(),
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    async def _get_application_metrics(self) -> Dict[str, Any]:
        """Get current application metrics.
        
        Returns:
            Dictionary containing application metrics
        """
        try:
            app_metrics = {
                "timestamp": datetime.now().isoformat(),
                "uptime": time.time() - self.dashboard.start_time,
            }
            
            # Get health monitor metrics
            if hasattr(self.dashboard, 'health_monitor'):
                health_data = await self.dashboard.health_monitor.get_comprehensive_health()
                app_metrics["health"] = health_data
            
            # Get performance optimizer metrics
            if hasattr(self.dashboard, 'performance_optimizer'):
                performance_data = await self.dashboard.performance_optimizer.get_performance_metrics()
                app_metrics["performance"] = performance_data
            
            # Get event bus metrics
            if hasattr(self.dashboard, 'event_bus'):
                event_metrics = self.dashboard.event_bus.get_metrics()
                app_metrics["events"] = event_metrics
            
            return app_metrics
            
        except Exception as e:
            logger.error(f"Error getting application metrics: {e}")
            return {}
    
    async def _check_metrics_alerts(self, metrics: Dict[str, Any]) -> None:
        """Check metrics for alert conditions.
        
        Args:
            metrics: Current metrics data
        """
        try:
            system_metrics = metrics.get("system", {})
            
            # CPU usage alert
            cpu_usage = system_metrics.get("cpu", {}).get("usage_percent", 0)
            if cpu_usage > 80:
                await self._create_alert(
                    "High CPU Usage",
                    f"CPU usage is at {cpu_usage:.1f}%",
                    "warning"
                )
            
            # Memory usage alert
            memory_usage = system_metrics.get("memory", {}).get("usage_percent", 0)
            if memory_usage > 85:
                await self._create_alert(
                    "High Memory Usage",
                    f"Memory usage is at {memory_usage:.1f}%",
                    "warning"
                )
            
            # Disk usage alert
            disk_usage = system_metrics.get("disk", {}).get("usage_percent", 0)
            if disk_usage > 90:
                await self._create_alert(
                    "High Disk Usage",
                    f"Disk usage is at {disk_usage:.1f}%",
                    "error"
                )
            
            # Process memory alert
            process_memory = system_metrics.get("process", {}).get("memory_rss", 0)
            if process_memory > 1024 * 1024 * 1024:  # 1GB
                await self._create_alert(
                    "High Process Memory",
                    f"Process memory usage is {process_memory / (1024*1024*1024):.1f}GB",
                    "warning"
                )
            
        except Exception as e:
            logger.error(f"Error checking metrics alerts: {e}")
    
    async def _create_alert(self, title: str, message: str, severity: str) -> None:
        """Create a new alert.
        
        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity (info, warning, error)
        """
        alert = {
            "id": f"alert_{int(time.time())}",
            "title": title,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "active": True,
        }
        
        # Add to alerts list
        self.dashboard.alerts.append(alert)
        
        # Keep only recent alerts
        if len(self.dashboard.alerts) > 100:
            self.dashboard.alerts = self.dashboard.alerts[-100:]
        
        # Broadcast alert to WebSocket clients
        await self._broadcast_alert(alert)
        
        logger.warning(f"Alert created: {title} - {message}")
    
    async def _broadcast_metrics_update(self, metrics: Dict[str, Any]) -> None:
        """Broadcast metrics update to WebSocket clients.
        
        Args:
            metrics: Metrics data to broadcast
        """
        if not hasattr(self.dashboard, 'websocket_clients'):
            return
        
        message = {
            "type": "metrics_update",
            "data": metrics
        }
        
        # Send to all connected WebSocket clients
        disconnected_clients = []
        for client in self.dashboard.websocket_clients:
            try:
                await client.send_str(json.dumps(message))
            except Exception:
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.dashboard.websocket_clients.remove(client)
    
    async def _broadcast_alert(self, alert: Dict[str, Any]) -> None:
        """Broadcast alert to WebSocket clients.
        
        Args:
            alert: Alert data to broadcast
        """
        if not hasattr(self.dashboard, 'websocket_clients'):
            return
        
        message = {
            "type": "alert",
            "data": alert
        }
        
        # Send to all connected WebSocket clients
        disconnected_clients = []
        for client in self.dashboard.websocket_clients:
            try:
                await client.send_str(json.dumps(message))
            except Exception:
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.dashboard.websocket_clients.remove(client)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary.
        
        Returns:
            Dictionary containing current metrics summary
        """
        if not self.dashboard.metrics_history:
            return {}
        
        latest_metrics = self.dashboard.metrics_history[-1]
        system_metrics = latest_metrics.get("system", {})
        
        return {
            "cpu_usage": system_metrics.get("cpu", {}).get("usage_percent", 0),
            "memory_usage": system_metrics.get("memory", {}).get("usage_percent", 0),
            "disk_usage": system_metrics.get("disk", {}).get("usage_percent", 0),
            "timestamp": latest_metrics.get("timestamp"),
        }
    
    def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history for specified hours.
        
        Args:
            hours: Number of hours of history to return
            
        Returns:
            List of metrics data
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_metrics = []
        for metrics in self.dashboard.metrics_history:
            try:
                metrics_time = datetime.fromisoformat(metrics.get("timestamp", ""))
                if metrics_time >= cutoff_time:
                    filtered_metrics.append(metrics)
            except Exception:
                continue
        
        return filtered_metrics
