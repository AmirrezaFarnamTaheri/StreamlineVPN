"""Tests for the `/api/v1/statistics` endpoint in `web/api.py`."""

import sys
from importlib import import_module, util
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient


def load_web_api_module():
    """Dynamically load the `web/api.py` module as a submodule."""
    # Ensure 'src' is on sys.path so package imports work
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    # Ensure parent package is loaded so relative imports work
    import_module("streamline_vpn.web")
    module_path = src_path / "streamline_vpn" / "web" / "api.py"
    spec = util.spec_from_file_location(
        "streamline_vpn.web.api_v1", module_path
    )
    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_statistics_returns_successful_sources():
    """The statistics endpoint should expose `successful_sources`."""

    web_api = load_web_api_module()
    app = web_api.create_app()
    client = TestClient(app)

    mock_merger = Mock()
    mock_merger.get_statistics = AsyncMock(
        return_value={
            "total_configs": 10,
            "successful_sources": 5,
            "success_rate": 0.5,
            "end_time": "now",
        }
    )
    mock_merger.get_configurations = AsyncMock(return_value=[])

    with patch.object(web_api, "get_merger", return_value=mock_merger):
        response = client.get("/api/v1/statistics")

    assert response.status_code == 200
    data = response.json()
    assert data["successful_sources"] == 5
    assert data["active_sources"] == 5
