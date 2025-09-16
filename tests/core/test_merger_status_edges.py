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


def test_merger_status_contains_expected_keys(tmp_path):
    cfg = tmp_path / "sources.yaml"
    cfg.write_text("sources: []", encoding="utf-8")
    merger = StreamlineVPNMerger(config_path=str(cfg))
    _run(merger.initialize())
    status = merger.get_status()
    assert isinstance(status, dict)
    # Assert commonly present keys without depending on optional ones
    assert "initialized" in status
    assert "config_count" in status or "formats_generated" in status
    assert isinstance(status.get("initialized"), bool)


