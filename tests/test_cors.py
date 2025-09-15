import importlib.util
import sys
from pathlib import Path

import pytest
import httpx
from httpx import ASGITransport

from streamline_vpn.settings import Settings


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


@pytest.mark.asyncio
async def test_disallowed_origin_rejected(monkeypatch):
    custom = Settings(
        allowed_origins=["https://allowed.com"],
        allowed_methods=["GET"],
        allowed_headers=["Content-Type"],
        allow_credentials=False,
    )

    app_factory = load_api_app()
    module = sys.modules[app_factory.__module__]
    monkeypatch.setattr(module, "get_settings", lambda: custom)

    app = app_factory()
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health", headers={"Origin": "https://bad.com"})
        assert "access-control-allow-origin" not in resp.headers
