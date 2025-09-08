"""Tests for background job cleanup in the web API."""

from datetime import datetime, timedelta
from pathlib import Path
import importlib.util
import importlib
import sys

from fastapi.testclient import TestClient


def load_api_module():
    """Load the standalone API module (not the package)."""
    module_path = Path(__file__).resolve().parents[1] / "src/streamline_vpn/web/api.py"
    importlib.import_module("streamline_vpn.web")  # ensure parent package loaded
    spec = importlib.util.spec_from_file_location(
        "streamline_vpn.web.api_module", module_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["streamline_vpn.web.api_module"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_cleanup_removes_old_jobs_and_keeps_active():
    api_module = load_api_module()
    app = api_module.create_app()
    with TestClient(app) as client:
        now = datetime.now()
        api_module.processing_jobs.clear()
        api_module.processing_jobs["old"] = {
            "status": "completed",
            "completed_at": (now - timedelta(hours=2)).isoformat(),
        }
        api_module.processing_jobs["recent"] = {
            "status": "completed",
            "completed_at": now.isoformat(),
        }
        api_module.processing_jobs["running"] = {
            "status": "running",
            "started_at": now.isoformat(),
        }

        response = client.post("/api/v1/pipeline/cleanup")
        assert response.status_code == 200
        data = response.json()
        assert data["removed"] == 1
        assert "old" not in api_module.processing_jobs
        assert "recent" in api_module.processing_jobs
        assert "running" in api_module.processing_jobs

