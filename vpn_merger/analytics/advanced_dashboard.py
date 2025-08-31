"""
Advanced Analytics Dashboard for VPN Configuration Merger
=======================================================

Real-time analytics dashboard with comprehensive metrics visualization,
performance monitoring, and interactive charts for VPN merger operations.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import aiohttp
from aiohttp import web
import aiofiles

from .models import (
    DashboardMetrics, ChartData, PerformanceMetrics, GeographicData, ProtocolStats,
    DEFAULT_HOST, DEFAULT_PORT, DEFAULT_UPDATE_INTERVAL, DEFAULT_HISTORY_LENGTH
)
from .chart_generator import ChartGenerator

logger = logging.getLogger(__name__)


class AnalyticsDashboard:
    """Advanced analytics dashboard for VPN merger operations.
    
    Features:
    - Real-time metrics visualization
    - Interactive charts and graphs
    - Performance trend analysis
    - Geographic distribution mapping
    - Protocol breakdown analysis
    - Cache performance monitoring
    """
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        """Initialize the analytics dashboard.
        
        Args:
            host: Host address to bind to
            port: Port number to bind to
        """
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None
        
        # Initialize components
        self.chart_generator = ChartGenerator()
        self.metrics_history = []
        self.charts = {}
        self.last_update = datetime.now()
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"Analytics dashboard initialized on {host}:{port}")
    
    def _setup_routes(self):
        """Setup web application routes."""
        self.app.router.add_get('/', self._handle_dashboard)
        self.app.router.add_get('/api/metrics', self._handle_metrics_api)
        self.app.router.add_get('/api/charts', self._handle_charts_api)
        self.app.router.add_get('/api/performance', self._handle_performance_api)
        self.app.router.add_static('/static', Path(__file__).parent / 'static')
    
    async def start(self):
        """Start the dashboard web server."""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()
            
            logger.info(f"Dashboard started at http://{self.host}:{self.port}")
            
            # Start background update task
            asyncio.create_task(self._background_update())
            
        except Exception as e:
            logger.error(f"Failed to start dashboard: {e}")
            raise
    
    async def stop(self):
        """Stop the dashboard web server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Dashboard stopped")
    
    async def _background_update(self):
        """Background task to update metrics and charts."""
        while True:
            try:
                await self._update_metrics()
                await self._update_charts()
                await asyncio.sleep(DEFAULT_UPDATE_INTERVAL)
            except Exception as e:
                logger.error(f"Error in background update: {e}")
                await asyncio.sleep(5)  # Shorter delay on error
    
    async def _update_metrics(self):
        """Update dashboard metrics."""
        try:
            # Get current metrics from VPN merger
            metrics = await self._collect_metrics()
            
            # Store in history
            self.metrics_history.append(metrics)
            
            # Keep only recent history
            if len(self.metrics_history) > DEFAULT_HISTORY_LENGTH:
                self.metrics_history = self.metrics_history[-DEFAULT_HISTORY_LENGTH:]
            
            self.last_update = datetime.now()
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    async def _collect_metrics(self) -> DashboardMetrics:
        """Collect current metrics from VPN merger components."""
        # This would integrate with actual VPN merger components
        # For now, return mock data
        return DashboardMetrics(
            real_time_configs=1000,
            source_reliability=0.85,
            geographic_distribution={'US': 300, 'EU': 250, 'ASIA': 200, 'OTHER': 250},
            protocol_breakdown={'vmess': 400, 'vless': 300, 'trojan': 200, 'ss': 100},
            performance_trends=[],
            cache_hit_rate=0.92,
            error_rate=0.03,
                last_updated=datetime.now()
            )
    
    async def _update_charts(self):
        """Update dashboard charts."""
        try:
            if not self.metrics_history:
                return
            
            latest_metrics = self.metrics_history[-1]
            
            # Update protocol breakdown chart
            protocol_chart = self.chart_generator.create_pie_chart(
                'protocol_breakdown',
                'Protocol Distribution',
                list(latest_metrics.protocol_breakdown.keys()),
                list(latest_metrics.protocol_breakdown.values())
            )
            if protocol_chart:
                self.charts['protocol_breakdown'] = protocol_chart
            
            # Update geographic distribution chart
            geo_chart = self.chart_generator.create_bar_chart(
                'geographic_distribution',
                'Geographic Distribution',
                list(latest_metrics.geographic_distribution.keys()),
                list(latest_metrics.geographic_distribution.values())
            )
            if geo_chart:
                self.charts['geographic_distribution'] = geo_chart
            
            # Update reliability gauge
            reliability_gauge = self.chart_generator.create_gauge_chart(
                'source_reliability',
                'Source Reliability',
                latest_metrics.source_reliability * 100
            )
            if reliability_gauge:
                self.charts['source_reliability'] = reliability_gauge
            
            # Update performance trends
            if len(self.metrics_history) > 1:
                timestamps = [m.last_updated for m in self.metrics_history]
                config_counts = [m.real_time_configs for m in self.metrics_history]
                
                trends_chart = self.chart_generator.create_line_chart(
                    'performance_trends',
                    'Configuration Count Over Time',
                    timestamps,
                    config_counts,
                    'Time',
                    'Config Count'
                )
                if trends_chart:
                    self.charts['performance_trends'] = trends_chart
            
        except Exception as e:
            logger.error(f"Error updating charts: {e}")
    
    async def _handle_dashboard(self, request: web.Request) -> web.Response:
        """Handle dashboard main page request."""
        try:
            html_content = await self._generate_dashboard_html()
            return web.Response(text=html_content, content_type='text/html')
        except Exception as e:
            logger.error(f"Error handling dashboard request: {e}")
            return web.Response(text="Dashboard Error", status=500)
    
    async def _handle_metrics_api(self, request: web.Request) -> web.Response:
        """Handle metrics API request."""
        try:
            if not self.metrics_history:
                return web.json_response({'error': 'No metrics available'})
            
            latest_metrics = self.metrics_history[-1]
            return web.json_response({
                'real_time_configs': latest_metrics.real_time_configs,
                'source_reliability': latest_metrics.source_reliability,
                'geographic_distribution': latest_metrics.geographic_distribution,
                'protocol_breakdown': latest_metrics.protocol_breakdown,
                'cache_hit_rate': latest_metrics.cache_hit_rate,
                'error_rate': latest_metrics.error_rate,
                'last_updated': latest_metrics.last_updated.isoformat()
            })
        except Exception as e:
            logger.error(f"Error handling metrics API: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_charts_api(self, request: web.Request) -> web.Response:
        """Handle charts API request."""
        try:
            chart_id = request.query.get('chart_id')
            if chart_id and chart_id in self.charts:
                chart = self.charts[chart_id]
                return web.json_response({
                    'chart_id': chart.chart_id,
                    'chart_type': chart.chart_type,
                    'title': chart.title,
                    'data': chart.data,
                    'last_updated': chart.last_updated.isoformat()
                })
            else:
                return web.json_response({
                    'charts': list(self.charts.keys()),
                    'last_updated': self.last_update.isoformat()
                })
        except Exception as e:
            logger.error(f"Error handling charts API: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_performance_api(self, request: web.Request) -> web.Response:
        """Handle performance API request."""
        try:
            if len(self.metrics_history) < 2:
                return web.json_response({'error': 'Insufficient data for performance analysis'})
            
            # Calculate performance trends
            recent_metrics = self.metrics_history[-10:]  # Last 10 data points
            
            response_times = [0.1 + (i * 0.01) for i in range(len(recent_metrics))]  # Mock data
            throughput = [m.real_time_configs for m in recent_metrics]
            error_rates = [m.error_rate for m in recent_metrics]
            
            return web.json_response({
                'response_times': response_times,
                'throughput': throughput,
                'error_rates': error_rates,
                'timestamps': [m.last_updated.isoformat() for m in recent_metrics]
            })
        except Exception as e:
            logger.error(f"Error handling performance API: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _generate_dashboard_html(self) -> str:
        """Generate dashboard HTML content."""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>VPN Merger Analytics Dashboard</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
                .chart { border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
                .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }
                .metric { background: #f5f5f5; padding: 15px; border-radius: 5px; text-align: center; }
                .metric-value { font-size: 24px; font-weight: bold; color: #333; }
                .metric-label { font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <h1>VPN Merger Analytics Dashboard</h1>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value" id="config-count">-</div>
                    <div class="metric-label">Configurations</div>
            </div>
                <div class="metric">
                    <div class="metric-value" id="reliability">-</div>
                    <div class="metric-label">Reliability</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="cache-hit">-</div>
                    <div class="metric-label">Cache Hit Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="error-rate">-</div>
                    <div class="metric-label">Error Rate</div>
                </div>
            </div>
            <div class="dashboard">
                <div class="chart">
                    <div id="protocol-chart"></div>
                </div>
                <div class="chart">
                    <div id="geo-chart"></div>
            </div>
                <div class="chart">
                    <div id="reliability-gauge"></div>
                </div>
                <div class="chart">
                    <div id="trends-chart"></div>
                </div>
            </div>
            <script>
                async function updateDashboard() {
                    try {
                        const response = await fetch('/api/metrics');
                        const data = await response.json();
                        
                        document.getElementById('config-count').textContent = data.real_time_configs.toLocaleString();
                        document.getElementById('reliability').textContent = (data.source_reliability * 100).toFixed(1) + '%';
                        document.getElementById('cache-hit').textContent = (data.cache_hit_rate * 100).toFixed(1) + '%';
                        document.getElementById('error-rate').textContent = (data.error_rate * 100).toFixed(2) + '%';
                        
                        // Update charts
                        updateProtocolChart(data.protocol_breakdown);
                        updateGeoChart(data.geographic_distribution);
                        
                    } catch (error) {
                        console.error('Error updating dashboard:', error);
                    }
                }
                
                function updateProtocolChart(protocolData) {
                    const data = [{
                        values: Object.values(protocolData),
                        labels: Object.keys(protocolData),
                        type: 'pie'
                    }];
                    
                    const layout = {
                        title: 'Protocol Distribution',
                        height: 400
                    };
                    
                    Plotly.newPlot('protocol-chart', data, layout);
                }
                
                function updateGeoChart(geoData) {
                    const data = [{
                        x: Object.keys(geoData),
                        y: Object.values(geoData),
                        type: 'bar'
                    }];
                    
                    const layout = {
                        title: 'Geographic Distribution',
                        height: 400
                    };
                    
                    Plotly.newPlot('geo-chart', data, layout);
                }
                
                // Update every 30 seconds
                updateDashboard();
                setInterval(updateDashboard, 30000);
            </script>
        </body>
        </html>
        """
        return html_template
    
    def get_dashboard_info(self) -> Dict[str, Any]:
        """Get dashboard information."""
        return {
            'host': self.host,
            'port': self.port,
            'url': f"http://{self.host}:{self.port}",
            'charts_available': list(self.charts.keys()),
            'metrics_history_length': len(self.metrics_history),
            'last_update': self.last_update.isoformat(),
            'status': 'running' if self.site else 'stopped'
        }
