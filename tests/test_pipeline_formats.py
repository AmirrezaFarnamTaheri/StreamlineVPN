import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def pipeline_client():
    spec = importlib.util.spec_from_file_location(
        "streamline_vpn.web.pipeline_api",
        Path("src/streamline_vpn/web/api.py"),
    )
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    app = api_module.create_app()
    with TestClient(app) as client:
        yield client


def test_run_pipeline_valid_formats(pipeline_client):
    """Pipeline accepts valid format combinations."""
    with patch(
        "streamline_vpn.core.merger.StreamlineVPNMerger.initialize",
        new=AsyncMock(return_value=None),
    ), patch(
        "streamline_vpn.core.merger.StreamlineVPNMerger.process_all",
        new=AsyncMock(return_value={"status": "success"}),
    ):
        response = pipeline_client.post(
            "/api/v1/pipeline/run",
            json={
                "config_path": "tests/fixtures/test_sources.yaml",
                "output_dir": "output",
                "formats": ["json", "clash"],
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_run_pipeline_invalid_format(pipeline_client):
    """Pipeline rejects unsupported formats."""
    response = pipeline_client.post(
        "/api/v1/pipeline/run",
        json={
            "config_path": "tests/fixtures/test_sources.yaml",
            "output_dir": "output",
            "formats": ["json", "invalid"],
        },
    )
    assert response.status_code == 400
    assert "Unsupported formats" in response.json()["detail"]
