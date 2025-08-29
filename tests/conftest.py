import os
import sys
import pytest

# Ensure project root is on sys.path for package imports during CI
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def pytest_collection_modifyitems(config, items):
    """Skip network-marked tests in CI environments, or when SKIP_NETWORK is set."""
    skip_network = False
    if os.environ.get("CI") or os.environ.get("SKIP_NETWORK"):
        skip_network = True
    if skip_network:
        marker = pytest.mark.skip(reason="Skipping network tests in CI")
        for item in items:
            if "network" in item.keywords:
                item.add_marker(marker)
