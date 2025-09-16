import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.core.merger import StreamlineVPNMerger


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def test_merger_health_check_minimal(tmp_path):
    cfg = tmp_path / "sources.yaml"
    cfg.write_text("sources: []", encoding="utf-8")
    merger = StreamlineVPNMerger(config_path=str(cfg))
    _run(merger.initialize())
    status = merger.health_check()
    assert isinstance(status, dict)
    assert "status" in status or "healthy" in str(status).lower()


