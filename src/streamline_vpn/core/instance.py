import asyncio
import aiohttp
from contextlib import asynccontextmanager
from typing import Optional

from .merger import StreamlineVPNMerger

_merger_instance: Optional[StreamlineVPNMerger] = None
_session: Optional[aiohttp.ClientSession] = None

_merger_instance: Optional[StreamlineVPNMerger] = None
_session: Optional[aiohttp.ClientSession] = None
_merger_refcount: int = 0

@asynccontextmanager
async def get_merger() -> StreamlineVPNMerger:
    """
    Provides a singleton instance of StreamlineVPNMerger with a managed aiohttp session.
    Ensures safe sharing across concurrent contexts.
    """
    global _merger_instance, _session, _merger_refcount
    if _merger_instance is None:
        if _session is None or _session.closed:
            _session = aiohttp.ClientSession()
        _merger_instance = StreamlineVPNMerger(session=_session)
        await _merger_instance.initialize()
    _merger_refcount += 1
    try:
        yield _merger_instance
    finally:
        _merger_refcount -= 1
        if _merger_refcount <= 0:
            if _merger_instance is not None:
                await _merger_instance.shutdown()
                _merger_instance = None
            if _session is not None and not _session.closed:
                await _session.close()
                _session = None

async def get_merger_instance() -> StreamlineVPNMerger:
    """
    A simplified way to get the merger instance without a context manager.
    Note: This does not manage the lifecycle of the merger instance.
    """
    global _merger_instance, _session
    if _merger_instance is None:
        if _session is None or _session.closed:
            _session = aiohttp.ClientSession()

        _merger_instance = StreamlineVPNMerger(session=_session)
        await _merger_instance.initialize()

    return _merger_instance