import pytest
from aiohttp import web
import asyncio
from pathlib import Path
import yaml

from streamline_vpn.core.merger import StreamlineVPNMerger


@pytest.fixture
async def mock_vpn_server(aiohttp_server):
    async def handler(request):
        return web.Response(text="vmess://test_config")

    app = web.Application()
    app.router.add_get('/test_source', handler)
    server = await aiohttp_server(app)
    return server


@pytest.fixture
def temp_config_file(tmp_path, mock_vpn_server):
    config = {
        'sources': {
            'test_group': {
                'urls': [
                    {
                        'url': f"http://{mock_vpn_server.host}:{mock_vpn_server.port}/test_source",
                        'weight': 1.0,
                        'protocols': ['vmess']
                    }
                ]
            }
        }
    }
    config_path = tmp_path / "test_config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    return config_path


@pytest.mark.asyncio
async def test_end_to_end_processing(temp_config_file, tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    merger = StreamlineVPNMerger(config_path=str(temp_config_file))
    result = await merger.process_all(output_dir=str(output_dir))

    assert result['success']
    assert result['sources_processed'] == 1
    assert result['configurations_found'] > 0

    # Check that output files were created
    output_files = list(output_dir.iterdir())
    assert len(output_files) > 0
