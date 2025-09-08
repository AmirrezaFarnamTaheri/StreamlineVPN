import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

spec = importlib.util.spec_from_file_location(
    "streamline_vpn.web.api_app",
    Path(__file__).resolve().parents[1] / "src/streamline_vpn/web/api.py",
)
api_module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = api_module
spec.loader.exec_module(api_module)
create_app = api_module.create_app


class DummySourceManager:
    def __init__(self):
        self.sources = set()

    async def add_source(self, url: str):
        if not url.startswith("http"):
            raise ValueError("Invalid or unsafe source URL")
        if url in self.sources:
            raise ValueError("Source already exists")
        self.sources.add(url)


@pytest.fixture
def client():
    app = create_app()
    merger = SimpleNamespace(source_manager=DummySourceManager())
    with patch.object(api_module, "get_merger", return_value=merger):
        with TestClient(app) as c:
            yield c, merger


def test_add_source_success(client):
    c, merger = client
    resp = c.post("/api/v1/sources/add", json={"url": "https://example.com"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    assert "https://example.com" in merger.source_manager.sources


def test_add_source_duplicate(client):
    c, merger = client
    merger.source_manager.sources.add("https://dup.com")
    resp = c.post("/api/v1/sources/add", json={"url": "https://dup.com"})
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


def test_add_source_invalid_url(client):
    c, _ = client
    resp = c.post("/api/v1/sources/add", json={"url": "not-a-url"})
    assert resp.status_code == 400
    assert "Invalid" in resp.json()["detail"]
