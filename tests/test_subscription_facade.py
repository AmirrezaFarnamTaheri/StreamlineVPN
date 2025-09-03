import os
import time
from fastapi.testclient import TestClient

# Ensure import path works when running from repo root
from vpn_automation.subscription_facade.app import app  # type: ignore


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"


def test_ingest_and_list():
    links = [
        "trojan://pass123@trojan.example.com:443#Sample-Trojan",
        "vless://11111111-2222-3333-4444-555555555555@example.com:443?security=reality&pbk=PUBKEY&sid=abcdef&sni=www.microsoft.com&type=tcp#Sample-REALITY",
    ]
    r = client.post("/api/ingest", json={"links": links, "replace": True})
    assert r.status_code == 200
    assert r.json()["ingested"] == 2

    rj = client.get("/api/nodes.json")
    assert rj.status_code == 200
    data = rj.json()
    assert isinstance(data, list) and len(data) == 2


def test_exports():
    rsb = client.get("/api/sub/singbox.json")
    assert rsb.status_code == 200
    assert "outbounds" in rsb.json()

    rcl = client.get("/api/sub/clash.yaml")
    assert rcl.status_code == 200
    assert "proxy-groups" in rcl.text or "proxy-groups" in rcl.content.decode("utf-8")

