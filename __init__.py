"""
VPN Subscription Merger Package
==============================

A high-performance, production-ready VPN subscription merger that aggregates and 
processes VPN configurations from multiple sources with advanced filtering, 
validation, and output formatting.

Version: 2.0.0
Status: Production Ready
License: MIT
Author: VPN Merger Team
"""

__version__ = "2.0.0"
__author__ = "VPN Merger Team"
__status__ = "Production Ready"
__license__ = "MIT"

# Import the main classes directly from the vpn_merger module
try:
    from vpn_merger import (
        VPNSubscriptionMerger, 
        SourceManager, 
        ConfigurationProcessor, 
        UnifiedSourceValidator,
        VPNConfiguration,
        check_dependencies,
        detect_and_run,
        run_in_jupyter
    )
except ImportError as e:
    # Fallback for when running as a script or when package is not properly installed
    import warnings
    warnings.warn(
        f"Failed to import vpn_merger components: {e}. "
        "This may happen when running as a script or when the package is not properly installed.",
        ImportWarning,
        stacklevel=2
    )
    
    VPNSubscriptionMerger = None
    SourceManager = None
    ConfigurationProcessor = None
    UnifiedSourceValidator = None
    VPNConfiguration = None
    check_dependencies = None
    detect_and_run = None
    run_in_jupyter = None

__all__ = [
    # Core classes
    "VPNSubscriptionMerger",
    "SourceManager", 
    "ConfigurationProcessor",
    "UnifiedSourceValidator",
    "VPNConfiguration",
    
    # Utility functions
    "check_dependencies",
    "detect_and_run",
    "run_in_jupyter",
    
    # Package metadata
    "__version__",
    "__author__",
    "__status__",
    "__license__"
]


def check_package_availability() -> dict:
    """Check which package components are available.
    
    Returns:
        Dictionary indicating availability of each component
    """
    return {
        'VPNSubscriptionMerger': VPNSubscriptionMerger is not None,
        'SourceManager': SourceManager is not None,
        'ConfigurationProcessor': ConfigurationProcessor is not None,
        'UnifiedSourceValidator': UnifiedSourceValidator is not None,
        'VPNConfiguration': VPNConfiguration is not None,
        'check_dependencies': check_dependencies is not None,
        'detect_and_run': detect_and_run is not None,
        'run_in_jupyter': run_in_jupyter is not None
    }


def get_package_info() -> dict:
    """Get comprehensive package information.
    
    Returns:
        Dictionary containing package metadata and component availability
    """
    return {
        'version': __version__,
        'author': __author__,
        'status': __status__,
        'license': __license__,
        'components_available': check_package_availability()
    }


# Add utility functions to __all__ for easy access
__all__.extend([
    'check_package_availability',
    'get_package_info'
])
