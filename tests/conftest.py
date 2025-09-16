# Test configuration for StreamlineVPN
import pytest

@pytest.fixture
def mock_merger():
    class MockMerger:
        async def initialize(self): pass
        async def shutdown(self): pass
    return MockMerger()
