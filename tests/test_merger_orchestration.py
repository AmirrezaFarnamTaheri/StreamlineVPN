from unittest.mock import AsyncMock

import pytest

from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.models.configuration import VPNConfiguration, Protocol


def cfg(host: str) -> VPNConfiguration:
    return VPNConfiguration(protocol=Protocol.VMESS, server=host, port=443, user_id="u")


@pytest.mark.asyncio
async def test_merger_process_all_with_mocks(tmp_path):
    m = StreamlineVPNMerger(config_path=str(tmp_path / "sources.yaml"))

    # Patch source manager to return active sources
    m.source_manager.get_active_sources = AsyncMock(return_value=[
        "https://s1.example.com", "https://s2.example.com"
    ])
    # Patch processor to return configs and pass through dedup/enhance
    m.processor.process_sources = AsyncMock(return_value=[cfg("a"), cfg("b"), cfg("a")])
    m.processor.deduplicate_configurations = AsyncMock(side_effect=lambda items: [items[0], items[1]])
    m.processor.apply_enhancements = AsyncMock(side_effect=lambda items: items)
    # Avoid file IO in output manager
    m.output_manager.save_configurations = AsyncMock(return_value=None)

    result = await m.process_all(output_dir=str(tmp_path / "out"), formats=["json"]) 
    assert result["success"] is True
    assert result["sources_processed"] == 2
    assert result["configurations_found"] == 2
    # get_configurations returns the enhanced configs
    configs = await m.get_configurations()
    assert len(configs) == 2

