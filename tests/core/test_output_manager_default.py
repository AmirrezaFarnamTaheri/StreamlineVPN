import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.core.output_manager import OutputManager


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def test_output_manager_defaults_return_true(tmp_path):
    om = OutputManager()
    # No formats passed -> defaults path should return True
    res = _run(om.save_configurations([{"name": "x"}], output_dir=str(tmp_path)))
    assert res is True


