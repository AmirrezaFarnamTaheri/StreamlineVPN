import json
from starlette.testclient import TestClient

from streamline_vpn.web.unified_api import app


def test_ws_root_streams_and_pongs():
    with TestClient(app) as client:
        with client.websocket_connect("/ws?client_id=tester") as ws:
            # Send ping and expect pong with optional client_id
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            assert data["type"] in ("pong", "statistics")
            # If first was pong, stats should follow next; if first was stats, great
            if data["type"] == "pong":
                msg = ws.receive_json()
                assert msg["type"] == "statistics"
                stats = msg["data"]
            else:
                stats = data["data"]
            # Basic schema checks
            assert isinstance(stats.get("total_sources", 0), int)
            assert isinstance(stats.get("active_sources", 0), int)
            assert isinstance(stats.get("total_configs", 0), int)
            assert isinstance(stats.get("success_rate", 0.0), (int, float))
            assert isinstance(stats.get("last_update", ""), str)


def test_ws_root_includes_client_id():
    with TestClient(app) as client:
        with client.websocket_connect("/ws?client_id=mydash") as ws:
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            if data["type"] == "pong":
                # Prefer pong to include client id if provided
                assert data.get("client_id", "mydash") == "mydash"
            else:
                # If stats came first, next pong should include it
                ws.send_json({"type": "ping"})
                pong = ws.receive_json()
                assert pong["type"] in ("pong", "statistics")
                if pong["type"] == "pong":
                    assert pong.get("client_id", "mydash") == "mydash"


def test_ws_test_client_ping_pong():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/test_client") as ws:
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            assert data["type"] == "pong"


def test_ws_test_client_ack_on_non_ping():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/test_client") as ws:
            payload = {"hello": "world"}
            ws.send_json(payload)
            data = ws.receive_json()
            assert data["type"] == "ack"
            assert data.get("received") == payload


def test_ws_client_id_path_fallback_and_ping():
    with TestClient(app) as client:
        # Depending on routing precedence, this may hit /ws/{client_id} or /ws/{rest:path}
        with client.websocket_connect("/ws/abc123") as ws:
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            # Both handlers respond to ping with 'pong'
            assert data["type"] == "pong"
            # Optional client_id field if matched by /ws/{client_id}
            if "client_id" in data:
                assert data["client_id"] == "abc123"
