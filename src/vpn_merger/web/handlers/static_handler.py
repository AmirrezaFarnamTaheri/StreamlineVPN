#!/usr/bin/env python3
"""
Static Handler for Enhanced Web Interface
========================================

Handles static content and HTML generation.
"""

import logging
from pathlib import Path
from typing import Any, Dict

from aiohttp.web import Response

logger = logging.getLogger(__name__)


class StaticHandler:
    """Handles static content and HTML generation."""
    
    def __init__(self):
        """Initialize static handler."""
        self.static_dir = Path(__file__).parent.parent / "static"
    
    def generate_enhanced_interface_html(self) -> str:
        """Generate the enhanced interface HTML.

        If a template file exists in `static/enhanced_interface.html`, load it.
        Otherwise return a compact built-in fallback for robustness.
        """
        try:
            template_path = self.static_dir / "enhanced_interface.html"
            if template_path.exists():
                return template_path.read_text(encoding="utf-8")
        except Exception:
            # Fall back to embedded content below
            pass
        return """
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>VPN Merger - Interface</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; }
    header { background: #4c63d2; color: #fff; padding: 1rem 1.25rem; }
    main { padding: 1rem 1.25rem; }
    .card { background: #fff; border-radius: 8px; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,.1); margin-bottom: 1rem; }
    .row { display: grid; grid-template-columns: repeat(auto-fit,minmax(280px,1fr)); gap: 1rem; }
    button { background:#4c63d2;color:#fff;border:0;border-radius:6px;padding:.6rem 1rem;cursor:pointer }
    pre { white-space: pre-wrap; word-break: break-word; background:#0b1021; color:#e7e9ff; padding: .75rem; border-radius:6px; max-height: 260px; overflow:auto }
  </style>
</head>
<body>
  <header>
    <h1>VPN Merger</h1>
  </header>
  <main>
    <div class=\"row\">
      <section class=\"card\">
        <h3>Status</h3>
        <pre id=\"status\">Loading...</pre>
        <button onclick=\"refreshStatus()\">Refresh</button>
      </section>
      <section class=\"card\">
        <h3>Health</h3>
        <pre id=\"health\">Loading...</pre>
        <button onclick=\"refreshHealth()\">Refresh</button>
      </section>
    </div>
    <section class=\"card\">
      <h3>Operations</h3>
      <label>Max Concurrent: <input id=\"max-concurrent\" type=\"number\" value=\"10\" min=\"1\" max=\"100\" /></label>
      <button onclick=\"runMerge()\">Run Merge</button>
      <button onclick=\"runExport()\">Export All</button>
      <pre id=\"ops-result\"></pre>
    </section>
  </main>
  <script>
    async function refreshStatus(){
      const r = await fetch('/api/status');
      const j = await r.json();
      document.getElementById('status').textContent = JSON.stringify(j,null,2);
    }
    async function refreshHealth(){
      const r = await fetch('/api/health');
      const j = await r.json();
      document.getElementById('health').textContent = JSON.stringify(j,null,2);
    }
    async function runMerge(){
      const mc = parseInt(document.getElementById('max-concurrent').value)||10;
      const r = await fetch('/api/merge',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({max_concurrent:mc})});
      const j = await r.json();
      document.getElementById('ops-result').textContent = JSON.stringify(j,null,2);
    }
    async function runExport(){
      const r = await fetch('/api/export',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({format:'all', output_dir:'output'})});
      const j = await r.json();
      document.getElementById('ops-result').textContent = JSON.stringify(j,null,2);
    }
    refreshStatus();
    refreshHealth();
  </script>
</body>
</html>
        """
                content.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to selected tab
            event.target.classList.add('active');
            
            currentTab = tabName;
        }
        
        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };
            
            ws.onclose = function() {
                setTimeout(connectWebSocket, 5000);
            };
        }
        
        function handleWebSocketMessage(data) {
            switch(data.type) {
                case 'status_update':
                case 'background_update':
                    updateDashboard(data.data);
                    break;
                case 'merge_completed':
                    showResult('merge-result', 'success', `Merge completed: ${data.data.configs_generated} configurations generated`);
                    break;
                case 'export_completed':
                    showResult('export-result', 'success', `Export completed: ${data.data.files_generated.length} files generated`);
                    break;
                case 'config_updated':
                    showResult('config-result', 'success', 'Configuration updated successfully');
                    break;
            }
        }
        
        function updateDashboard(data) {
            // Update system status
            const systemStatus = document.getElementById('system-status');
            systemStatus.innerHTML = `
                <div class="metric">
                    <span>Status</span>
                    <span class="status healthy">Running</span>
                </div>
                <div class="metric">
                    <span>Active Connections</span>
                    <span>${data.active_connections || 0}</span>
                </div>
                <div class="metric">
                    <span>Monitoring</span>
                    <span class="status ${data.monitoring_active ? 'healthy' : 'warning'}">${data.monitoring_active ? 'Active' : 'Inactive'}</span>
                </div>
            `;
            
            // Update health status
            const healthStatus = document.getElementById('health-status');
            healthStatus.innerHTML = `
                <div class="metric">
                    <span>Health</span>
                    <span class="status ${data.health_status === 'healthy' ? 'healthy' : 'unhealthy'}">${data.health_status || 'Unknown'}</span>
                </div>
            `;
        }
        
        async function runMerge() {
            const strategy = document.getElementById('merge-strategy').value;
            const maxConcurrent = parseInt(document.getElementById('max-concurrent').value);
            
            showLoading('merge-result');
            
            try {
                const response = await fetch('/api/merge', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ strategy, max_concurrent: maxConcurrent })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showResult('merge-result', 'success', `Merge completed: ${result.configs_generated} configurations generated`);
                } else {
                    showResult('merge-result', 'error', `Merge failed: ${result.error}`);
                }
            } catch (error) {
                showResult('merge-result', 'error', `Merge failed: ${error.message}`);
            }
        }
        
        async function runExport() {
            const format = document.getElementById('export-format').value;
            const outputDir = document.getElementById('output-dir').value;
            
            showLoading('export-result');
            
            try {
                const response = await fetch('/api/export', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ format, output_dir: outputDir })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showResult('export-result', 'success', `Export completed: ${result.files_generated.length} files generated`);
                } else {
                    showResult('export-result', 'error', `Export failed: ${result.error}`);
                }
            } catch (error) {
                showResult('export-result', 'error', `Export failed: ${error.message}`);
            }
        }
        
        async function startMonitoring() {
            try {
                const response = await fetch('/api/monitoring/start', { method: 'POST' });
                const result = await response.json();
                
                if (response.ok) {
                    showResult('monitoring-status', 'success', result.message);
                } else {
                    showResult('monitoring-status', 'error', result.error);
                }
            } catch (error) {
                showResult('monitoring-status', 'error', `Failed to start monitoring: ${error.message}`);
            }
        }
        
        async function stopMonitoring() {
            try {
                const response = await fetch('/api/monitoring/stop', { method: 'POST' });
                const result = await response.json();
                
                if (response.ok) {
                    showResult('monitoring-status', 'success', result.message);
                } else {
                    showResult('monitoring-status', 'error', result.error);
                }
            } catch (error) {
                showResult('monitoring-status', 'error', `Failed to stop monitoring: ${error.message}`);
            }
        }
        
        async function updateConfig() {
            const configText = document.getElementById('config-text').value;
            
            try {
                const config = JSON.parse(configText);
                
                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showResult('config-result', 'success', result.message);
                } else {
                    showResult('config-result', 'error', result.error);
                }
            } catch (error) {
                showResult('config-result', 'error', `Invalid JSON: ${error.message}`);
            }
        }
        
        function showLoading(elementId) {
            document.getElementById(elementId).innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading...</p></div>';
        }
        
        function showResult(elementId, type, message) {
            document.getElementById(elementId).innerHTML = `<div class="alert ${type}">${message}</div>`;
        }
        
        // Initialize
        connectWebSocket();
        
        // Load initial data
        fetch('/api/status')
            .then(response => response.json())
            .then(data => updateDashboard(data));
            
        fetch('/api/health')
            .then(response => response.json())
            .then(data => {
                const healthStatus = document.getElementById('health-status');
                healthStatus.innerHTML = `
                    <div class="metric">
                        <span>Overall Status</span>
                        <span class="status ${data.overall_status}">${data.overall_status}</span>
                    </div>
                `;
            });
            
        fetch('/api/config')
            .then(response => response.json())
            .then(data => {
                document.getElementById('config-text').value = JSON.stringify(data, null, 2);
            });
    </script>
</body>
</html>
        """
    
    async def handle_main_interface(self, request) -> Response:
        """Handle main interface page."""
        html_content = self.generate_enhanced_interface_html()
        return Response(text=html_content, content_type="text/html")

