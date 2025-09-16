import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.security.manager import SecurityManager


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def test_security_manager_validate_request_sync():
    mgr = SecurityManager()
    res = mgr.validate_request({"path": "/api"})
    if hasattr(res, "__await__"):
        res = _run(res)
    assert isinstance(res, dict) or res is True


