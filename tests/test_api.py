import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from streamline_vpn.web.api import create_app, get_merger
from streamline_vpn.core.merger import StreamlineVPNMerger


@pytest.fixture(scope="module")
def client():
    app = create_app()
    # Mock the merger dependency for tests
    mock_merger_instance = AsyncMock(spec=StreamlineVPNMerger)
    mock_merger_instance.source_manager = AsyncMock()

    async def override_get_merger():
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
    assert "invalid_format" in str(data["detail"])


def test_service_unavailable_if_merger_fails(monkeypatch):
    """
    If the merger fails to initialize, endpoints should return a 503 error.
    """
    # Mock the StreamlineVPNMerger to raise an exception on init
    with patch("streamline_vpn.web.api.StreamlineVPNMerger", side_effect=RuntimeError("Merger Boom!")):
        app = create_app()
        with TestClient(app) as client:
            # The health endpoint should reflect the degraded state
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "degraded"

            # Any endpoint depending on the merger should fail
            response = client.get("/api/v1/statistics")
            assert response.status_code == 503
            assert response.json()["detail"] == "Service not initialized"
