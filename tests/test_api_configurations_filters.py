from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from streamline_vpn.web.api import create_app, get_merger
from streamline_vpn.models.configuration import VPNConfiguration, Protocol


def make_cfg(protocol: Protocol, server: str) -> VPNConfiguration:
    return VPNConfiguration(protocol=protocol, server=server, port=443, user_id="u")


@pytest.fixture
def client_with_configs(monkeypatch):
    app = create_app()
    mock_merger = MagicMock()
    cfgs = [make_cfg(Protocol.VMESS, "a"), make_cfg(Protocol.VLESS, "b")]
    mock_merger.get_configurations = MagicMock(return_value=cfgs)
    # Override get_merger at module level (function is not a FastAPI dependency here)
    import streamline_vpn.web.api as api_module
    monkeypatch.setattr(api_module, "get_merger", lambda: mock_merger)
    with TestClient(app) as c:
        yield c


def test_configurations_filter_protocol(client_with_configs):
    resp = client_with_configs.get("/api/v1/configurations?protocol=vmess")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for cfg in data["configurations"]:
        assert cfg["protocol"] == "vmess"


def test_configurations_pagination(client_with_configs):
    resp = client_with_configs.get("/api/v1/configurations?limit=1&offset=1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 1
    assert data["offset"] == 1
    assert len(data["configurations"]) == 1
