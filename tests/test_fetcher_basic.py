"""
Basic tests for fetcher module
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.fetcher.service import FetcherService
from streamline_vpn.fetcher.circuit_breaker import CircuitBreaker
from streamline_vpn.fetcher.rate_limiter import RateLimiter
from streamline_vpn.fetcher.io_client import SessionManager


class TestFetcherBasic:
    """Test basic fetcher functionality"""
    
    def test_fetcher_service_initialization(self):
        """Test fetcher service initialization"""
        service = FetcherService()
        assert service is not None
        assert hasattr(service, 'fetch')
        assert hasattr(service, 'fetch_multiple')
        assert hasattr(service, 'get_statistics')
    
    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization"""
        breaker = CircuitBreaker()
        assert breaker is not None
        assert hasattr(breaker, 'call')
        assert hasattr(breaker, 'get_state')
        assert hasattr(breaker, 'reset')
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter()
        assert limiter is not None
        assert hasattr(limiter, 'is_allowed')
        assert hasattr(limiter, 'wait_if_needed')
        assert hasattr(limiter, 'get_stats')
    
    def test_session_manager_initialization(self):
        """Test session manager initialization"""
        manager = SessionManager()
        assert manager is not None
        assert hasattr(manager, 'get_session')
        assert hasattr(manager, 'close_all')
    
    @pytest.mark.asyncio
    async def test_fetcher_service_fetch(self):
        """Test fetcher service fetch method"""
        service = FetcherService()
        
        with patch.object(service, 'fetch') as mock_fetch:
            mock_fetch.return_value = {"success": True, "data": "test data"}
            
            result = await service.fetch("https://example.com/sources.txt")
            assert result == {"success": True, "data": "test data"}
            mock_fetch.assert_called_once_with("https://example.com/sources.txt")
    
    @pytest.mark.asyncio
    async def test_fetcher_service_fetch_multiple(self):
        """Test fetcher service fetch multiple method"""
        service = FetcherService()
        
        with patch.object(service, 'fetch_multiple') as mock_fetch:
            mock_fetch.return_value = [{"success": True, "data": "test1"}, {"success": True, "data": "test2"}]
            
            urls = ["https://example.com/sources1.txt", "https://example.com/sources2.txt"]
            result = await service.fetch_multiple(urls)
            assert len(result) == 2
            assert result[0]["success"] is True
            assert result[1]["success"] is True
            mock_fetch.assert_called_once_with(urls)
    
    def test_fetcher_service_get_statistics(self):
        """Test fetcher service get statistics method"""
        service = FetcherService()
        
        stats = service.get_statistics()
        assert isinstance(stats, dict)
        assert "total_requests" in stats
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_call(self):
        """Test circuit breaker call method"""
        breaker = CircuitBreaker()
        
        async def test_func():
            return "success"
        
        result = await breaker.call(test_func)
        assert result == "success"
    
    def test_circuit_breaker_get_state(self):
        """Test circuit breaker get state method"""
        breaker = CircuitBreaker()
        
        state = breaker.get_state()
        assert state is not None
        assert hasattr(state, 'name')
    
    def test_circuit_breaker_reset(self):
        """Test circuit breaker reset method"""
        breaker = CircuitBreaker()
        
        with patch.object(breaker, 'reset') as mock_reset:
            mock_reset.return_value = None
            
            result = breaker.reset()
            assert result is None
            mock_reset.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rate_limiter_is_allowed(self):
        """Test rate limiter is allowed method"""
        limiter = RateLimiter()
        
        result = await limiter.is_allowed("test_key")
        assert isinstance(result, bool)
    
    def test_rate_limiter_get_stats(self):
        """Test rate limiter get stats method"""
        limiter = RateLimiter()
        
        stats = limiter.get_stats("test_key")
        assert isinstance(stats, dict)
        assert "current_requests" in stats
    
    
    @pytest.mark.asyncio
    async def test_session_manager_get_session(self):
        """Test session manager get session method"""
        manager = SessionManager()
        
        with patch.object(manager, 'get_session') as mock_get:
            mock_get.return_value = AsyncMock()
            
            result = await manager.get_session()
            assert result is not None
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_session_manager_close_all(self):
        """Test session manager close all method"""
        manager = SessionManager()
        
        result = await manager.close_all()
        assert result is None
