import pytest
from fastapi.testclient import TestClient
from streamline_vpn.web.api.server import APIServer
from streamline_vpn.settings import Settings

@pytest.fixture(scope="module")
def client():
    # Create a dummy settings object for testing
    settings = Settings(
        secret_key="test_secret",
        redis_nodes=[{"host": "localhost", "port": "6379"}]
    )

    app = APIServer(
        secret_key=settings.secret_key,
        redis_nodes=settings.redis_nodes
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
    with patch('streamline_vpn.web.api.routes.run_pipeline_main') as mock_run_pipeline:
        mock_run_pipeline.return_value = 0 # Simulate a successful run

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
