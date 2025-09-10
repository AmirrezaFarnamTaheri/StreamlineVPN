from unittest.mock import Mock

import pytest

from streamline_vpn.core.source_manager import SourceManager
from streamline_vpn.models.source import SourceTier


def make_security_ok():
    sec = Mock()
    sec.validate_source = Mock(return_value={
        "is_valid_url": True,
        "is_blocked": False,
        "is_rate_limited": False,
        "domain_analysis": {"is_safe": True},
        "is_safe": True,
    })
    return sec


def test_source_manager_load_add_and_stats(tmp_path):
    # Copy fixture to temp
    cfg_path = tmp_path / "sources.yaml"
    from pathlib import Path
    fixture = Path("tests/fixtures/test_sources.yaml").resolve()
    cfg_path.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")

    sm = SourceManager(str(cfg_path), security_manager=make_security_ok(), fetcher_service=None)

    # Should load some sources
    assert len(sm.sources) >= 1

    # Add a new source
    import asyncio
    url = "https://new.example.com/list.txt"
    asyncio.run(sm.add_source(url, tier=SourceTier.RELIABLE))
    assert url in sm.sources

    # Duplicate add should raise
    with pytest.raises(ValueError):
        asyncio.run(sm.add_source(url, tier=SourceTier.RELIABLE))

    # Update performance and compute statistics (async API)
    asyncio.run(sm.update_source_performance(url, success=True, config_count=50, response_time=1.0))
    stats = sm.get_source_statistics()
    assert stats["total_sources"] >= 1
    assert "tier_distribution" in stats

    # Blacklist / whitelist
    sm.blacklist_source(url, reason="test")
    assert sm.sources[url].is_blacklisted is True
    sm.whitelist_source(url)
    assert sm.sources[url].is_blacklisted is False
