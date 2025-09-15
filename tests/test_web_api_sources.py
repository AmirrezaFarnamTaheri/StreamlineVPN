from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from streamline_vpn.web.api import create_app, get_merger
from streamline_vpn.core.merger import StreamlineVPNMerger


class DummySourceManager:
    """A mock source manager for testing purposes."""
    def __init__(self):
        self.sources = set()

    async def add_source(self, url: str):
        if "invalid" in url:
            raise ValueError("Invalid URL")
        if url in self.sources:
            raise ValueError("Source already exists")
        self.sources.add(url)


@pytest.fixture
def client_with_mock_merger():
    """Fixture to provide a test client with a mocked merger."""
    app = create_app()

    mock_merger = MagicMock(spec=StreamlineVPNMerger)
    mock_merger.source_manager = DummySourceManager()

    async def override_get_merger():
        return mock_merger

    app.dependency_overrides[get_merger] = override_get_merger

    with TestClient(app) as c:
        yield c, mock_merger


def test_add_source_success(client_with_mock_merger):
    """Test successfully adding a new source."""
    client, merger = client_with_mock_merger
    response = client.post("/api/v1/sources", json={"url": "https://test-server.example"})

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert "https://test-server.example" in merger.source_manager.sources


def test_add_source_duplicate(client_with_mock_merger):
    """Test that adding a duplicate source returns a 400 error."""
    client, merger = client_with_mock_merger
    merger.source_manager.sources.add("https://dup.com")

    response = client.post("/api/v1/sources", json={"url": "https://dup.com"})

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_add_source_invalid_url(client_with_mock_merger):
    """Test that adding an invalid URL returns a 400 error."""
    client, _ = client_with_mock_merger

    response = client.post("/api/v1/sources", json={"url": "invalid-url"})

    assert response.status_code == 400
    assert "Invalid URL" in response.json()["detail"]
