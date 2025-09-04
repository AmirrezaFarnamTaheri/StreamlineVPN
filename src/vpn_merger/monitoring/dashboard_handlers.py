"""
Dashboard Request Handlers
=========================

Request handlers for the monitoring dashboard API endpoints.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from aiohttp import web
from aiohttp.web import Request, Response

logger = logging.getLogger(__name__)


class DashboardHandlers:
    """Request handlers for dashboard API endpoints."""
    
    def __init__(self, dashboard):
        """Initialize handlers with dashboard reference.
        
        Args:
            dashboard: Reference to the monitoring dashboard instance
        """
        self.dashboard = dashboard
    
    async def handle_dashboard(self, request: Request) -> Response:
        """Handle main dashboard page request."""
        html_content = self._generate_dashboard_html()
        return web.Response(text=html_content, content_type="text/html")
    
    async def handle_health_api(self, request: Request) -> Response:
        """Handle health API endpoint."""
        try:
            health_data = await self.dashboard.health_monitor.get_comprehensive_health()
            return web.json_response(health_data)
        except Exception as e:
            logger.error(f"Error getting health data: {e}")
            return web.json_response({"error": "Failed to get health data"}, status=500)
    
    async def handle_metrics_api(self, request: Request) -> Response:
        """Handle metrics API endpoint."""
        try:
            metrics_data = {
                "current_metrics": self.dashboard._get_current_metrics(),
                "metrics_history": self.dashboard.metrics_history[-100:],  # Last 100 entries
                "last_update": self.dashboard.last_update.isoformat(),
            }
            return web.json_response(metrics_data)
        except Exception as e:
            logger.error(f"Error getting metrics data: {e}")
            return web.json_response({"error": "Failed to get metrics data"}, status=500)
    
    async def handle_alerts_api(self, request: Request) -> Response:
        """Handle alerts API endpoint."""
        try:
            alerts_data = {
                "active_alerts": [alert for alert in self.dashboard.alerts if alert.get("active", True)],
                "all_alerts": self.dashboard.alerts,
                "alert_count": len([alert for alert in self.dashboard.alerts if alert.get("active", True)]),
            }
            return web.json_response(alerts_data)
        except Exception as e:
            logger.error(f"Error getting alerts data: {e}")
            return web.json_response({"error": "Failed to get alerts data"}, status=500)
    
    async def handle_performance_api(self, request: Request) -> Response:
        """Handle performance API endpoint."""
        try:
            performance_data = await self.dashboard.performance_optimizer.get_performance_metrics()
            return web.json_response(performance_data)
        except Exception as e:
            logger.error(f"Error getting performance data: {e}")
            return web.json_response({"error": "Failed to get performance data"}, status=500)
    
    async def handle_system_api(self, request: Request) -> Response:
        """Handle system API endpoint."""
        try:
            system_data = {
                "system_info": self.dashboard._get_system_info(),
                "resource_usage": self.dashboard._get_resource_usage(),
                "uptime": self.dashboard._get_uptime(),
            }
            return web.json_response(system_data)
        except Exception as e:
            logger.error(f"Error getting system data: {e}")
            return web.json_response({"error": "Failed to get system data"}, status=500)
    
    async def handle_events_api(self, request: Request) -> Response:
        """Handle events API endpoint."""
        try:
            # Get query parameters
            limit = int(request.query.get("limit", 50))
            event_type = request.query.get("type")
            
            events_data = self.dashboard._get_recent_events(limit, event_type)
            return web.json_response(events_data)
        except Exception as e:
            logger.error(f"Error getting events data: {e}")
            return web.json_response({"error": "Failed to get events data"}, status=500)
    
    async def handle_websocket(self, request: Request) -> Response:
        """Handle WebSocket connection for real-time updates."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        logger.info("WebSocket connection established")
        
        try:
            # Add client to dashboard's WebSocket clients
            self.dashboard.websocket_clients.append(ws)
            
            # Send initial data
            await ws.send_str(json.dumps({
                "type": "initial_data",
                "data": {
                    "health": await self.dashboard.health_monitor.get_comprehensive_health(),
                    "metrics": self.dashboard._get_current_metrics(),
                    "alerts": [alert for alert in self.dashboard.alerts if alert.get("active", True)],
                }
            }))
            
            # Keep connection alive and handle incoming messages
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_websocket_message(ws, data)
                    except json.JSONDecodeError:
                        await ws.send_str(json.dumps({"error": "Invalid JSON"}))
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Remove client from dashboard's WebSocket clients
            if ws in self.dashboard.websocket_clients:
                self.dashboard.websocket_clients.remove(ws)
            logger.info("WebSocket connection closed")
        
        return ws
    
    async def _handle_websocket_message(self, ws: web.WebSocketResponse, data: Dict[str, Any]) -> None:
        """Handle incoming WebSocket message.
        
        Args:
            ws: WebSocket response object
            data: Message data
        """
        message_type = data.get("type")
        
        if message_type == "ping":
            await ws.send_str(json.dumps({"type": "pong"}))
        elif message_type == "subscribe":
            # Handle subscription to specific data types
            subscription_type = data.get("subscription_type")
            if subscription_type in ["health", "metrics", "alerts", "performance"]:
                await ws.send_str(json.dumps({
                    "type": "subscription_confirmed",
                    "subscription_type": subscription_type
                }))
        elif message_type == "get_data":
            # Handle data request
            data_type = data.get("data_type")
            if data_type == "health":
                health_data = await self.dashboard.health_monitor.get_comprehensive_health()
                await ws.send_str(json.dumps({
                    "type": "data_update",
                    "data_type": "health",
                    "data": health_data
                }))
            elif data_type == "metrics":
                metrics_data = self.dashboard._get_current_metrics()
                await ws.send_str(json.dumps({
                    "type": "data_update",
                    "data_type": "metrics",
                    "data": metrics_data
                }))
    
    def _generate_dashboard_html(self) -> str:
        """Generate the main dashboard HTML page.
        
        Returns:
            HTML content for the dashboard
        """
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VPN Merger Monitoring Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .metric-card { transition: transform 0.2s, box-shadow 0.2s; }
        .metric-card:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        .status-healthy { color: #10b981; }
        .status-warning { color: #f59e0b; }
        .status-error { color: #ef4444; }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <header class="mb-8">
            <h1 class="text-3xl font-bold text-gray-800">VPN Merger Monitoring Dashboard</h1>
            <p class="text-gray-600 mt-2">Real-time system monitoring and performance metrics</p>
        </header>
        
        <!-- Status Overview -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="metric-card bg-white rounded-lg shadow p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600">System Health</p>
                        <p class="text-2xl font-bold status-healthy" id="system-health">Healthy</p>
                    </div>
                    <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                        <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                </div>
            </div>
            
            <div class="metric-card bg-white rounded-lg shadow p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600">Active Alerts</p>
                        <p class="text-2xl font-bold" id="active-alerts">0</p>
                    </div>
                    <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                        <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-5 5v-5zM4.5 19.5L9 15l3 3 6-6"></path>
                        </svg>
                    </div>
                </div>
            </div>
            
            <div class="metric-card bg-white rounded-lg shadow p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600">CPU Usage</p>
                        <p class="text-2xl font-bold" id="cpu-usage">0%</p>
                    </div>
                    <div class="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                        <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path>
                        </svg>
                    </div>
                </div>
            </div>
            
            <div class="metric-card bg-white rounded-lg shadow p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600">Memory Usage</p>
                        <p class="text-2xl font-bold" id="memory-usage">0%</p>
                    </div>
                    <div class="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                        <svg class="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"></path>
                        </svg>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Charts Section -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-semibold text-gray-800 mb-4">Performance Metrics</h3>
                <canvas id="performance-chart" width="400" height="200"></canvas>
            </div>
            
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-semibold text-gray-800 mb-4">System Resources</h3>
                <canvas id="resources-chart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <!-- Alerts Section -->
        <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold text-gray-800 mb-4">Recent Alerts</h3>
            <div id="alerts-list" class="space-y-3">
                <p class="text-gray-500 text-center py-4">No active alerts</p>
            </div>
        </div>
    </div>
    
    <script>
        // WebSocket connection for real-time updates
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        };
        
        function updateDashboard(data) {
            if (data.type === 'initial_data' || data.type === 'data_update') {
                const dashboardData = data.data;
                
                // Update health status
                if (dashboardData.health) {
                    document.getElementById('system-health').textContent = 
                        dashboardData.health.overall_status || 'Unknown';
                }
                
                // Update alerts
                if (dashboardData.alerts) {
                    document.getElementById('active-alerts').textContent = 
                        dashboardData.alerts.length;
                    updateAlertsList(dashboardData.alerts);
                }
                
                // Update metrics
                if (dashboardData.metrics) {
                    updateMetrics(dashboardData.metrics);
                }
            }
        }
        
        function updateMetrics(metrics) {
            // Update CPU and Memory usage
            if (metrics.cpu_usage !== undefined) {
                document.getElementById('cpu-usage').textContent = 
                    Math.round(metrics.cpu_usage) + '%';
            }
            
            if (metrics.memory_usage !== undefined) {
                document.getElementById('memory-usage').textContent = 
                    Math.round(metrics.memory_usage) + '%';
            }
        }
        
        function updateAlertsList(alerts) {
            const alertsList = document.getElementById('alerts-list');
            
            if (alerts.length === 0) {
                alertsList.innerHTML = '<p class="text-gray-500 text-center py-4">No active alerts</p>';
                return;
            }
            
            alertsList.innerHTML = alerts.map(alert => `
                <div class="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div>
                        <p class="font-medium text-red-800">${alert.title || 'Alert'}</p>
                        <p class="text-sm text-red-600">${alert.message || ''}</p>
                    </div>
                    <span class="text-xs text-red-500">${new Date(alert.timestamp).toLocaleTimeString()}</span>
                </div>
            `).join('');
        }
        
        // Initialize charts
        const performanceCtx = document.getElementById('performance-chart').getContext('2d');
        const performanceChart = new Chart(performanceCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Response Time (ms)',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
        const resourcesCtx = document.getElementById('resources-chart').getContext('2d');
        const resourcesChart = new Chart(resourcesCtx, {
            type: 'doughnut',
            data: {
                labels: ['CPU', 'Memory', 'Disk'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [
                        'rgb(59, 130, 246)',
                        'rgb(16, 185, 129)',
                        'rgb(245, 158, 11)'
                    ]
                }]
            },
            options: {
                responsive: true
            }
        });
    </script>
</body>
</html>
        """
