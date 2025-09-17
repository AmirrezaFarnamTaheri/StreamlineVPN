import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.core.config_validator import ConfigurationValidator


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def test_config_validator_protocol_specific_minimal():
    v = ConfigurationValidator()
    _run(v.initialize())
    vmess = {
        "type": "vmess",
        "host": "example.com",
        "port": 443,
        "uuid": "123e4567-e89b-12d3-a456-426614174000",
    }
    res = v.validate_config(vmess)
    assert isinstance(res, dict)
    assert "is_valid" in res
