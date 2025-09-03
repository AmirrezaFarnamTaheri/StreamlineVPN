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

# Optional security/sanitization helpers (re-exported if available)
try:
    from .sanitization import (
        is_safe_url,
        is_sql_safe,
        is_xss_safe,
        is_path_safe,
        sanitize_log_line,
        is_config_safe,
        is_https_secure,
    )
    __all__.extend([
        'is_safe_url',
        'is_sql_safe',
        'is_xss_safe',
        'is_path_safe',
        'sanitize_log_line',
        'is_config_safe',
        'is_https_secure',
    ])
except Exception:
    pass