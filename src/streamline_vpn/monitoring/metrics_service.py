"""
Metrics Service
===============

Main metrics service that coordinates collection and export.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..utils.logging import get_logger
from .metrics_collector import MetricsCollector, VPNServerMetrics
from .metrics_exporter import MetricsExporter
from .alerting_rules import AlertingRules

logger = get_logger(__name__)


class MetricsService:
    """Main metrics service with collection and export capabilities."""
    
    def __init__(self):
        """Initialize metrics service."""
        self.collector = MetricsCollector()
        self.exporter = MetricsExporter(self.collector)
        self.alerting_rules = AlertingRules()
    
    async def start_collection(self) -> None:
        """Start metrics collection."""
        if self.collector.is_collecting:
            return
        
        self.collector.is_collecting = True
        self.collector.collection_task = asyncio.create_task(self._collect_metrics_loop())
        logger.info("Started Prometheus metrics collection")
    
    async def stop_collection(self) -> None:
        """Stop metrics collection."""
        self.collector.is_collecting = False
        if self.collector.collection_task:
            self.collector.collection_task.cancel()
            try:
                await self.collector.collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped Prometheus metrics collection")
    
    async def _collect_metrics_loop(self) -> None:
        """Main metrics collection loop."""
        while self.collector.is_collecting:
            try:
                await self._collect_vpn_metrics()
                await asyncio.sleep(self.collector.collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(self.collector.collection_interval)
    
    async def _collect_vpn_metrics(self) -> None:
        """Collect VPN metrics from various sources."""
        # This would integrate with actual VPN servers and services
        # For now, we'll simulate metric collection
        
        # Simulate server metrics collection
        servers = await self._get_vpn_servers()
        for server in servers:
            metrics = await self._get_server_metrics(server)
            self.collector.update_connection_metrics(metrics)
    
    async def _get_vpn_servers(self) -> List[str]:
        """Get list of VPN servers."""
        # Simulate server discovery
        return ["server-1", "server-2", "server-3"]
    
    async def _get_server_metrics(self, server_id: str) -> VPNServerMetrics:
        """Get metrics for a specific server."""
        # Simulate server metrics collection
        return VPNServerMetrics(
            server_id=server_id,
            server_name=f"vpn-{server_id}",
            protocol="vless",
            region="us-east",
            active_connections=50,
            total_connections=1000,
            bytes_uploaded=1024000,
            bytes_downloaded=2048000,
            avg_latency=0.05,
            packet_loss_rate=0.001,
            cpu_usage=45.0,
            memory_usage=60.0,
            disk_usage=30.0,
            last_updated=datetime.now()
        )
    
    def export_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        return self.exporter.export_prometheus_metrics()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary for monitoring dashboard."""
        return self.collector.get_metrics_summary()
    
    def get_alerting_rules(self) -> str:
        """Get alerting rules in Prometheus format."""
        return self.alerting_rules.get_prometheus_rules()


# Global metrics service instance
_metrics_service: Optional[MetricsService] = None


def initialize_metrics() -> MetricsService:
    """Initialize global metrics service."""
    global _metrics_service
    _metrics_service = MetricsService()
    return _metrics_service


def get_metrics() -> Optional[MetricsService]:
    """Get global metrics service instance."""
    return _metrics_service


def get_alerting_rules() -> AlertingRules:
    """Get VPN alerting rules."""
    return AlertingRules()
