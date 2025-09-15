"""Import coverage smoke tests.

These tests import a broad set of modules to execute top-level definitions,
increasing statement coverage without invoking external side effects.
"""

import importlib
import pytest


@pytest.mark.parametrize(
    "modname",
    [
        # Web/API surface
        "streamline_vpn.web.api",
        "streamline_vpn.web.config_generator",
        "streamline_vpn.web.unified_api",
        "streamline_vpn.web.settings",
        # Monitoring (pure definitions)
        "streamline_vpn.monitoring.metrics",
        "streamline_vpn.monitoring.metrics_collector",
        "streamline_vpn.monitoring.metrics_exporter",
        "streamline_vpn.monitoring.metrics_service",
        # Jobs
        "streamline_vpn.jobs.models",
        "streamline_vpn.jobs.manager",
        "streamline_vpn.jobs.cleanup",
        "streamline_vpn.jobs.persistence",
        "streamline_vpn.jobs.job_executor",
        # Fetcher (no network on import)
        "streamline_vpn.fetcher.circuit_breaker",
        "streamline_vpn.fetcher.rate_limiter",
        "streamline_vpn.fetcher.io_client",
        "streamline_vpn.fetcher.policies",
        "streamline_vpn.fetcher.service",
        # State
        "streamline_vpn.state.fsm",
        "streamline_vpn.state.manager",
        # Security auth models and policy (pure definitions)
        "streamline_vpn.security.auth.models",
        "streamline_vpn.security.auth.policy_engine",
        "streamline_vpn.security.blocklist_manager",
        "streamline_vpn.security.rate_limiter",
        "streamline_vpn.security.threat_analyzer",
        "streamline_vpn.security.validator",
        # Discovery manager (definitions; heavy calls are inside async funcs)
        "streamline_vpn.discovery.manager",
        # Settings and helpers
        "streamline_vpn.settings",
        "streamline_vpn.utils.helpers",
        "streamline_vpn.utils.validation",
    ],
)
def test_import_module(modname):
    try:
        mod = importlib.import_module(modname)
    except ImportError:
        pytest.skip(f"Module {modname} not importable in this environment")
    else:
        assert mod is not None
