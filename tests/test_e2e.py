import pytest
from aiohttp import web
from pathlib import Path
import yaml

import pytest_asyncio
from unittest.mock import patch, AsyncMock

from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.models.configuration import VPNConfiguration, ProtocolType


@pytest_asyncio.fixture
async def mock_vpn_server(aiohttp_server):
    async def handler(request):
        return web.Response(text="vmess://test_config")

    app = web.Application()
    app.router.add_get("/test_source", handler)
    server = await aiohttp_server(app)
    return server


@pytest.fixture
def temp_config_file(tmp_path, mock_vpn_server):
    config = {
        "sources": {
            "reliable": {
                "urls": [
                    {
                        "url": f"http://{mock_vpn_server.host}:{mock_vpn_server.port}/test_source",
                        "weight": 1.0,
                        "protocols": ["vmess"],
                    }
                ]
            }
        }
    }
    config_path = tmp_path / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path


@pytest.mark.asyncio
async def test_end_to_end_processing(
    temp_config_file, tmp_path, mock_vpn_server
):
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    test_url = (
        f"http://{mock_vpn_server.host}:{mock_vpn_server.port}/test_source"
    )
    with patch(
        "streamline_vpn.security.manager.SecurityManager.validate_source",
        return_value={"is_safe": True},
    ), patch(
        "streamline_vpn.core.source_manager.SourceManager.get_active_sources",
        new_callable=AsyncMock,
        return_value=[test_url],
    ), patch(
        "streamline_vpn.core.processing.parser.ConfigurationParser.parse_configuration",
        return_value=VPNConfiguration(
            protocol=ProtocolType.VMESS,
            server="example.com",
            port=443,
            user_id="test",
        ),
    ):
        merger = StreamlineVPNMerger(config_path=str(temp_config_file))
        result = await merger.process_all(output_dir=str(output_dir))

    assert result["success"]
    assert result["sources_processed"] == 1
    assert result["configurations_found"] > 0

    # Check that output files were created
    output_files = list(output_dir.iterdir())
    assert len(output_files) > 0
