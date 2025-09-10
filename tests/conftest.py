import asyncio
import logging
import platform
import pytest


@pytest.fixture(scope="session", autouse=True)
def _cleanup_aiohttp_sessions_on_session_end():
    """Best-effort cleanup for any aiohttp sessions created in tests.

    Some tests may construct services without awaiting their explicit shutdown.
    This fixture closes any tracked sessions at the end of the session to avoid
    resource warnings from aiohttp about unclosed sessions/connectors.
    """
    yield
    try:
        from streamline_vpn.fetcher.io_client import get_tracked_sessions

        sessions = [s for s in get_tracked_sessions() if not s.closed]
        if not sessions:
            return

        async def _close_all():
            for s in sessions:
                try:
                    await s.close()
                except Exception:
                    pass

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            for s in sessions:
                try:
                    loop.create_task(s.close())
                except Exception:
                    pass
        else:
            try:
                asyncio.run(_close_all())
            except Exception:
                pass
    except Exception:
        # If anything goes wrong, avoid failing the test run at teardown
        pass


@pytest.fixture(scope="session", autouse=True)
def _win_event_loop_policy_and_silence_asyncio():
    """On Windows, use selector loop to avoid Proactor SSL errors and silence asyncio logger.

    This reduces noisy "Fatal error on SSL transport" messages that can occur when
    background transports are torn down quickly during test teardown.
    """
    if platform.system().lower().startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass
    # Run tests
    yield
    try:
        logging.getLogger("asyncio").setLevel(logging.CRITICAL)
    except Exception:
        pass
