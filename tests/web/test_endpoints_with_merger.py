import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from src.streamline_vpn.web.unified_api import create_unified_app
from src.streamline_vpn.models.configuration import VPNConfiguration, Protocol

@pytest.fixture
def mock_merger():
    """Provides a mock merger instance."""
    merger = MagicMock()
    merger.source_manager = MagicMock()
    merger.source_manager.sources = {"tier1": ["http://test.com"]}
    merger.get_configurations = MagicMock(return_value=[VPNConfiguration(protocol=Protocol.VMESS, server="s1", port=443)])
    merger.process_all = AsyncMock()
    merger.get_statistics = AsyncMock(return_value={"total_configurations": 1})
    return merger

@pytest.fixture
def client(mock_merger):
    """Test client with a mocked merger instance."""
    with patch("src.streamline_vpn.web.unified_api.get_merger_instance", new=AsyncMock(return_value=mock_merger)):
        app = create_unified_app()
        with TestClient(app) as c:
            yield c

def test_get_sources(client):
    """Test the /api/v1/sources endpoint."""
    response = client.get("/api/v1/sources")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "tier1" in data["sources"]

def test_get_configurations(client):
    """Test the /api/v1/configurations endpoint."""
    response = client.get("/api/v1/configurations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["configurations"][0]["server"] == "s1"

def test_run_pipeline(client):
    """Test the /api/v1/pipeline/run endpoint."""
    response = client.post("/api/v1/pipeline/run")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

def test_get_statistics(client):
    """Test the /api/statistics endpoint."""
    response = client.get("/api/statistics")
    assert response.status_code == 200
    assert response.json()["total_configurations"] == 1