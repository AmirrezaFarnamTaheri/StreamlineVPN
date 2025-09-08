"""
Utility Functions
================

Utility functions and helpers for StreamlineVPN.
"""

from .logging import setup_logging, get_logger
from .validation import validate_config
from .helpers import format_bytes, format_duration
from .error_handling import (
    CircuitBreaker,
    CircuitBreakerError,
    RetryExhaustedError,
    retry_with_backoff,
    timeout_handler,
    ErrorRecovery,
    safe_execute,
    safe_execute_async,
)

__all__ = [
    "setup_logging",
    "get_logger",
    "validate_config",
    "format_bytes",
    "format_duration",
    "CircuitBreaker",
    "CircuitBreakerError",
    "RetryExhaustedError",
    "retry_with_backoff",
    "timeout_handler",
    "ErrorRecovery",
    "safe_execute",
    "safe_execute_async",
]
