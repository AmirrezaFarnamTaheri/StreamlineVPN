"""
Pytest configuration and fixtures for StreamlineVPN tests.
Includes proper async mock handling and test utilities.
"""

import asyncio
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator
import tempfile
import logging

# Add src to path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from streamline_vpn.models.configuration import VPNConfiguration, Protocol
from streamline_vpn.models.source import SourceMetadata, SourceTier


# Configure logging for tests
logging.getLogger("streamline_vpn").setLevel(logging.DEBUG)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    if sys.platform == "win32":
        # Use ProactorEventLoop on Windows to avoid SSL teardown warnings
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_configurations():
    """Sample VPN configurations for testing."""
    return [
        VPNConfiguration(
            protocol=Protocol.VMESS,
            server="example1.com",
            port=443,
            uuid="550e8400-e29b-41d4-a716-446655440000",
            alterId=0,
            security="auto",
            network="ws",
            path="/",
            host="example1.com"
        ),
        VPNConfiguration(
            protocol=Protocol.VLESS,
            server="example2.com",
            port=443,
            uuid="550e8400-e29b-41d4-a716-446655440001",
            security="tls",
            network="grpc",
            serviceName="grpc",
            host="example2.com"
        ),
        VPNConfiguration(
            protocol=Protocol.TROJAN,
            server="example3.com",
            port=443,
            password="password123",
            sni="example3.com",
            security="tls"
        ),
        VPNConfiguration(
            protocol=Protocol.SHADOWSOCKS,
            server="example4.com",
            port=8388,
            method="chacha20-ietf-poly1305",
            password="password123"
        )
    ]


@pytest.fixture
def sample_sources():
    """Sample source metadata for testing."""
    return [
        SourceMetadata(
            url="https://example1.com/configs",
            tier=SourceTier.PREMIUM,
            weight=1.0,
            protocols=["vmess", "vless"]
        ),
        SourceMetadata(
            url="https://example2.com/configs", 
            tier=SourceTier.STANDARD,
            weight=0.8,
            protocols=["trojan", "shadowsocks"]
        ),
        SourceMetadata(
            url="https://example3.com/configs",
            tier=SourceTier.BACKUP,
            weight=0.5,
            protocols=["vmess"]
        )
    ]


class AsyncContextManagerMock:
    """Proper async context manager mock for aiohttp responses."""
    
    def __init__(self, mock_response):
        self.mock_response = mock_response
        
    async def __aenter__(self):
        return self.mock_response
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


class MockResponse:
    """Mock HTTP response for testing."""
    
    def __init__(self, status: int = 200, text: str = "", json_data: Optional[Dict] = None):
        self.status = status
        self._text = text
        self._json_data = json_data or {}
        
    async def text(self):
        return self._text
        
    async def json(self):
        return self._json_data
        
    def raise_for_status(self):
        if self.status >= 400:
            raise Exception(f"HTTP {self.status}")


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session with proper async context manager."""
    session_mock = AsyncMock()
    
    def create_response_mock(status=200, text="", json_data=None):
        response = MockResponse(status, text, json_data)
        return AsyncContextManagerMock(response)
    
    session_mock.get = MagicMock(side_effect=lambda *args, **kwargs: create_response_mock())
    session_mock.post = MagicMock(side_effect=lambda *args, **kwargs: create_response_mock())
    
    return session_mock


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.ping = AsyncMock(return_value=True)
    redis_mock.flushall = AsyncMock(return_value=True)
    return redis_mock


class MockStreamlineVPNMerger:
    """Mock merger for testing API endpoints."""
    
    def __init__(self, *args, **kwargs):
        self.source_manager = MagicMock()
        self.source_manager.sources = {}
        self.configurations = []
        self.statistics = {
            "total_configurations": 0,
            "active_sources": 0,
            "last_update": None,
            "processing_time": 0
        }
        
    async def initialize(self):
        pass
        
    async def shutdown(self):
        pass
        
    async def process_all(self, *args, **kwargs):
        return {"success": True, "processed": 0}
        
    async def get_statistics(self):
        return self.statistics
        
    def get_configurations(self):
        return self.configurations
        
    def add_configuration(self, config: VPNConfiguration):
        self.configurations.append(config)
        self.statistics["total_configurations"] += 1


@pytest.fixture
def mock_merger():
    """Mock merger instance for testing."""
    return MockStreamlineVPNMerger()


@pytest.fixture
def mock_fastapi_app():
    """Mock FastAPI application for testing."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    
    app = FastAPI()
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
        
    @app.get("/")
    async def root():
        return {"service": "StreamlineVPN API"}
        
    return TestClient(app)


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add integration marker to tests in integration directories
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
            
        # Add slow marker to tests that might be slow
        if "performance" in item.name or "load" in item.name:
            item.add_marker(pytest.mark.slow)


# Environment setup for tests
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables."""
    test_env = {
        "STREAMLINE_ENV": "testing",
        "STREAMLINE_LOG_LEVEL": "DEBUG",
        "CACHE_ENABLED": "false",
        "STREAMLINE_REDIS__NODES": "[]",
        "VPN_TIMEOUT": "30",
        "VPN_CONCURRENT_LIMIT": "5"
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)