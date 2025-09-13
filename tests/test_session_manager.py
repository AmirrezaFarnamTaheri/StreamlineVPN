import asyncio

import pytest

from streamline_vpn.fetcher.io_client import _SESSION_MANAGER, make_session


@pytest.mark.asyncio
async def test_session_manager_reuses_default_session():
    s1 = await _SESSION_MANAGER.get_session("default")
    s2 = await _SESSION_MANAGER.get_session("default")
    assert s1 is s2
    await _SESSION_MANAGER.close_all()


def test_make_session_returns_live_session():
    session = make_session(50, 30)
    assert not session.closed
    asyncio.run(_SESSION_MANAGER.close_all())
