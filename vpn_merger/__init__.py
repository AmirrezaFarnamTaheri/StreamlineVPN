"""
VPN Subscription Merger
======================

A high-performance, production-ready VPN subscription merger that aggregates and processes
VPN configurations from multiple sources with advanced filtering, validation, and output formatting.

Version: 2.0.0
Status: Production Ready
License: MIT
Author: VPN Merger Team
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core.merger import VPNSubscriptionMerger
    from .core.source_manager import SourceManager
    from .core.config_processor import ConfigurationProcessor
    from .core.health_checker import SourceHealthChecker
    from .models.configuration import VPNConfiguration
    from .utils.dependencies import check_dependencies
    from .utils.environment import detect_and_run, run_in_jupyter

# Core components
from .core.merger import VPNSubscriptionMerger
from .core.source_manager import SourceManager
from .core.config_processor import ConfigurationProcessor
from .core.health_checker import SourceHealthChecker

# Data models
from .models.configuration import VPNConfiguration

# Utility functions
from .utils.dependencies import check_dependencies
from .utils.environment import detect_and_run, run_in_jupyter

__version__ = "2.0.0"
__author__ = "VPN Merger Team"
__status__ = "Production Ready"
__license__ = "MIT"

__all__ = [
    # Core classes
    "VPNSubscriptionMerger",
    "SourceManager", 
    "ConfigurationProcessor",
    "SourceHealthChecker",
    
    # Data models
    "VPNConfiguration",
    
    # Utility functions
    "check_dependencies",
    "detect_and_run",
    "run_in_jupyter",
]
