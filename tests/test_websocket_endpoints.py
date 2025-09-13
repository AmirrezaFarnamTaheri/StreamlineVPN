from starlette.testclient import TestClient

from streamline_vpn.web.unified_api import app


def test_ws_connection_and_ping():
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            # Initial connection message
            msg = ws.receive_json()
            assert msg["type"] == "connection"
            assert msg["status"] == "connected"
            assert "client_id" in msg

            # Ping-pong
            ws.send_json({"type": "ping"})
            pong = ws.receive_json()
            assert pong["type"] == "pong"


def test_ws_get_stats_and_echo():
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            # Consume initial connection message
            _ = ws.receive_json()
            # Request stats (may depend on merger availability)
            ws.send_json({"type": "get_stats"})
            data = ws.receive_json()
            # Either statistics or echo if merger not initialized yet
            assert data["type"] in ("statistics", "echo")

            # Unknown type -> echo
            payload = {"type": "unknown", "value": 42}
            ws.send_json(payload)
            echo = ws.receive_json()
            assert echo["type"] == "echo"
            assert echo.get("received") == payload
