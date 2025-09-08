import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from streamline_vpn.models import OutputFormat


def load_api_app():
    api_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "streamline_vpn"
        / "web"
        / "api.py"
    )
    spec = importlib.util.spec_from_file_location(
        "streamline_vpn.web.api_app", api_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # type: ignore[assignment]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module.create_app


def get_client():
    app_factory = load_api_app()
    app = app_factory()
    return TestClient(app)


async def _noop(*args, **kwargs):
    return None


async def _fake_process_all(self, output_dir: str, formats: list):
    return {"success": True, "formats": formats}


def test_run_pipeline_valid_formats(tmp_path):
    config = "tests/fixtures/test_sources.yaml"
    with get_client() as app_client, patch(
        "streamline_vpn.core.merger.StreamlineVPNMerger.initialize", _noop
    ), patch(
        "streamline_vpn.core.merger.StreamlineVPNMerger.process_all",
        _fake_process_all,
    ):
        resp = app_client.post(
            "/api/v1/pipeline/run",
            json={
                "config_path": config,
                "output_dir": str(tmp_path),
                "formats": [OutputFormat.JSON.value, OutputFormat.CLASH.value],
            },
        )
        assert resp.status_code == 200


def test_run_pipeline_invalid_format(tmp_path):
    config = "tests/fixtures/test_sources.yaml"
    with get_client() as app_client, patch(
        "streamline_vpn.core.merger.StreamlineVPNMerger.initialize", _noop
    ), patch(
        "streamline_vpn.core.merger.StreamlineVPNMerger.process_all",
        _fake_process_all,
    ):
        resp = app_client.post(
            "/api/v1/pipeline/run",
            json={
                "config_path": config,
                "output_dir": str(tmp_path),
                "formats": ["json", "invalid"],
            },
        )
        assert resp.status_code == 400
        assert "Unsupported formats" in resp.json()["detail"]
