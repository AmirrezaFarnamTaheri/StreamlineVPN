from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from streamline_vpn.web.app import create_app
from streamline_vpn.web.dependencies import get_merger
from streamline_vpn.models.configuration import VPNConfiguration, Protocol


def make_cfg(protocol: Protocol, server: str) -> VPNConfiguration:
    return VPNConfiguration(protocol=protocol, server=server, port=443, user_id="u")


@pytest.fixture
def client_with_configs():
    app = create_app()
    mock_merger = MagicMock()
    all_configs = [make_cfg(Protocol.VMESS, "a"), make_cfg(Protocol.VLESS, "b")]

    # Simulate the actual filtering behavior of the merger
    def mock_get_configurations(protocol=None, **kwargs):
        if protocol:
            return [c for c in all_configs if c.protocol.value == protocol]
        return all_configs

    mock_merger.get_configurations.side_effect = mock_get_configurations

    def override_get_merger():
        return mock_merger

    app.dependency_overrides[get_merger] = override_get_merger
    with TestClient(app) as c:
        yield c


def test_configurations_filter_protocol(client_with_configs):
    resp = client_with_configs.get("/api/v1/configurations?protocol=vmess")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    for cfg in data["configurations"]:
        assert cfg["protocol"] == "vmess"
    # Also check that the mock was called with the correct filter
    mock_merger = client_with_configs.app.dependency_overrides[get_merger]()
    mock_merger.get_configurations.assert_called_with(
        protocol="vmess", location=None, min_quality=0.0
    )


def test_configurations_pagination(client_with_configs):
    resp = client_with_configs.get("/api/v1/configurations?limit=1&offset=1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 1
    assert data["offset"] == 1
    assert len(data["configurations"]) == 1