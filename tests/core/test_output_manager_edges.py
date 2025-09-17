import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.core.output_manager import OutputManager


def _await(coro):
    import asyncio

    return asyncio.get_event_loop().run_until_complete(coro)


def test_output_manager_single_and_multiple(tmp_path):
    om = OutputManager()
    configs = [{"name": "c1"}]
    # single
    path = _await(
        om.save_configurations(configs, output_dir=str(tmp_path), formats="json")
    )
    assert isinstance(path, Path)
    assert path.exists() or path.name.endswith(".json")
    # multiple
    res = _await(
        om.save_configurations(
            configs, output_dir=str(tmp_path), formats=["json", "clash"]
        )
    )
    assert isinstance(res, dict)
    assert "json" in res and "clash" in res
