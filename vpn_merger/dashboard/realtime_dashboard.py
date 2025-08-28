from __future__ import annotations

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import json


app = FastAPI()


class DashboardState:
    def __init__(self):
        self.clients: list[WebSocket] = []
        self.stats = {
            'total_sources': 0,
            'active_sources': 0,
            'total_configs': 0,
            'valid_configs': 0,
            'processing_speed': 0.0,
            'current_phase': 'idle',
            'errors': [],
            'recent_configs': [],
        }

    async def broadcast_update(self):
        if not self.clients:
            return
        message = json.dumps(self.stats)
        dead = []
        for ws in self.clients:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self.clients:
                self.clients.remove(ws)


state = DashboardState()


@app.get("/")
async def get_dashboard():
    return HTMLResponse("""<html><body><h1>VPN Merger Dashboard</h1></body></html>""")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        if websocket in state.clients:
            state.clients.remove(websocket)

