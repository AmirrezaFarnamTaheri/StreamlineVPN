import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from streamline_vpn.web.app import create_app
from streamline_vpn.web.dependencies import get_merger
from streamline_vpn.core.merger import StreamlineVPNMerger


@pytest.fixture
def client():
    """Fixture to create a test client with a mocked merger."""
    app = create_app()
    mock_merger_instance = MagicMock(spec=StreamlineVPNMerger)
    mock_merger_instance.source_manager = MagicMock()

    def override_get_merger():
        return mock_merger_instance

    app.dependency_overrides[get_merger] = override_get_merger
    with TestClient(app) as c:
        yield c


def test_run_pipeline_endpoint(client):
    """
    Test the /api/v1/pipeline/run endpoint.
    It should accept the request and return a 202 status code.
    """
    with patch("pathlib.Path.is_file", return_value=True):
        response = client.post(
            "/api/v1/pipeline/run",
            json={
                "config_path": "tests/fixtures/test_sources.yaml",
                "output_dir": "output",
                "formats": ["json"],
            },
        )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert "job_id" in data


def test_pipeline_run_unknown_formats_rejected(client):
    """A pipeline run with unknown output formats should return a 400 error."""
    with patch("pathlib.Path.is_file", return_value=True):
        response = client.post(
            "/api/v1/pipeline/run",
            json={
                "config_path": "tests/fixtures/test_sources.yaml",
                "output_dir": "output",
                "formats": ["json", "invalid_format"],
            },
        )
    assert response.status_code == 400  # Pydantic validation error
    data = response.json()
    assert "detail" in data
    assert "formats" in str(data["detail"]).lower()


def test_service_unavailable_if_merger_fails():
    """
    If the merger fails to initialize, endpoints should return a 503 error.
    """
    mock_merger_class = MagicMock()
    mock_merger_instance = mock_merger_class.return_value
    mock_merger_instance.initialize = AsyncMock(
        side_effect=Exception("Merger initialization failed")
    )

    app = create_app(merger_class=mock_merger_class)
    with TestClient(app) as client:
        # Any endpoint depending on the merger should fail
        response = client.get("/api/v1/sources")
        assert response.status_code == 503
        assert response.json()["detail"] == "Merger not initialized"