from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .metrics_collector import MetricsCollector
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

try:
    from .tracing_enhanced import TracingService
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False


class MonitoringDashboard:
    """Real-time monitoring dashboard for VPN merger metrics."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'vpn_merger_dashboard_secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.host = host
        self.port = port
        self.metrics_collector = None
        self.tracing_service = None
        
        # Mock data for demonstration
        self.mock_metrics = {
            "configs_processed": 0,
            "sources_active": 0,
            "merge_operations": 0,
            "errors_count": 0,
            "avg_processing_time": 0.0,
            "protocol_distribution": {},
            "source_health": {},
            "performance_metrics": {}
        }
        
        self.setup_routes()
        self.setup_socket_events()
        
        if METRICS_AVAILABLE:
            try:
                self.metrics_collector = MetricsCollector()
            except Exception as e:
                print(f"Failed to initialize metrics collector: {e}")
        
        if TRACING_AVAILABLE:
            try:
                self.tracing_service = TracingService()
            except Exception as e:
                print(f"Failed to initialize tracing service: {e}")
    
    def setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html')
        
        @self.app.route('/api/metrics')
        def get_metrics():
            """Get current metrics."""
            if self.metrics_collector:
                return jsonify(self._collect_real_metrics())
            else:
                return jsonify(self._collect_mock_metrics())
        
        @self.app.route('/api/sources')
        def get_sources():
            """Get source health information."""
            return jsonify(self._get_source_health())
        
        @self.app.route('/api/protocols')
        def get_protocols():
            """Get protocol distribution."""
            return jsonify(self._get_protocol_distribution())
        
        @self.app.route('/api/performance')
        def get_performance():
            """Get performance metrics."""
            return jsonify(self._get_performance_metrics())
        
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint."""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "metrics_available": METRICS_AVAILABLE,
                "tracing_available": TRACING_AVAILABLE
            })
    
    def setup_socket_events(self):
        """Setup WebSocket events for real-time updates."""
        
        @self.socketio.on('connect')
        def handle_connect():
            print(f"Client connected: {request.sid}")
            emit('status', {'data': 'Connected to VPN Merger Dashboard'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('request_metrics')
        def handle_metrics_request():
            """Handle metrics update request."""
            metrics = self._collect_real_metrics() if self.metrics_collector else self._collect_mock_metrics()
            emit('metrics_update', metrics)
    
    def _collect_real_metrics(self) -> Dict[str, Any]:
        """Collect real metrics from the metrics collector."""
        try:
            if not self.metrics_collector:
                return self._collect_mock_metrics()
            
            # Collect metrics from Prometheus registry
            metrics = {}
            
            # Config processing metrics
            if hasattr(self.metrics_collector, 'configs_processed'):
                metrics['configs_processed'] = self.metrics_collector.configs_processed._value.get()
            
            # Source metrics
            if hasattr(self.metrics_collector, 'sources_total'):
                metrics['sources_total'] = self.metrics_collector.sources_total._value.get()
            
            # Error metrics
            if hasattr(self.metrics_collector, 'errors_total'):
                metrics['errors_total'] = self.metrics_collector.errors_total._value.get()
            
            # Latency metrics
            if hasattr(self.metrics_collector, 'processing_latency'):
                hist = self.metrics_collector.processing_latency
                metrics['avg_processing_time'] = hist._sum._value.get() / max(hist._count._value.get(), 1)
            
            return metrics
        except Exception as e:
            print(f"Error collecting real metrics: {e}")
            return self._collect_mock_metrics()
    
    def _collect_mock_metrics(self) -> Dict[str, Any]:
        """Collect mock metrics for demonstration."""
        # Simulate increasing metrics
        self.mock_metrics["configs_processed"] += 10
        self.mock_metrics["sources_active"] = min(50, self.mock_metrics["sources_active"] + 1)
        self.mock_metrics["merge_operations"] += 1
        self.mock_metrics["errors_count"] += (1 if time.time() % 60 < 10 else 0)
        self.mock_metrics["avg_processing_time"] = 0.5 + (time.time() % 10) / 20
        
        return self.mock_metrics
    
    def _get_source_health(self) -> Dict[str, Any]:
        """Get source health information."""
        return {
            "healthy_sources": 45,
            "degraded_sources": 3,
            "failed_sources": 2,
            "total_sources": 50,
            "last_check": datetime.now().isoformat(),
            "health_score": 0.92
        }
    
    def _get_protocol_distribution(self) -> Dict[str, Any]:
        """Get protocol distribution."""
        return {
            "vmess": 35,
            "vless": 25,
            "trojan": 20,
            "shadowsocks": 15,
            "wireguard": 3,
            "openvpn": 2,
            "total": 100
        }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "cpu_usage": 45.2,
            "memory_usage": 67.8,
            "disk_io": 12.3,
            "network_throughput": 89.1,
            "active_connections": 156,
            "queue_depth": 23
        }
    
    def start_metrics_broadcast(self):
        """Start broadcasting metrics updates to connected clients."""
        def broadcast_loop():
            while True:
                try:
                    metrics = self._collect_real_metrics() if self.metrics_collector else self._collect_mock_metrics()
                    self.socketio.emit('metrics_update', metrics)
                    time.sleep(5)  # Update every 5 seconds
                except Exception as e:
                    print(f"Error in metrics broadcast: {e}")
                    time.sleep(10)
        
        broadcast_thread = threading.Thread(target=broadcast_loop, daemon=True)
        broadcast_thread.start()
    
    def run(self, debug: bool = False):
        """Run the dashboard."""
        print(f"Starting VPN Merger Monitoring Dashboard on {self.host}:{self.port}")
        print(f"Metrics available: {METRICS_AVAILABLE}")
        print(f"Tracing available: {TRACING_AVAILABLE}")
        
        # Start metrics broadcasting
        self.start_metrics_broadcast()
        
        # Run the Flask app
        self.socketio.run(self.app, host=self.host, port=self.port, debug=debug)


def create_dashboard_templates():
    """Create HTML templates for the dashboard."""
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VPN Merger Monitoring Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-5px);
        }
        .metric-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #555;
            margin-bottom: 10px;
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        .metric-unit {
            font-size: 0.8em;
            color: #888;
        }
        .charts-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
        }
        .chart-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .chart-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #555;
            margin-bottom: 15px;
            text-align: center;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-healthy { background-color: #4CAF50; }
        .status-degraded { background-color: #FF9800; }
        .status-failed { background-color: #F44336; }
        .refresh-info {
            text-align: center;
            color: white;
            margin-top: 20px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 VPN Merger Monitoring Dashboard</h1>
            <p>Real-time metrics and performance monitoring</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">Configs Processed</div>
                <div class="metric-value" id="configs-processed">0</div>
                <div class="metric-unit">total</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Active Sources</div>
                <div class="metric-value" id="sources-active">0</div>
                <div class="metric-unit">sources</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Merge Operations</div>
                <div class="metric-value" id="merge-operations">0</div>
                <div class="metric-unit">operations</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Error Rate</div>
                <div class="metric-value" id="error-rate">0</div>
                <div class="metric-unit">%</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Avg Processing Time</div>
                <div class="metric-value" id="avg-processing-time">0</div>
                <div class="metric-unit">ms</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Health Score</div>
                <div class="metric-value" id="health-score">0</div>
                <div class="metric-unit">%</div>
            </div>
        </div>
        
        <div class="charts-container">
            <div class="chart-card">
                <div class="chart-title">Protocol Distribution</div>
                <canvas id="protocolChart" width="400" height="300"></canvas>
            </div>
            <div class="chart-card">
                <div class="chart-title">Source Health Status</div>
                <canvas id="healthChart" width="400" height="300"></canvas>
            </div>
            <div class="chart-card">
                <div class="chart-title">Performance Metrics</div>
                <canvas id="performanceChart" width="400" height="300"></canvas>
            </div>
            <div class="chart-card">
                <div class="chart-title">Processing Timeline</div>
                <canvas id="timelineChart" width="400" height="300"></canvas>
            </div>
        </div>
        
        <div class="refresh-info">
            <p>🔄 Auto-refreshing every 5 seconds | Last update: <span id="last-update">Never</span></p>
        </div>
    </div>

    <script>
        // Initialize Socket.IO connection
        const socket = io();
        
        // Chart instances
        let protocolChart, healthChart, performanceChart, timelineChart;
        
        // Initialize charts
        function initializeCharts() {
            // Protocol Distribution Chart
            const protocolCtx = document.getElementById('protocolChart').getContext('2d');
            protocolChart = new Chart(protocolCtx, {
                type: 'doughnut',
                data: {
                    labels: ['VMess', 'VLESS', 'Trojan', 'Shadowsocks', 'WireGuard', 'OpenVPN'],
                    datasets: [{
                        data: [35, 25, 20, 15, 3, 2],
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            
            // Health Status Chart
            const healthCtx = document.getElementById('healthChart').getContext('2d');
            healthChart = new Chart(healthCtx, {
                type: 'bar',
                data: {
                    labels: ['Healthy', 'Degraded', 'Failed'],
                    datasets: [{
                        label: 'Sources',
                        data: [45, 3, 2],
                        backgroundColor: ['#4CAF50', '#FF9800', '#F44336']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
            
            // Performance Metrics Chart
            const performanceCtx = document.getElementById('performanceChart').getContext('2d');
            performanceChart = new Chart(performanceCtx, {
                type: 'radar',
                data: {
                    labels: ['CPU', 'Memory', 'Disk I/O', 'Network', 'Connections', 'Queue'],
                    datasets: [{
                        label: 'Usage %',
                        data: [45, 68, 12, 89, 60, 23],
                        backgroundColor: 'rgba(102, 126, 234, 0.2)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        pointBackgroundColor: 'rgba(102, 126, 234, 1)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
            
            // Timeline Chart
            const timelineCtx = document.getElementById('timelineChart').getContext('2d');
            timelineChart = new Chart(timelineCtx, {
                type: 'line',
                data: {
                    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                    datasets: [{
                        label: 'Configs/Hour',
                        data: [1200, 800, 1500, 2000, 1800, 1600],
                        borderColor: 'rgba(102, 126, 234, 1)',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        // Update metrics display
        function updateMetrics(metrics) {
            document.getElementById('configs-processed').textContent = metrics.configs_processed || 0;
            document.getElementById('sources-active').textContent = metrics.sources_active || 0;
            document.getElementById('merge-operations').textContent = metrics.merge_operations || 0;
            
            const errorRate = metrics.errors_count || 0;
            const total = metrics.configs_processed || 1;
            document.getElementById('error-rate').textContent = ((errorRate / total) * 100).toFixed(2);
            
            document.getElementById('avg-processing-time').textContent = (metrics.avg_processing_time || 0).toFixed(1);
            
            // Update health score (mock calculation)
            const healthScore = 92; // This would come from source health data
            document.getElementById('health-score').textContent = healthScore;
            
            // Update last update timestamp
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        }
        
        // Socket event handlers
        socket.on('connect', function() {
            console.log('Connected to dashboard');
            socket.emit('request_metrics');
        });
        
        socket.on('metrics_update', function(metrics) {
            updateMetrics(metrics);
        });
        
        socket.on('status', function(data) {
            console.log('Status:', data.data);
        });
        
        // Initialize dashboard when page loads
        document.addEventListener('DOMContentLoaded', function() {
            initializeCharts();
            
            // Request initial metrics
            socket.emit('request_metrics');
            
            // Request metrics every 5 seconds as backup
            setInterval(() => {
                socket.emit('request_metrics');
            }, 5000);
        });
    </script>
</body>
</html>'''
    
    with open(os.path.join(templates_dir, 'dashboard.html'), 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    
    print(f"Dashboard templates created in {templates_dir}")


if __name__ == "__main__":
    # Create templates if they don't exist
    create_dashboard_templates()
    
    # Create and run dashboard
    dashboard = MonitoringDashboard(host="0.0.0.0", port=8080)
    dashboard.run(debug=True)
