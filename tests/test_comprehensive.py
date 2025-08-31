import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_full_processing_pipeline(tmp_path: Path):
    """Test basic functionality of the VPN merger components."""
    
    # Import the module
    import importlib.util, sys
    root = Path(__file__).resolve().parents[1] / "vpn_merger.py"
    spec = importlib.util.spec_from_file_location("vpn_merger_app", str(root))
    vm = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(vm)

    # Test basic initialization
    merger = vm.VPNSubscriptionMerger()
    assert merger is not None
    assert hasattr(merger, 'source_manager')
    assert hasattr(merger, 'config_processor')
    
    # Test source manager
    source_manager = merger.source_manager
    assert source_manager is not None
    sources = source_manager.get_all_sources()
    assert isinstance(sources, list)
    
    # Test configuration processor
    config_processor = merger.config_processor
    assert config_processor is not None
    
    # Test processing a simple config
    test_config = "vmess://eyJhZGQiOiAidGVzdC5leGFtcGxlLmNvbSIsICJwb3J0IjogNDQzfQ=="
    result = config_processor.process_config(test_config)
    assert result is not None
    assert result.protocol == "vmess"
    assert 0 <= result.quality_score <= 1
    
    # Test that the merger can be initialized and has the expected structure
    assert hasattr(merger, 'stats')
    assert 'total_sources' in merger.stats
    assert 'processed_sources' in merger.stats
    assert 'valid_configs' in merger.stats
