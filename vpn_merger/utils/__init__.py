"""
Utility functions for VPN Subscription Merger.

This package contains helper utilities for:
- Dependencies: Environment validation and dependency checking
- Environment: Execution mode detection and Jupyter integration
"""

from .dependencies import check_dependencies
from .environment import detect_and_run, run_in_jupyter

__all__ = [
    "check_dependencies",
    "detect_and_run", 
    "run_in_jupyter",
]
