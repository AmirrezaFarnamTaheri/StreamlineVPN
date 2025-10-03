import asyncio
import sys
from unittest.mock import MagicMock

import pytest

# On Windows, the default event loop policy can cause noisy SSL teardown
# errors. Using the WindowsSelectorEventLoopPolicy can resolve this.
# This check is crucial for cross-platform compatibility.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for each test session.
    This is a standard fixture for pytest-asyncio.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_merger():
    """A mock merger for testing purposes."""
    merger = MagicMock()
    merger.initialize = asyncio.coroutine(MagicMock())
    merger.shutdown = asyncio.coroutine(MagicMock())
    return merger