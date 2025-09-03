import asyncio
import base64
from fastapi.testclient import TestClient

from vpn_merger.web.free_nodes_api_sqla import app  # type: ignore


client = TestClient(app)


def _sample_links():
    vmess = "vmess://" + base64.b64encode(
        ("{"
         "\"v\":\"2\",\"ps\":\"T1\",\"add\":\"vmess.example.com\",\"port\":\"443\",\"id\":\"aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee\",\"net\":\"tcp\",\"type\":\"none\",\"tls\":\"tls\""  # noqa: E501
         "}").encode()
    ).decode()
    vless = "vless://11111111-2222-3333-4444-555555555555@example.com:443?security=reality&sni=www.microsoft.com#V1"
    return [vmess, vless]


def test_health_and_ingest_and_select():
    r = client.get("/health")
    assert r.status_code == 200

    payload = {"links": _sample_links()}
    r = client.post("/api/ingest", json=payload)
    assert r.status_code == 200
    assert r.json()["ingested"] >= 1

    sel = client.get("/api/select")
    assert sel.status_code == 200
    body = sel.json()
    assert "primary" in body and body["primary"]["host"]


def test_metrics_endpoints():
    lst = client.get("/api/metrics")
    assert lst.status_code == 200
    # May be empty if background collector hasn't run yet
    if isinstance(lst.json(), list) and lst.json():
        node_id = lst.json()[0]["node_id"]
        one = client.get(f"/api/metrics/{node_id}")
        assert one.status_code in (200, 404)

