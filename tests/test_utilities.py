"""
Test Utilities
=============

Focused tests for utility functions.
"""

from unittest.mock import Mock, patch

from vpn_merger.utils.dependencies import (
    check_dependencies,
    check_python_version,
    get_optional_dependencies,
    validate_environment,
)
from vpn_merger.utils.environment import (
    get_execution_mode,
    get_optimal_concurrency,
    is_jupyter_environment,
)


class TestDependencies:
    """Test dependency checking utilities."""

    def test_check_dependencies_success(self):
        """Test successful dependency check."""
        with patch.dict(
            "sys.modules", {"aiohttp": Mock(), "nest_asyncio": Mock(), "aiodns": Mock()}
        ):
            result = check_dependencies()
            assert result is True

    def test_check_dependencies_missing(self):
        """Test dependency check with missing dependencies."""
        with patch.dict("sys.modules", {"aiohttp": Mock(), "nest_asyncio": None, "aiodns": Mock()}):
            result = check_dependencies()
            assert result is False

    def test_get_optional_dependencies(self):
        """Test optional dependency detection."""
        with patch.dict("sys.modules", {"yaml": Mock(), "tqdm": Mock(), "aiofiles": Mock()}):
            optional = get_optional_dependencies()
            assert "PyYAML" in optional
            assert "tqdm" in optional
            assert "aiofiles" in optional

    def test_get_optional_dependencies_missing(self):
        """Test optional dependency detection with missing modules."""
        with patch.dict("sys.modules", {"yaml": None, "tqdm": None, "aiofiles": None}):
            optional = get_optional_dependencies()
            assert len(optional) == 0

    def test_check_python_version_success(self):
        """Test Python version check with valid version."""
        with patch("sys.version_info", (3, 10, 0)):
            result = check_python_version()
            assert result is True

    def test_check_python_version_too_old(self):
        """Test Python version check with old version."""
        with patch("sys.version_info", (3, 9, 0)):
            result = check_python_version()
            assert result is False

    def test_validate_environment_success(self):
        """Test environment validation with all checks passing."""
        with (
            patch("vpn_merger.utils.dependencies.check_python_version", return_value=True),
            patch("vpn_merger.utils.dependencies.check_dependencies", return_value=True),
        ):
            result = validate_environment()
            assert result is True

    def test_validate_environment_python_fail(self):
        """Test environment validation with Python version check failing."""
        with patch("vpn_merger.utils.dependencies.check_python_version", return_value=False):
            result = validate_environment()
            assert result is False

    def test_validate_environment_dependencies_fail(self):
        """Test environment validation with dependency check failing."""
        with (
            patch("vpn_merger.utils.dependencies.check_python_version", return_value=True),
            patch("vpn_merger.utils.dependencies.check_dependencies", return_value=False),
        ):
            result = validate_environment()
            assert result is False


class TestEnvironment:
    """Test environment detection utilities."""

    def test_get_execution_mode_no_loop(self):
        """Test execution mode detection with no event loop."""
        with patch("asyncio.get_event_loop", side_effect=RuntimeError("No event loop")):
            mode = get_execution_mode()
            assert mode == "no_loop"

    def test_get_execution_mode_sync_context(self):
        """Test execution mode detection in sync context."""
        mock_loop = Mock()
        mock_loop.is_running.return_value = False

        with patch("asyncio.get_event_loop", return_value=mock_loop):
            mode = get_execution_mode()
            assert mode == "sync_context"

    def test_get_execution_mode_async_context(self):
        """Test execution mode detection in async context."""
        mock_loop = Mock()
        mock_loop.is_running.return_value = True

        with patch("asyncio.get_event_loop", return_value=mock_loop):
            mode = get_execution_mode()
            assert mode == "async_context"

    def test_is_jupyter_environment_true(self):
        """Test Jupyter environment detection when true."""
        with patch.dict("sys.modules", {"IPython": Mock()}):
            result = is_jupyter_environment()
            assert result is True

    def test_is_jupyter_environment_jupyter_client(self):
        """Test Jupyter environment detection with jupyter_client."""
        with patch.dict("sys.modules", {"IPython": None, "jupyter_client": Mock()}):
            result = is_jupyter_environment()
            assert result is True

    def test_is_jupyter_environment_false(self):
        """Test Jupyter environment detection when false."""
        with patch.dict("sys.modules", {"IPython": None, "jupyter_client": None}):
            result = is_jupyter_environment()
            assert result is False

    def test_get_optimal_concurrency_from_env(self):
        """Test getting optimal concurrency from environment variable."""
        with patch.dict("os.environ", {"VPN_CONCURRENT_LIMIT": "75"}):
            concurrency = get_optimal_concurrency()
            assert concurrency == 75

    def test_get_optimal_concurrency_invalid_env(self):
        """Test getting optimal concurrency with invalid environment variable."""
        with patch.dict("os.environ", {"VPN_CONCURRENT_LIMIT": "invalid"}):
            concurrency = get_optimal_concurrency()
            # Should fall back to default based on environment
            assert concurrency in [20, 50]

    def test_get_optimal_concurrency_jupyter(self):
        """Test getting optimal concurrency in Jupyter environment."""
        with (
            patch.dict("os.environ", {}),
            patch("vpn_merger.utils.environment.is_jupyter_environment", return_value=True),
        ):
            concurrency = get_optimal_concurrency()
            assert concurrency == 20

    def test_get_optimal_concurrency_script(self):
        """Test getting optimal concurrency in script environment."""
        with (
            patch.dict("os.environ", {}),
            patch("vpn_merger.utils.environment.is_jupyter_environment", return_value=False),
        ):
            concurrency = get_optimal_concurrency()
            assert concurrency == 50


