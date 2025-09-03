"""
Pytest Configuration for VPN Merger Tests
========================================

This module provides pytest configuration, fixtures, and test environment setup
for the VPN Merger application.
"""

import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

# Ensure project root is on sys.path for package imports during CI
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Add the vpn_merger package to the path
VPN_MERGER_PATH = os.path.join(ROOT, "vpn_merger")
if VPN_MERGER_PATH not in sys.path:
    sys.path.insert(0, VPN_MERGER_PATH)


def pytest_collection_modifyitems(config: pytest.Config, items: list) -> None:
    """Skip network-marked tests in CI environments, or when SKIP_NETWORK is set.

    Args:
        config: Pytest configuration object
        items: List of test items to potentially modify
    """
    skip_network = False
    if os.environ.get("CI") or os.environ.get("SKIP_NETWORK"):
        skip_network = True

    if skip_network:
        marker = pytest.mark.skip(reason="Skipping network tests in CI")
        for item in items:
            if "network" in item.keywords:
                item.add_marker(marker)


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Provide test data directory path.

    Returns:
        Path to the test data directory
    """
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def temp_output_dir(tmp_path_factory) -> Path:
    """Provide temporary output directory for tests.

    Args:
        tmp_path_factory: Pytest's temporary path factory

    Returns:
        Path to a temporary output directory
    """
    return tmp_path_factory.mktemp("test_output")


@pytest.fixture(autouse=True)
def setup_test_environment() -> Generator[None, None, None]:
    """Setup test environment variables.

    This fixture automatically runs for all tests to ensure
    proper test environment configuration.

    Yields:
        None

    Note:
        Environment variables are automatically cleaned up after each test
    """
    # Set test-specific environment variables
    os.environ.setdefault("VPN_MERGER_TEST_MODE", "true")
    os.environ.setdefault("SKIP_NETWORK", "true")

    yield

    # Cleanup
    if "VPN_MERGER_TEST_MODE" in os.environ:
        del os.environ["VPN_MERGER_TEST_MODE"]


@pytest.fixture(scope="session")
def test_config() -> dict:
    """Provide test configuration data.

    Returns:
        Dictionary containing test configuration
    """
    return {"test_mode": True, "skip_network": True, "max_concurrent": 5, "timeout": 10}


@pytest.fixture(scope="function")
def clean_environment() -> Generator[None, None, None]:
    """Provide a clean environment for individual tests.

    This fixture ensures that each test starts with a clean
    environment by temporarily clearing certain environment variables.

    Yields:
        None
    """
    # Store original values
    original_vars = {}
    for key in ["VPN_MERGER_TEST_MODE", "SKIP_NETWORK", "VPN_CONCURRENT_LIMIT"]:
        if key in os.environ:
            original_vars[key] = os.environ[key]

    # Set test defaults
    os.environ["VPN_MERGER_TEST_MODE"] = "true"
    os.environ["SKIP_NETWORK"] = "true"

    yield

    # Restore original values
    for key, value in original_vars.items():
        os.environ[key] = value
    for key in ["VPN_MERGER_TEST_MODE", "SKIP_NETWORK"]:
        if key not in original_vars and key in os.environ:
            del os.environ[key]
