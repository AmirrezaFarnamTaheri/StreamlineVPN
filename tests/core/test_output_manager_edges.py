import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.core.output_manager import OutputManager


@pytest.mark.asyncio
async def test_output_manager_single_and_multiple(tmp_path):
    om = OutputManager()
    configs = [{"name": "c1"}]
    # single
    path = await om.save_configurations(
        configs, output_dir=str(tmp_path), formats="json"
    )
    assert isinstance(path, Path)
    assert path.exists() or path.name.endswith(".json")
    # multiple
    res = await om.save_configurations(
        configs, output_dir=str(tmp_path), formats=["json", "clash"]
    )
    assert isinstance(res, dict)
    assert "json" in res and "clash" in res
