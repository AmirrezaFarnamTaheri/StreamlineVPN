import pytest
from fastapi.testclient import TestClient

from streamline_vpn.settings import Settings
from streamline_vpn.web.api.server import APIServer


@pytest.fixture(scope="module")
def client():
    # Create a dummy settings object for testing
    settings = Settings(
        secret_key="test_secret",
        redis_nodes=[{"host": "localhost", "port": "6379"}],
    )

    app = APIServer(
        secret_key=settings.secret_key, redis_nodes=settings.redis_nodes
    ).get_app()

    with TestClient(app) as c:
        yield c


def test_run_pipeline_endpoint(client):
    """
    Test the /api/v1/pipeline/run endpoint.
    """
    # We'll use the test configuration file for this test.
    # We also need to mock the run_pipeline_main function to avoid actually running the pipeline.
    from unittest.mock import patch

    with patch(
        "streamline_vpn.web.api.routes.run_pipeline_main"
    ) as mock_run_pipeline:
        mock_run_pipeline.return_value = 0  # Simulate a successful run

        response = client.post(
            "/api/v1/pipeline/run",
            json={
                "config_path": "tests/fixtures/test_sources.yaml",
                "output_dir": "output",
                "formats": ["json"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Pipeline started successfully"
        assert "job_id" in data


def test_process_unknown_formats_rejected(client):
    """Unknown output formats should return a 400 error."""
    response = client.post(
        "/api/process",
        json={"formats": ["json", "invalid"]},
    )
    assert response.status_code == 400
    data = response.json()
    assert "Unknown formats" in data["detail"]


def test_process_internal_error_returns_500(client, monkeypatch):
    """Unexpected errors should return a 500 HTTP error."""

    async def mock_initialize(self):
        pass

    async def mock_process_all(self, output_dir: str, formats: list):
        raise RuntimeError("boom")

    from streamline_vpn.core.merger import StreamlineVPNMerger

    monkeypatch.setattr(StreamlineVPNMerger, "initialize", mock_initialize)
    monkeypatch.setattr(StreamlineVPNMerger, "process_all", mock_process_all)

    response = client.post("/api/process", json={"formats": ["json"]})
    assert response.status_code == 500
    assert response.json()["detail"] == "Processing failed"


def test_get_sources_invalid_yaml(client, tmp_path, monkeypatch, caplog):
    """Malformed YAML should be logged and return a generic error."""
    bad_config = tmp_path / "sources.yaml"
    bad_config.write_text(":\n- bad")
    monkeypatch.setenv("APP_CONFIG_PATH", str(bad_config))
    with caplog.at_level("ERROR"):
        response = client.get("/api/sources")
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Invalid YAML format in sources configuration"
    )
    assert "Failed to parse sources.yaml" in caplog.text
