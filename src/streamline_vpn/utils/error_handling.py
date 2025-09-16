"""
Error Handling Utilities
========================

Comprehensive error handling and recovery mechanisms for StreamlineVPN.
"""

import asyncio
import functools
import time
from typing import Any, Callable, Optional, Type, Union

from ..utils.logging import get_logger

logger = get_logger(__name__)


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


class CircuitBreaker:
    """Circuit breaker pattern implementation for fault tolerance."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def __call__(self, func: Callable) -> Callable:
        """Decorator for circuit breaker."""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await self._call_async(func, *args, **kwargs)
        return wrapper

    async def _call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise CircuitBreakerError("Circuit breaker is OPEN")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info("Circuit breaker reset to CLOSED")
            
            return result

        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.warning("Circuit breaker opened after %d failures", self.failure_count)
            
            raise


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,),
):
    """Retry decorator with exponential backoff and jitter.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to prevent thundering herd
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error("All %d attempts failed for %s", max_attempts, func.__name__)
                        raise RetryExhaustedError(f"All {max_attempts} attempts failed") from e
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    if jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)  # Add ±25% jitter
                    
                    logger.warning("Attempt %d failed for %s: %s. Retrying in %.2fs", attempt + 1, func.__name__, e, delay)
                    await asyncio.sleep(delay)
            
            # This should never be reached, but just in case
            raise RetryExhaustedError("Unexpected retry exhaustion") from last_exception
            
        return wrapper
    return decorator


def timeout_handler(timeout_seconds: float = 30.0):
    """Timeout decorator for async functions.

    Args:
        timeout_seconds: Timeout in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                logger.error("Function %s timed out after %ds", func.__name__, timeout_seconds)
                raise
        return wrapper
    return decorator


class ErrorRecovery:
    """Error recovery and fallback mechanisms."""

    @staticmethod
    async def with_fallback(
        primary_func: Callable,
        fallback_func: Callable,
        exceptions: tuple = (Exception,),
        *args,
        **kwargs
    ) -> Any:
        """Execute primary function with fallback on failure.

        Args:
            primary_func: Primary function to execute
            fallback_func: Fallback function to execute on failure
            exceptions: Exceptions to catch and trigger fallback
            *args: Arguments for functions
            **kwargs: Keyword arguments for functions

        Returns:
            Result from primary or fallback function
        """
        try:
            if asyncio.iscoroutinefunction(primary_func):
                return await primary_func(*args, **kwargs)
            else:
                return primary_func(*args, **kwargs)
        except exceptions as e:
            logger.warning("Primary function failed: %s. Using fallback.", e)
            try:
                if asyncio.iscoroutinefunction(fallback_func):
                    return await fallback_func(*args, **kwargs)
                else:
                    return fallback_func(*args, **kwargs)
            except Exception as fallback_error:
                logger.error("Fallback function also failed: %s", fallback_error)
                raise

    @staticmethod
    async def with_default(
        func: Callable,
        default_value: Any,
        exceptions: tuple = (Exception,),
        *args,
        **kwargs
    ) -> Any:
        """Execute function with default value on failure.

        Args:
            func: Function to execute
            default_value: Default value to return on failure
            exceptions: Exceptions to catch
            *args: Arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Result from function or default value
        """
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except exceptions as e:
            logger.warning("Function failed, using default value: %s", e)
            return default_value


def safe_execute(
    func: Callable,
    default_return: Any = None,
    exceptions: tuple = (Exception,),
    log_errors: bool = True,
    *args,
    **kwargs
) -> Any:
    """Safely execute function with error handling.

    Args:
        func: Function to execute
        default_return: Value to return on error
        exceptions: Exceptions to catch
        log_errors: Whether to log errors
        *args: Arguments for function
        **kwargs: Keyword arguments for function

    Returns:
        Function result or default_return on error
    """
    try:
        return func(*args, **kwargs)
    except exceptions as e:
        if log_errors:
            logger.error("Safe execution failed for %s: %s", func.__name__, e)
        return default_return


async def safe_execute_async(
    func: Callable,
    default_return: Any = None,
    exceptions: tuple = (Exception,),
    log_errors: bool = True,
    *args,
    **kwargs
) -> Any:
    """Safely execute async function with error handling.

    Args:
        func: Async function to execute
        default_return: Value to return on error
        exceptions: Exceptions to catch
        log_errors: Whether to log errors
        *args: Arguments for function
        **kwargs: Keyword arguments for function

    Returns:
        Function result or default_return on error
    """
    try:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    except exceptions as e:
        if log_errors:
            logger.error("Safe async execution failed for %s: %s", func.__name__, e)
        return default_return


# Simple helpers expected by tests
def handle_exception(func: Callable, return_value: Any = None, *args, **kwargs) -> Any:
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error("Exception handled: %s", e)
        return return_value


async def async_handle_exception(func: Callable, return_value: Any = None, *args, **kwargs) -> Any:
    try:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)
    except Exception as e:
        logger.error("Async exception handled: %s", e)
        return return_value