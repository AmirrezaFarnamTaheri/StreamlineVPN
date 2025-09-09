from unittest.mock import patch
from fastapi.testclient import TestClient

from streamline_vpn.web.api import create_app
from streamline_vpn.models.formats import OutputFormat


def test_run_pipeline_valid_formats(tmp_path):
    """
    The pipeline endpoint should accept valid formats and return a 202 status.
    """
    app = create_app()
    with TestClient(app) as client, patch("pathlib.Path.is_file", return_value=True):
        response = client.post(
            "/api/v1/pipeline/run",
            json={
                "config_path": "tests/fixtures/test_sources.yaml",
                "output_dir": str(tmp_path),
                "formats": [OutputFormat.JSON.value, OutputFormat.CLASH.value],
            },
        )
        assert response.status_code == 202


def test_run_pipeline_invalid_format(tmp_path):
    """
    The pipeline endpoint should reject invalid formats with a 400 status.
    """
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/pipeline/run",
            json={
                "config_path": "tests/fixtures/test_sources.yaml",
                "output_dir": str(tmp_path),
                "formats": ["json", "invalid-format"],
            },
        )
        assert response.status_code == 400  # Validation error
        assert "invalid-format" in response.text
