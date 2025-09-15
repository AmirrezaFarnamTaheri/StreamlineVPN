import asyncio
from pathlib import Path

import pytest

from streamline_vpn.core.output_manager import OutputManager
from streamline_vpn.models.configuration import VPNConfiguration, Protocol


def sample_config() -> VPNConfiguration:
    return VPNConfiguration(
        protocol=Protocol.VMESS,
        server="s.test-server.example",
        port=443,
        user_id="uuid",
        tls=True,
    )


@pytest.mark.asyncio
async def test_output_manager_all_formats(tmp_path: Path):
    mgr = OutputManager()
    cfgs = [sample_config()]
    result = await mgr.save_configurations(cfgs, str(tmp_path), formats=[
        "raw", "json", "csv", "base64", "clash", "singbox"
    ])
    # Should return mapping for all requested (optional ones may still map to paths)
    assert isinstance(result, dict)
    for f in ["raw", "json", "clash", "singbox"]:
        assert f in result
        assert isinstance(result[f], Path)


def test_output_manager_sync_wrapper(tmp_path: Path):
    mgr = OutputManager()
    cfgs = [sample_config()]
    out = mgr.save_configurations_sync(cfgs, str(tmp_path), formats="json")
    assert isinstance(out, Path)

    # Inside running loop should raise
    async def run_inside_loop():
        with pytest.raises(RuntimeError):
            mgr.save_configurations_sync(cfgs, str(tmp_path), formats="json")

    asyncio.run(run_inside_loop())

