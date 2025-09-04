"""
Dependencies Utility
==================

Handles dependency checking and validation for the VPN Merger application.
"""

import sys


def check_dependencies() -> bool:
    """Check if required dependencies are available.

    Returns:
        True if all required dependencies are available, False otherwise
    """
    missing = []

    try:
        import aiohttp
    except ImportError:
        missing.append("aiohttp")

    try:
        import nest_asyncio
    except ImportError:
        missing.append("nest_asyncio")

    try:
        import aiodns
    except ImportError:
        missing.append("aiodns")

    if missing:
        print(f"Missing required dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False

    return True


def get_optional_dependencies() -> list[str]:
    """Get list of optional dependencies that enhance functionality.

    Returns:
        List of available optional dependency names
    """
    optional = []

    try:
        import yaml

        optional.append("PyYAML")
    except ImportError:
        pass

    try:
        import tqdm

        optional.append("tqdm")
    except ImportError:
        pass

    try:
        import aiofiles

        optional.append("aiofiles")
    except ImportError:
        pass

    return optional


def get_missing_optional_dependencies() -> list[str]:
    """Get list of missing optional dependencies.

    Returns:
        List of missing optional dependency names
    """
    all_optional = ["PyYAML", "tqdm", "aiofiles"]
    available = get_optional_dependencies()
    return [dep for dep in all_optional if dep not in available]


def check_python_version() -> bool:
    """Check if Python version meets requirements.

    Returns:
        True if Python version is 3.10+, False otherwise
    """
    if sys.version_info < (3, 10):
        print(f"Python 3.10+ required, got {sys.version}")
        return False
    return True


def get_python_version_info() -> tuple[int, int, int]:
    """Get current Python version information.

    Returns:
        Tuple of (major, minor, micro) version numbers
    """
    return sys.version_info[:3]


def validate_environment() -> bool:
    """Validate the complete environment for running the merger.

    Returns:
        True if environment is valid, False otherwise
    """
    print("Validating environment...")

    # Check Python version
    if not check_python_version():
        return False

    # Check required dependencies
    if not check_dependencies():
        return False

    # Check optional dependencies
    optional_deps = get_optional_dependencies()
    if optional_deps:
        print(f"Optional dependencies available: {', '.join(optional_deps)}")

    missing_optional = get_missing_optional_dependencies()
    if missing_optional:
        print(f"Missing optional dependencies: {', '.join(missing_optional)}")
        print("Install with: pip install " + " ".join(missing_optional))

    print("Environment validation passed")
    return True


def get_dependency_summary() -> dict[str, bool | list[str]]:
    """Get comprehensive dependency status summary.

    Returns:
        Dictionary containing dependency status information
    """
    return {
        "python_version": get_python_version_info(),
        "python_version_ok": check_python_version(),
        "required_deps_ok": check_dependencies(),
        "available_optional": get_optional_dependencies(),
        "missing_optional": get_missing_optional_dependencies(),
        "environment_ready": validate_environment(),
    }


def print_dependency_report() -> None:
    """Print a formatted dependency status report."""
    summary = get_dependency_summary()

    print("VPN Merger - Dependency Report")
    print("=" * 40)
    print(f"Python Version: {'.'.join(map(str, summary['python_version']))}")
    print(f"Python Version OK: {'✅' if summary['python_version_ok'] else '❌'}")
    print(f"Required Dependencies: {'✅' if summary['required_deps_ok'] else '❌'}")

    if summary["available_optional"]:
        print(f"Optional Dependencies: ✅ {', '.join(summary['available_optional'])}")

    if summary["missing_optional"]:
        print(f"Missing Optional: ⚠️  {', '.join(summary['missing_optional'])}")

    print(f"Environment Ready: {'✅' if summary['environment_ready'] else '❌'}")
    print("=" * 40)


# Override with ASCII-clean version for consistent output in all terminals
def _print_dependency_report_ascii(summary: dict) -> None:
    print("VPN Merger - Dependency Report")
    print("=" * 40)
    print(f"Python Version: {'.'.join(map(str, summary['python_version']))}")
    print(f"Python Version OK: {'YES' if summary['python_version_ok'] else 'NO'}")
    print(f"Required Dependencies: {'YES' if summary['required_deps_ok'] else 'NO'}")
    if summary.get('available_optional'):
        print(f"Optional Dependencies: {', '.join(summary['available_optional'])}")
    if summary.get('missing_optional'):
        print(f"Missing Optional: {', '.join(summary['missing_optional'])}")
    print(f"Environment Ready: {'YES' if summary['environment_ready'] else 'NO'}")
    print("=" * 40)


def print_dependency_report() -> None:  # type: ignore[no-redef]
    """ASCII-only dependency status report (overrides earlier definition)."""
    _print_dependency_report_ascii(get_dependency_summary())
