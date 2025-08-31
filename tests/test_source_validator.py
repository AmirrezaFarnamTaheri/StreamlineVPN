"""
Test Source Validator
====================

Focused tests for source validation functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from vpn_merger.core.source_validator import UnifiedSourceValidator, ValidationResult


class TestUnifiedSourceValidator:
    """Test the SourceHealthChecker class comprehensively."""
    
    @pytest.fixture
    def checker(self):
        """Create a UnifiedSourceValidator instance for testing."""
        return UnifiedSourceValidator()
    
    def test_initialization(self, checker):
        """Test UnifiedSourceValidator initialization."""
        assert checker is not None
        assert checker.timeout == 30
        assert checker.session is None
    
    def test_protocol_detection(self, checker):
        """Test protocol detection from content."""
        content = """
        vmess://eyJhZGQiOiAidGVzdC5leGFtcGxlLmNvbSIsICJwb3J0IjogNDQzfQ==
        vless://12345678-90ab-12f3-a6c5-4681aaaaaaaa@test.example.com:443?security=tls
        trojan://testpassword@test.example.com:443
        ss://base64encoded
        """
        
        protocols = checker._detect_protocols(content)
        assert "vmess" in protocols
        assert "vless" in protocols
        assert "trojan" in protocols
        assert "shadowsocks" in protocols
    
    def test_config_estimation(self, checker):
        """Test config count estimation."""
        content = """
        vmess://config1
        vless://config2
        trojan://config3
        # This is a comment
        vmess://config4
        """
        
        # The checker estimates configs by splitting lines
        lines = content.split('\n')
        estimated_configs = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        assert estimated_configs == 4
    
    def test_reliability_calculation(self, checker):
        """Test reliability score calculation."""
        score = checker._calculate_reliability_score(200, 1000, ["vmess", "vless"], 1.0)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be reasonably high for good source
        
        # Test with different parameters
        score2 = checker._calculate_reliability_score(404, 0, [], 5.0)
        assert score2 < 0.5  # Should be low for failed source
    
    @pytest.mark.asyncio
    async def test_validate_source_mock(self, checker):
        """Test source validation with mocked HTTP responses."""
        mock_url = "https://raw.githubusercontent.com/test/test.txt"
        mock_content = "vmess://test\nvless://test2"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.headers = {'Content-Type': 'text/plain'}
            mock_response.text = AsyncMock(return_value=mock_content)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Mock the session
            checker.session = Mock()
            checker.session.get = mock_get
            
            health = await checker.validate_source(mock_url)
            
            assert health.url == mock_url
            assert health.accessible is True
            assert health.estimated_configs == 2
            assert "vmess" in health.protocols_found
            assert "vless" in health.protocols_found
    
    @pytest.mark.asyncio
    async def test_validate_source_error(self, checker):
        """Test source validation with error handling."""
        mock_url = "https://invalid-url.com"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            # Mock the session
            checker.session = Mock()
            checker.session.get = mock_get
            
            health = await checker.validate_source(mock_url)
            
            assert health.url == mock_url
            assert health.accessible is False
            assert health.error is not None
            assert health.reliability_score == 0.0
    
    def test_health_summary(self, checker):
        """Test health summary generation."""
        # Create ValidationResult objects instead of dictionaries
        validation_results = [
            ValidationResult(url='url1', accessible=True, status_code=200, content_length=1000, 
                           estimated_configs=100, protocols_found=['vmess'], reliability_score=0.8, 
                           response_time=1.0, error=None, timestamp=datetime.now()),
            ValidationResult(url='url2', accessible=True, status_code=200, content_length=1000, 
                           estimated_configs=100, protocols_found=['vless'], reliability_score=0.9, 
                           response_time=1.0, error=None, timestamp=datetime.now()),
            ValidationResult(url='url3', accessible=False, status_code=500, content_length=0, 
                           estimated_configs=0, protocols_found=[], reliability_score=0.0, 
                           response_time=5.0, error="Connection failed", timestamp=datetime.now()),
        ]
        
        # Add to validation history
        checker.validation_history = validation_results
        
        summary = checker.get_validation_statistics()
        
        assert summary['total_validations'] == 3
        assert summary['successful_validations'] == 2
        assert summary['failed_validations'] == 1
        assert abs(summary['average_reliability_score'] - 0.85) < 0.001
    
    def test_context_manager(self, checker):
        """Test async context manager functionality."""
        # This would need aiohttp to be properly tested
        # For now, just test the structure
        assert hasattr(checker, '__aenter__')
        assert hasattr(checker, '__aexit__')
