"""Tests for unified API endpoints using a mocked merger."""

from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from streamline_vpn.models.source import SourceMetadata, SourceTier
from streamline_vpn.models.configuration import VPNConfiguration, Protocol
from streamline_vpn.web.unified_api import create_unified_app


class DummyMerger:
    """Minimal merger stub for API tests."""

    def __init__(self, *args, **kwargs):  # pragma: no cover - signature
        self.source_manager = SimpleNamespace(
            sources={
                "http://test-server.example": SourceMetadata(
                    url="http://test-server.example", tier=SourceTier.PREMIUM
                )
            }
        )
        self.results = [
            VPNConfiguration(protocol=Protocol.VMESS, server="s", port=443)
        ]

    async def initialize(self):  # pragma: no cover - trivial
        return None

    async def shutdown(self):  # pragma: no cover - trivial
        return None

    async def process_all(self, *args, **kwargs):  # pragma: no cover - simple
        return {"success": True}


@pytest.fixture
def client(monkeypatch):
    """Test client with merger patched to dummy implementation."""

    monkeypatch.setattr(
        "streamline_vpn.web.unified_api.StreamlineVPNMerger", DummyMerger
    )
    app = create_unified_app()
    with TestClient(app) as c:
        yield c


def test_sources_and_configurations_endpoints(client):
    """Ensure sources and configurations are returned from the API."""

    resp = client.get("/api/v1/sources")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1

    resp2 = client.get("/api/v1/configurations")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["total"] == 1


def test_pipeline_run_and_url_validation(client):
    """Pipeline execution and URL validation endpoints."""

    run_resp = client.post("/api/v1/pipeline/run", json={})
    assert run_resp.status_code == 200
    assert run_resp.json()["status"] == "completed"

    val_resp = client.post(
        "/api/v1/sources/validate-urls",
        json={"urls": ["http://ok", "not-a-url"]},
    )
    assert val_resp.status_code == 200
    body = val_resp.json()
    assert body["checked"] == 2
