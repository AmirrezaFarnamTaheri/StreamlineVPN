from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
import json
import os
import hmac
import secrets
from datetime import datetime, timedelta


app = FastAPI()
# Mount versioned REST API under the same app
try:
    from .rest_endpoints import api as rest_api  # type: ignore
    app.include_router(rest_api)
except Exception:
    pass
try:
    from .graphql import get_router  # type: ignore
    app.include_router(get_router())
except Exception:
    pass


class DashboardManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_status(self, message: dict):
        to_remove = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                to_remove.append(connection)
        for c in to_remove:
            if c in self.active_connections:
                self.active_connections.remove(c)


dashboard_manager = DashboardManager()


class WebSocketAuth:
    """Optional HMAC-based token verifier for WebSocket connections.

    If env DASHBOARD_HMAC_KEY is set, tokens are expected to be of the form
    client_id:timestamp_iso:hex_signature where signature = HMAC_SHA256(key, client_id:timestamp)
    and accepted within 24 hours.
    """

    def __init__(self, secret_key: str | None):
        self.secret_key = secret_key

    def generate_token(self, client_id: str) -> str:
        if not self.secret_key:
            # fallback random token when no HMAC configured
            return secrets.token_urlsafe(16)
        timestamp = datetime.utcnow().isoformat()
        message = f"{client_id}:{timestamp}"
        signature = hmac.new(self.secret_key.encode(), message.encode(), 'sha256').hexdigest()
        return f"{message}:{signature}"

    def verify(self, token: str) -> bool:
        if not self.secret_key:
            return True
        try:
            message, signature = token.rsplit(":", 1)
            expected = hmac.new(self.secret_key.encode(), message.encode(), 'sha256').hexdigest()
            if not hmac.compare_digest(signature, expected):
                return False
            # validate timestamp recency
            parts = message.split(":", 1)
            if len(parts) != 2:
                return False
            ts = parts[1]
            ts_dt = datetime.fromisoformat(ts)
            if datetime.utcnow() - ts_dt > timedelta(hours=24):
                return False
            return True
        except Exception:
            return False


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(default=None)):
    expected = os.environ.get("DASHBOARD_TOKEN")
    hmac_key = os.environ.get("DASHBOARD_HMAC_KEY")
    auth = WebSocketAuth(hmac_key)
    # HMAC verification when key is present; otherwise fallback to static token check
    if hmac_key:
        if not token or not auth.verify(token):
            await websocket.close(code=1008)
            return
    elif expected and token != expected:
        await websocket.close(code=1008)
        return
    await dashboard_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        dashboard_manager.disconnect(websocket)


@app.get("/")
async def dashboard():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <title>VPN Merger Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin:0; padding:20px; background: linear-gradient(135deg,#667eea 0%,#764ba2 100%); }
            .container { max-width:1200px; margin:0 auto; background:#fff; border-radius:20px; padding:30px; box-shadow:0 20px 60px rgba(0,0,0,.3); }
            .stats-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); gap:20px; margin:20px 0; }
            .stat-card { background: linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:#fff; padding:20px; border-radius:10px; text-align:center; }
            .stat-value { font-size:2em; font-weight:700; margin:10px 0; }
            .stat-label { opacity:.9; font-size:.9em; }
            #configChart { max-height: 360px; margin: 20px 0; }
            .recent-configs { max-height: 280px; overflow-y:auto; border:1px solid #e0e0e0; border-radius:5px; padding:10px; margin:20px 0; }
            .config-item { padding:8px; margin:5px 0; background:#f5f5f5; border-radius:5px; font-family:monospace; font-size:.85em; }
            .phase-indicator { display:inline-block; padding:5px 15px; border-radius:20px; background:#4caf50; color:#fff; margin:10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 VPN Merger Real-time Dashboard</h1>
            <div class="phase-indicator" id="phase">Phase: <span id="phaseText">Idle</span></div>
            <div class="stats-grid">
                <div class="stat-card"><div class="stat-label">Total Sources</div><div class="stat-value" id="totalSources">0</div></div>
                <div class="stat-card"><div class="stat-label">Active Sources</div><div class="stat-value" id="activeSources">0</div></div>
                <div class="stat-card"><div class="stat-label">Total Configs</div><div class="stat-value" id="totalConfigs">0</div></div>
                <div class="stat-card"><div class="stat-label">Valid Configs</div><div class="stat-value" id="validConfigs">0</div></div>
                <div class="stat-card"><div class="stat-label">Processing Speed</div><div class="stat-value"><span id="processingSpeed">0</span>/s</div></div>
                <div class="stat-card"><div class="stat-label">Invalid Hosts (total)</div><div class="stat-value" id="invalidHosts">0</div></div>
            </div>
            <canvas id="configChart"></canvas>
            <h3>Recent Configurations</h3>
            <div class="recent-configs" id="recentConfigs"></div>
        </div>
        <script>
            const ws = new WebSocket('ws://localhost:8000/ws');
            const chart = new Chart(document.getElementById('configChart'), {
                type: 'line',
                data: { labels: [], datasets: [
                        { label: 'Configs Found', data: [], borderColor: '#667eea', tension: .4 },
                        { label: 'Valid Configs', data: [], borderColor: '#764ba2', tension: .4 }
                    ] }, options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }
            });
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data || '{}');
                document.getElementById('totalSources').textContent = data.total_sources || 0;
                document.getElementById('activeSources').textContent = data.active_sources || 0;
                document.getElementById('totalConfigs').textContent = data.total_configs || 0;
                document.getElementById('validConfigs').textContent = data.valid_configs || 0;
                document.getElementById('processingSpeed').textContent = (data.processing_speed || 0).toFixed ? (data.processing_speed || 0).toFixed(1) : (data.processing_speed || 0);
                document.getElementById('phaseText').textContent = data.current_phase || 'Idle';
                if (typeof data.invalid_hosts !== 'undefined') {
                    document.getElementById('invalidHosts').textContent = data.invalid_hosts;
                }
                const now = new Date().toLocaleTimeString();
                chart.data.labels.push(now);
                chart.data.datasets[0].data.push(data.total_configs || 0);
                chart.data.datasets[1].data.push(data.valid_configs || 0);
                if (chart.data.labels.length > 20) { chart.data.labels.shift(); chart.data.datasets[0].data.shift(); chart.data.datasets[1].data.shift(); }
                chart.update();
                if (Array.isArray(data.recent_configs) && data.recent_configs.length > 0) {
                    const div = document.getElementById('recentConfigs');
                    const items = data.recent_configs.slice(-5).reverse();
                    const html = items.map(c => `<div class="config-item">${c.protocol} - ${c.host}:${c.port} (${c.ping_ms}ms)</div>`).join('');
                    div.innerHTML = html + div.innerHTML;
                    while (div.children.length > 20) { div.removeChild(div.lastChild); }
                }
            };
        </script>
    </body>
    </html>
    """)


