import pytest
from aiohttp import web
from pathlib import Path
import yaml
import pytest_asyncio
from unittest.mock import patch

from streamline_vpn.core.merger import StreamlineVPNMerger

@pytest_asyncio.fixture
async def mock_vpn_server(aiohttp_server):
    """A mock server that returns a valid vmess configuration line."""
    async def handler(request):
        # A valid base64 encoded vmess configuration
        vmess_config_b64 = "ewogICJ2IjogIjIiLAogICJwcyI6ICJUZXN0IiwKICAiYWRkIjogImV4YW1wbGUuY29tIiwKICAicG9ydCI6IDQ0MywKICAiaWQiOiAiZmQ3YWQyMTYtZDIzMy00ZmY4LWE4M2EtZTZlMGU3ODU3ZmM2IiwKICAiYWlkIjogMCwKICAibmV0IjogIndzIiwKICAidHlwZSI6ICJub25lIiwKICAiaG9zdCI6ICJleGFtcGxlLmNvbSIsCiAgInBhdGgiOiAiLyIsCiAgInRscyI6ICJ0bHMiCn0="
        # The parser expects to find full vmess:// links in the content
        return web.Response(text=f"vmess://{vmess_config_b64}")

    app = web.Application()
    app.router.add_get("/test_source", handler)
    server = await aiohttp_server(app)
    return server


@pytest.mark.asyncio
async def test_end_to_end_processing(tmp_path, mock_vpn_server):
    """
    Tests the full processing pipeline from config loading to output generation.
    """
    # 1. Create a temporary configuration file pointing to the mock server
    config = {
        "sources": {
                "reliable": {
                    "urls": [{
                        "url": f"http://{mock_vpn_server.host}:{mock_vpn_server.port}/test_source",
                        "weight": 1.0,
                        "protocols": ["vmess"],
                    }]
                }
        },
        "output": {
            "formats": ["json", "raw"]
        }
    }
    config_path = tmp_path / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    output_dir = tmp_path / "output"

    # 2. Patch the SecurityManager to avoid external network calls for validation
    with patch("streamline_vpn.core.merger.SecurityManager", autospec=True) as MockSecurityManager:
        mock_security_instance = MockSecurityManager.return_value
        mock_security_instance.validate_source.return_value = {"is_safe": True, "is_valid_url": True}
        mock_security_instance.analyze_configuration.return_value = {"is_safe": True}

        # 3. Initialize the merger and run the full processing pipeline
        merger = StreamlineVPNMerger(config_path=str(config_path))
        result = await merger.process_all(output_dir=str(output_dir))

    # 4. Assert the results
    assert result["success"] is True
    assert result["total_sources"] == 1
    assert result["total_configurations"] == 1
    assert result["warnings"] == [] # Should be no warnings in this ideal case

    # 5. Check that output files were created correctly
    output_files = list(output_dir.iterdir())
    assert len(output_files) == 2  # json and raw

    names = {f.name for f in output_files}
    assert "configurations.json" in names
    assert "configurations.txt" in names # RawFormatter adds .txt
