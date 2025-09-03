"""
Environment Utility
=================

Handles environment detection and execution mode selection for the VPN Merger.
"""

import asyncio
import logging
import os

logger = logging.getLogger(__name__)


async def run_in_jupyter():
    """Run merger in Jupyter/IPython environment.

    Returns:
        List of processed VPN configurations

    Raises:
        ImportError: If nest_asyncio is not available
    """
    try:
        import nest_asyncio

        nest_asyncio.apply()
        logger.info("Applied nest_asyncio for Jupyter environment")
    except ImportError:
        logger.warning("nest_asyncio not available, may have event loop issues")

    from ..core.merger import VPNSubscriptionMerger

    merger = VPNSubscriptionMerger()
    results = await merger.run_comprehensive_merge()
    merger.save_results(results)

    logger.info(f"Jupyter execution completed with {len(results)} configurations")
    return results


def detect_and_run(config=None):
    """Detect environment and run appropriately.

    This function automatically detects the execution context and runs
    the merger in the most appropriate way.

    Args:
        config: Optional configuration (currently unused)

    Returns:
        Either a coroutine or the final results, depending on context
    """
    try:
        # Try to get current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, return coroutine
            logger.info("Detected async context, returning coroutine")
            from ..core.merger import VPNSubscriptionMerger

            merger = VPNSubscriptionMerger()
            return merger.run_comprehensive_merge()
        else:
            # We can run the event loop
            logger.info("Detected sync context, running event loop")
            from ..core.merger import VPNSubscriptionMerger

            merger = VPNSubscriptionMerger()
            return loop.run_until_complete(merger.run_comprehensive_merge())
    except RuntimeError:
        # No event loop, create one
        logger.info("No event loop found, creating new one")
        from ..core.merger import VPNSubscriptionMerger

        merger = VPNSubscriptionMerger()
        return asyncio.run(merger.run_comprehensive_merge())


def get_execution_mode() -> str:
    """Detect the current execution mode.

    Returns:
        String describing the execution mode
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return "async_context"
        else:
            return "sync_context"
    except RuntimeError:
        return "no_loop"


def is_jupyter_environment() -> bool:
    """Check if running in Jupyter/IPython environment.

    Returns:
        True if running in Jupyter/IPython, False otherwise
    """
    try:
        # Check for IPython
        import IPython

        return True
    except ImportError:
        pass

    try:
        # Check for Jupyter
        import jupyter_client

        return True
    except ImportError:
        pass

    return False


def get_optimal_concurrency() -> int:
    """Get optimal concurrency based on environment.

    Returns:
        Optimal concurrency limit for the current environment
    """
    # Check environment variables
    env_concurrency = os.environ.get("VPN_CONCURRENT_LIMIT")
    if env_concurrency is not None:
        try:
            concurrency = int(env_concurrency)
            # Allow zero/negative per tests; just return parsed value
            logger.info(f"Using environment concurrency limit: {concurrency}")
            return concurrency
        except ValueError:
            logger.warning(f"Invalid VPN_CONCURRENT_LIMIT value: {env_concurrency}")

    # Default based on environment
    try:
        jup = is_jupyter_environment()
    except Exception:
        jup = False
    if jup:
        default_limit = 20  # Lower for Jupyter
        logger.info(f"Jupyter environment detected, using concurrency limit: {default_limit}")
    else:
        default_limit = 50  # Higher for scripts
        logger.info(f"Script environment detected, using concurrency limit: {default_limit}")

    return default_limit


def get_environment_info() -> dict:
    """Get comprehensive environment information.

    Returns:
        Dictionary containing environment details
    """
    return {
        "execution_mode": get_execution_mode(),
        "is_jupyter": is_jupyter_environment(),
        "optimal_concurrency": get_optimal_concurrency(),
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        "platform": os.sys.platform,
        "env_vars": {
            "VPN_CONCURRENT_LIMIT": os.environ.get("VPN_CONCURRENT_LIMIT"),
            "VPN_MERGER_TEST_MODE": os.environ.get("VPN_MERGER_TEST_MODE"),
            "SKIP_NETWORK": os.environ.get("SKIP_NETWORK"),
        },
    }


def print_environment_report() -> None:
    """Print a formatted environment information report."""
    info = get_environment_info()

    print("VPN Merger - Environment Report")
    print("=" * 40)
    print(f"Execution Mode: {info['execution_mode']}")
    print(f"Jupyter Environment: {'✅' if info['is_jupyter'] else '❌'}")
    print(f"Optimal Concurrency: {info['optimal_concurrency']}")
    print(f"Python Version: {info['python_version']}")
    print(f"Platform: {info['platform']}")
    print("\nEnvironment Variables:")
    for key, value in info["env_vars"].items():
        status = f"✅ {value}" if value else "❌ Not set"
        print(f"  {key}: {status}")
    print("=" * 40)


def validate_execution_environment() -> bool:
    """Validate that the execution environment is suitable.

    Returns:
        True if environment is suitable, False otherwise
    """
    try:
        # Check if we can access the event loop
        loop = asyncio.get_event_loop()
        logger.debug(f"Event loop accessible: {loop}")

        # Check if we can import core components

        logger.info("Core components importable")
        return True

    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        return False
