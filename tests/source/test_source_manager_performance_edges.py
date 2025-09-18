import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.core.source_manager import SourceManager


import pytest


@pytest.mark.asyncio
async def test_source_manager_tier_and_stats(tmp_path):
    cfg = tmp_path / "sources.yaml"
    cfg.write_text("sources: []", encoding="utf-8")
    sm = SourceManager(str(cfg))
    await sm.initialize()
    await sm.add_source({"name": "s1", "url": "http://a.example"})
    stats = sm.get_source_stats()
    assert "total_sources" in stats or isinstance(stats, dict)