class TestEnvironmentIntegration:
    """Test environment utilities integration."""

    def test_environment_detection_workflow(self):
        """Test complete environment detection workflow."""
        # Mock a Jupyter environment
        with patch.dict("sys.modules", {"IPython": Mock()}), patch.dict("os.environ", {}):
            # Check environment type
            is_jupyter = is_jupyter_environment()
            assert is_jupyter is True

            # Get optimal concurrency
            concurrency = get_optimal_concurrency()
            assert concurrency == 20

    def test_environment_detection_script_workflow(self):
        """Test environment detection workflow for script execution."""
        # Mock a script environment
        with (
            patch.dict("sys.modules", {"IPython": None, "jupyter_client": None}),
            patch.dict("os.environ", {}),
        ):
            # Check environment type
            is_jupyter = is_jupyter_environment()
            assert is_jupyter is False

            # Get optimal concurrency
            concurrency = get_optimal_concurrency()
            assert concurrency == 50

    def test_environment_detection_with_custom_concurrency(self):
        """Test environment detection with custom concurrency setting."""
        # Mock environment with custom concurrency
        with patch.dict("os.environ", {"VPN_CONCURRENT_LIMIT": "100"}):
            concurrency = get_optimal_concurrency()
            assert concurrency == 100

    def test_error_handling_in_environment_detection(self):
        """Test error handling in environment detection."""
        # Mock environment detection to raise exception
        with patch(
            "vpn_merger.utils.environment.is_jupyter_environment",
            side_effect=Exception("Detection failed"),
        ):
            # Should handle gracefully and return default
            concurrency = get_optimal_concurrency()
            assert concurrency in [20, 50]  # Should have a fallback value


class TestUtilityEdgeCases:
    """Test utility function edge cases."""

    def test_dependency_check_with_import_error(self):
        """Test dependency check with import error."""
        with patch("builtins.__import__", side_effect=ImportError("Module not found")):
            result = check_dependencies()
            assert result is False

    def test_python_version_check_edge_cases(self):
        """Test Python version check edge cases."""
        # Test exact boundary
        with patch("sys.version_info", (3, 10, 0)):
            result = check_python_version()
            assert result is True

        # Test boundary - 1
        with patch("sys.version_info", (3, 9, 9)):
            result = check_python_version()
            assert result is False

        # Test boundary + 1
        with patch("sys.version_info", (3, 10, 1)):
            result = check_python_version()
            assert result is True

    def test_environment_variable_edge_cases(self):
        """Test environment variable edge cases."""
        # Test empty string
        with patch.dict("os.environ", {"VPN_CONCURRENT_LIMIT": ""}):
            concurrency = get_optimal_concurrency()
            assert concurrency in [20, 50]  # Should fall back to default

        # Test very large number
        with patch.dict("os.environ", {"VPN_CONCURRENT_LIMIT": "999999"}):
            concurrency = get_optimal_concurrency()
            assert concurrency == 999999

        # Test zero
        with patch.dict("os.environ", {"VPN_CONCURRENT_LIMIT": "0"}):
            concurrency = get_optimal_concurrency()
            assert concurrency == 0

        # Test negative number
        with patch.dict("os.environ", {"VPN_CONCURRENT_LIMIT": "-10"}):
            concurrency = get_optimal_concurrency()
            assert concurrency == -10  # Should allow negative values

    def test_module_import_edge_cases(self):
        """Test module import edge cases."""
        # Test with None modules
        with patch.dict("sys.modules", {"aiohttp": None, "nest_asyncio": None, "aiodns": None}):
            result = check_dependencies()
            assert result is False

        # Test with mock modules that have no attributes
        mock_module = Mock()
        del mock_module.__spec__  # Remove spec to simulate incomplete module

        with patch.dict(
            "sys.modules",
            {"aiohttp": mock_module, "nest_asyncio": mock_module, "aiodns": mock_module},
        ):
            result = check_dependencies()
            assert result is True  # Should still pass with mock modules
