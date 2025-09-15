"""
Focused tests for Utils Error Handling
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.utils.error_handling import (
    retry_with_backoff, timeout_handler, safe_execute
)


class TestErrorHandling:
    """Test error handling functions"""
    
    def test_safe_execute_success(self):
        """Test safe execute on success"""
        def success_func():
            return "success"
        
        result = safe_execute(success_func)
        assert result == "success"
    
    def test_safe_execute_with_return_value(self):
        """Test safe execute with return value"""
        def failing_func():
            raise ValueError("Test error")
        
        result = safe_execute(failing_func, default_return="default")
        assert result == "default"
    
    def test_safe_execute_with_exception(self):
        """Test safe execute without return value"""
        def failing_func():
            raise ValueError("Test error")
        
        result = safe_execute(failing_func)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_success(self):
        """Test retry with backoff on success"""
        call_count = 0
        
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        decorated_func = retry_with_backoff(max_attempts=3)(success_func)
        result = await decorated_func()
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_failure(self):
        """Test retry with backoff on failure"""
        from streamline_vpn.utils.error_handling import RetryExhaustedError
        
        call_count = 0
        
        async def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Test error")
        
        decorated_func = retry_with_backoff(max_attempts=3)(failing_func)
        with pytest.raises(RetryExhaustedError):
            await decorated_func()
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_max_retries(self):
        """Test retry with backoff with max retries"""
        from streamline_vpn.utils.error_handling import RetryExhaustedError
        
        call_count = 0
        
        async def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Test error")
        
        decorated_func = retry_with_backoff(max_attempts=5)(failing_func)
        with pytest.raises(RetryExhaustedError):
            await decorated_func()
        assert call_count == 5
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_custom_delay(self):
        """Test retry with backoff with custom delay"""
        from streamline_vpn.utils.error_handling import RetryExhaustedError
        
        call_count = 0
        
        async def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Test error")
        
        decorated_func = retry_with_backoff(max_attempts=2, base_delay=0.1)(failing_func)
        with pytest.raises(RetryExhaustedError):
            await decorated_func()
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_timeout_handler_success(self):
        """Test timeout handler on success"""
        async def success_func():
            await asyncio.sleep(0.1)
            return "success"
        
        decorated_func = timeout_handler(timeout_seconds=1.0)(success_func)
        result = await decorated_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_timeout_handler_timeout(self):
        """Test timeout handler on timeout"""
        async def slow_func():
            await asyncio.sleep(2.0)
            return "success"
        
        decorated_func = timeout_handler(timeout_seconds=0.5)(slow_func)
        with pytest.raises(asyncio.TimeoutError):
            await decorated_func()
    
    @pytest.mark.asyncio
    async def test_timeout_handler_exception(self):
        """Test timeout handler on exception"""
        async def failing_func():
            raise ValueError("Test error")
        
        decorated_func = timeout_handler(timeout_seconds=1.0)(failing_func)
        with pytest.raises(ValueError):
            await decorated_func()
    
    @pytest.mark.asyncio
    async def test_timeout_handler_custom_timeout(self):
        """Test timeout handler with custom timeout"""
        async def slow_func():
            await asyncio.sleep(0.5)
            return "success"
        
        decorated_func = timeout_handler(timeout_seconds=1.0)(slow_func)
        result = await decorated_func()
        assert result == "success"
