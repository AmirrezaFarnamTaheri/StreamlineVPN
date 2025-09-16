import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.security.manager import SecurityManager


def test_security_manager_validate_configuration_sync_path():
    mgr = SecurityManager()
    res = mgr.validate_configuration({"protocol": "vmess"})
    # May return dict or coroutine depending on unwrap; normalize
    if hasattr(res, "__await__"):
        import asyncio
        res = asyncio.get_event_loop().run_until_complete(res)
    assert isinstance(res, dict) or res is True


