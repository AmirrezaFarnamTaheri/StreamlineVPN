from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
import json
import os


app = FastAPI()


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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(default=None)):
    expected = os.environ.get("DASHBOARD_TOKEN")
    if expected and token != expected:
        # Close with policy violation (1008)
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
        <title>VPN Merger Dashboard</title>
        <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
    </head>
    <body>
        <h1>VPN Merger Status</h1>
        <div id=\"stats\">
            <div>Total Configs: <span id=\"total-configs\">0</span></div>
            <div>Active Sources: <span id=\"active-sources\">0</span></div>
            <div>Success Rate: <span id=\"success-rate\">0%</span></div>
        </div>
        <canvas id=\"performanceChart\" width=\"400\" height=\"200\"></canvas>
        <div id=\"recent-configs\">
            <h3>Recent Configs Found</h3>
            <ul id=\"config-list\"></ul>
        </div>
        <script>
            const ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            function updateDashboard(data) {
                document.getElementById('total-configs').textContent = data.total_configs || 0;
                document.getElementById('active-sources').textContent = data.active_sources || 0;
                document.getElementById('success-rate').textContent = (data.success_rate || 0) + '%';
                if (data.new_config) {
                    const li = document.createElement('li');
                    li.textContent = `${data.new_config.protocol} - ${data.new_config.host}:${data.new_config.port} (${data.new_config.ping_ms}ms)`;
                    document.getElementById('config-list').prepend(li);
                }
            }
        </script>
    </body>
    </html>
    """)


