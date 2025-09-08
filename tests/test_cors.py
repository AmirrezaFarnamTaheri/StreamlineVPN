import importlib.util
import pathlib
import sys

from fastapi.testclient import TestClient

from streamline_vpn.settings import reset_settings_cache
from streamline_vpn.web.settings import Settings as WebSettings
from streamline_vpn.web.static_server import EnhancedStaticServer

API_MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "src/streamline_vpn/web/api.py"
)
spec = importlib.util.spec_from_file_location(
    "streamline_vpn.web.api_v2", API_MODULE_PATH
)
web_api = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = web_api
spec.loader.exec_module(web_api)
create_app = web_api.create_app


def test_api_disallowed_origin_rejected(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", '["https://allowed.com"]')
    reset_settings_cache()
    app = create_app()
    client = TestClient(app)
    resp_allowed = client.options(
        "/",
        headers={
            "Origin": "https://allowed.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp_allowed.status_code == 200

    resp_blocked = client.options(
        "/",
        headers={
            "Origin": "https://blocked.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp_blocked.status_code == 400


def test_static_server_disallowed_origin_rejected():
    settings = WebSettings(
        ALLOWED_ORIGINS=["https://allowed.com"], UPDATE_INTERVAL=1
    )
    server = EnhancedStaticServer(settings)
    with TestClient(server.app) as client:
        resp_allowed = client.options(
            "/api/status",
            headers={
                "Origin": "https://allowed.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp_allowed.status_code == 200

        resp_blocked = client.options(
            "/api/status",
            headers={
                "Origin": "https://blocked.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp_blocked.status_code == 400
