"""
Focused tests for Security Components
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.security.blocklist_manager import BlocklistManager
from streamline_vpn.security.pattern_analyzer import PatternAnalyzer
from streamline_vpn.security.rate_limiter import RateLimiter
from streamline_vpn.security.threat_analyzer import ThreatAnalyzer
from streamline_vpn.security.validator import SecurityValidator


class TestBlocklistManager:
    """Test BlocklistManager class"""
    
    def test_initialization(self):
        """Test blocklist manager initialization"""
        manager = BlocklistManager()
        assert hasattr(manager, 'blocked_ips')
        assert hasattr(manager, 'blocked_domains')
        assert hasattr(manager, 'blocked_patterns')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test blocklist manager initialization"""
        manager = BlocklistManager()
        result = await manager.initialize()
        assert result is True
    
    def test_add_blocked_ip(self):
        """Test adding blocked IP"""
        manager = BlocklistManager()
        
        with patch.object(manager, 'add_blocked_ip') as mock_add:
            mock_add.return_value = True
            
            result = manager.add_blocked_ip("192.168.1.1")
            assert result is True
            mock_add.assert_called_once_with("192.168.1.1")
    
    def test_remove_blocked_ip(self):
        """Test removing blocked IP"""
        manager = BlocklistManager()
        
        with patch.object(manager, 'remove_blocked_ip') as mock_remove:
            mock_remove.return_value = True
            
            result = manager.remove_blocked_ip("192.168.1.1")
            assert result is True
            mock_remove.assert_called_once_with("192.168.1.1")
    
    def test_is_blocked_ip(self):
        """Test checking if IP is blocked"""
        manager = BlocklistManager()
        
        with patch.object(manager, 'is_blocked_ip') as mock_check:
            mock_check.return_value = False
            
            result = manager.is_blocked_ip("192.168.1.1")
            assert result is False
            mock_check.assert_called_once_with("192.168.1.1")
    
    def test_add_blocked_domain(self):
        """Test adding blocked domain"""
        manager = BlocklistManager()
        
        with patch.object(manager, 'add_blocked_domain') as mock_add:
            mock_add.return_value = True
            
            result = manager.add_blocked_domain("example.com")
            assert result is True
            mock_add.assert_called_once_with("example.com")
    
    def test_remove_blocked_domain(self):
        """Test removing blocked domain"""
        manager = BlocklistManager()
        
        with patch.object(manager, 'remove_blocked_domain') as mock_remove:
            mock_remove.return_value = True
            
            result = manager.remove_blocked_domain("example.com")
            assert result is True
            mock_remove.assert_called_once_with("example.com")
    
    def test_is_blocked_domain(self):
        """Test checking if domain is blocked"""
        manager = BlocklistManager()
        
        with patch.object(manager, 'is_blocked_domain') as mock_check:
            mock_check.return_value = False
            
            result = manager.is_blocked_domain("example.com")
            assert result is False
            mock_check.assert_called_once_with("example.com")
    
    def test_add_blocked_pattern(self):
        """Test adding blocked pattern"""
        manager = BlocklistManager()
        
        with patch.object(manager, 'add_blocked_pattern') as mock_add:
            mock_add.return_value = True
            
            result = manager.add_blocked_pattern("malicious.*")
            assert result is True
            mock_add.assert_called_once_with("malicious.*")
    
    def test_remove_blocked_pattern(self):
        """Test removing blocked pattern"""
        manager = BlocklistManager()
        
        with patch.object(manager, 'remove_blocked_pattern') as mock_remove:
            mock_remove.return_value = True
            
            result = manager.remove_blocked_pattern("malicious.*")
            assert result is True
            mock_remove.assert_called_once_with("malicious.*")
    
    def test_is_blocked_pattern(self):
        """Test checking if pattern is blocked"""
        manager = BlocklistManager()
        
        with patch.object(manager, 'is_blocked_pattern') as mock_check:
            mock_check.return_value = False
            
            result = manager.is_blocked_pattern("malicious.*")
            assert result is False
            mock_check.assert_called_once_with("malicious.*")
    
    def test_get_blocklist_stats(self):
        """Test getting blocklist statistics"""
        manager = BlocklistManager()
        
        with patch.object(manager, 'get_blocklist_stats') as mock_stats:
            mock_stats.return_value = {
                "blocked_ips": 0,
                "blocked_domains": 0,
                "blocked_patterns": 0
            }
            
            result = manager.get_blocklist_stats()
            assert "blocked_ips" in result
            assert "blocked_domains" in result
            assert "blocked_patterns" in result
            mock_stats.assert_called_once()


class TestPatternAnalyzer:
    """Test PatternAnalyzer class"""
    
    def test_initialization(self):
        """Test pattern analyzer initialization"""
        analyzer = PatternAnalyzer()
        assert hasattr(analyzer, 'suspicious_patterns')
        assert hasattr(analyzer, 'pattern_rules')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test pattern analyzer initialization"""
        analyzer = PatternAnalyzer()
        result = await analyzer.initialize()
        assert result is True
    
    def test_analyze_pattern(self):
        """Test analyzing pattern"""
        analyzer = PatternAnalyzer()
        
        with patch.object(analyzer, 'analyze_pattern') as mock_analyze:
            mock_analyze.return_value = {"is_suspicious": False, "confidence": 0.1}
            
            result = analyzer.analyze_pattern("normal text")
            assert result["is_suspicious"] is False
            assert result["confidence"] == 0.1
            mock_analyze.assert_called_once_with("normal text")
    
    def test_analyze_pattern_safe(self):
        """Test analyzing safe pattern"""
        analyzer = PatternAnalyzer()
        
        with patch.object(analyzer, 'analyze_pattern') as mock_analyze:
            mock_analyze.return_value = {"is_suspicious": False, "confidence": 0.0}
            
            result = analyzer.analyze_pattern("safe content")
            assert result["is_suspicious"] is False
            assert result["confidence"] == 0.0
            mock_analyze.assert_called_once_with("safe content")
    
    def test_add_suspicious_pattern(self):
        """Test adding suspicious pattern"""
        analyzer = PatternAnalyzer()
        
        with patch.object(analyzer, 'add_suspicious_pattern') as mock_add:
            mock_add.return_value = True
            
            result = analyzer.add_suspicious_pattern("malicious.*")
            assert result is True
            mock_add.assert_called_once_with("malicious.*")
    
    def test_remove_suspicious_pattern(self):
        """Test removing suspicious pattern"""
        analyzer = PatternAnalyzer()
        
        with patch.object(analyzer, 'remove_suspicious_pattern') as mock_remove:
            mock_remove.return_value = True
            
            result = analyzer.remove_suspicious_pattern("malicious.*")
            assert result is True
            mock_remove.assert_called_once_with("malicious.*")
    
    def test_analyze_configuration(self):
        """Test analyzing configuration"""
        analyzer = PatternAnalyzer()
        
        config = {"type": "vmess", "name": "test"}
        
        with patch.object(analyzer, 'analyze_configuration') as mock_analyze:
            mock_analyze.return_value = {"is_safe": True, "issues": []}
            
            result = analyzer.analyze_configuration(config)
            assert result["is_safe"] is True
            assert result["issues"] == []
            mock_analyze.assert_called_once_with(config)
    
    def test_get_analysis_stats(self):
        """Test getting analysis statistics"""
        analyzer = PatternAnalyzer()
        
        with patch.object(analyzer, 'get_analysis_stats') as mock_stats:
            mock_stats.return_value = {
                "total_analyzed": 0,
                "suspicious_found": 0,
                "patterns_count": 0
            }
            
            result = analyzer.get_analysis_stats()
            assert "total_analyzed" in result
            assert "suspicious_found" in result
            assert "patterns_count" in result
            mock_stats.assert_called_once()


class TestRateLimiter:
    """Test RateLimiter class"""
    
    def test_initialization(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter()
        assert hasattr(limiter, 'requests')
        assert hasattr(limiter, 'max_requests')
        assert hasattr(limiter, 'time_window')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter()
        result = await limiter.initialize()
        assert result is True
    
    def test_is_allowed(self):
        """Test checking if request is allowed"""
        limiter = RateLimiter()
        
        with patch.object(limiter, 'is_allowed') as mock_check:
            mock_check.return_value = True
            
            result = limiter.is_allowed("192.168.1.1")
            assert result is True
            mock_check.assert_called_once_with("192.168.1.1")
    
    def test_is_allowed_exceeded(self):
        """Test checking when rate limit exceeded"""
        limiter = RateLimiter(max_requests=10, time_window=60)
        
        with patch.object(limiter, 'is_allowed') as mock_check:
            mock_check.return_value = False
            
            result = limiter.is_allowed("192.168.1.1")
            assert result is False
            mock_check.assert_called_once_with("192.168.1.1")
    
    def test_reset_limits(self):
        """Test resetting rate limits"""
        limiter = RateLimiter()
        
        with patch.object(limiter, 'reset_limits') as mock_reset:
            mock_reset.return_value = None
            
            result = limiter.reset_limits("192.168.1.1")
            assert result is None
            mock_reset.assert_called_once_with("192.168.1.1")
    
    def test_get_rate_limit_stats(self):
        """Test getting rate limit statistics"""
        limiter = RateLimiter()
        
        with patch.object(limiter, 'get_rate_limit_stats') as mock_stats:
            mock_stats.return_value = {
                "total_requests": 0,
                "allowed_requests": 0,
                "blocked_requests": 0
            }
            
            result = limiter.get_rate_limit_stats()
            assert "total_requests" in result
            assert "allowed_requests" in result
            assert "blocked_requests" in result
            mock_stats.assert_called_once()


class TestThreatAnalyzer:
    """Test ThreatAnalyzer class"""
    
    def test_initialization(self):
        """Test threat analyzer initialization"""
        analyzer = ThreatAnalyzer()
        assert hasattr(analyzer, 'threat_patterns')
        assert hasattr(analyzer, 'threat_rules')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test threat analyzer initialization"""
        analyzer = ThreatAnalyzer()
        result = await analyzer.initialize()
        assert result is True
    
    def test_analyze_threat(self):
        """Test analyzing threat"""
        analyzer = ThreatAnalyzer()
        
        threat_data = {"ip": "192.168.1.1", "pattern": "suspicious"}
        
        with patch.object(analyzer, 'analyze_threat') as mock_analyze:
            mock_analyze.return_value = {"is_threat": False, "confidence": 0.1}
            
            result = analyzer.analyze_threat(threat_data)
            assert result["is_threat"] is False
            assert result["confidence"] == 0.1
            mock_analyze.assert_called_once_with(threat_data)
    
    def test_analyze_threat_safe(self):
        """Test analyzing safe data"""
        analyzer = ThreatAnalyzer()
        
        threat_data = {"ip": "192.168.1.1", "pattern": "normal"}
        
        with patch.object(analyzer, 'analyze_threat') as mock_analyze:
            mock_analyze.return_value = {"is_threat": False, "confidence": 0.0}
            
            result = analyzer.analyze_threat(threat_data)
            assert result["is_threat"] is False
            assert result["confidence"] == 0.0
            mock_analyze.assert_called_once_with(threat_data)
    
    def test_add_threat_pattern(self):
        """Test adding threat pattern"""
        analyzer = ThreatAnalyzer()
        
        with patch.object(analyzer, 'add_threat_pattern') as mock_add:
            mock_add.return_value = True
            
            result = analyzer.add_threat_pattern("malicious.*")
            assert result is True
            mock_add.assert_called_once_with("malicious.*")
    
    def test_remove_threat_pattern(self):
        """Test removing threat pattern"""
        analyzer = ThreatAnalyzer()
        
        with patch.object(analyzer, 'remove_threat_pattern') as mock_remove:
            mock_remove.return_value = True
            
            result = analyzer.remove_threat_pattern("malicious.*")
            assert result is True
            mock_remove.assert_called_once_with("malicious.*")
    
    def test_analyze_configuration(self):
        """Test analyzing configuration for threats"""
        analyzer = ThreatAnalyzer()
        
        config = {"type": "vmess", "name": "test"}
        
        with patch.object(analyzer, 'analyze_configuration') as mock_analyze:
            mock_analyze.return_value = {"is_safe": True, "threats": []}
            
            result = analyzer.analyze_configuration(config)
            assert result["is_safe"] is True
            assert result["threats"] == []
            mock_analyze.assert_called_once_with(config)
    
    def test_get_threat_stats(self):
        """Test getting threat statistics"""
        analyzer = ThreatAnalyzer()
        
        with patch.object(analyzer, 'get_threat_stats') as mock_stats:
            mock_stats.return_value = {
                "total_analyzed": 0,
                "threats_detected": 0,
                "patterns_count": 0
            }
            
            result = analyzer.get_threat_stats()
            assert "total_analyzed" in result
            assert "threats_detected" in result
            assert "patterns_count" in result
            mock_stats.assert_called_once()


class TestSecurityValidator:
    """Test SecurityValidator class"""
    
    def test_initialization(self):
        """Test security validator initialization"""
        validator = SecurityValidator()
        assert hasattr(validator, 'validation_rules')
        assert hasattr(validator, 'security_checks')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test security validator initialization"""
        validator = SecurityValidator()
        result = await validator.initialize()
        assert result is True
    
    def test_validate_configuration(self):
        """Test validating configuration"""
        validator = SecurityValidator()
        
        config = {"type": "vmess", "name": "test"}
        
        with patch.object(validator, 'validate_configuration') as mock_validate:
            mock_validate.return_value = {"is_valid": True, "issues": []}
            
            result = validator.validate_configuration(config)
            assert result["is_valid"] is True
            assert result["issues"] == []
            mock_validate.assert_called_once_with(config)
    
    def test_validate_configuration_invalid(self):
        """Test validating invalid configuration"""
        validator = SecurityValidator()
        
        config = {"type": "invalid"}
        
        with patch.object(validator, 'validate_configuration') as mock_validate:
            mock_validate.return_value = {"is_valid": False, "issues": ["Invalid type"]}
            
            result = validator.validate_configuration(config)
            assert result["is_valid"] is False
            assert "Invalid type" in result["issues"]
            mock_validate.assert_called_once_with(config)
    
    def test_validate_request(self):
        """Test validating request"""
        validator = SecurityValidator()
        
        request_data = {"ip": "192.168.1.1", "path": "/api/test"}
        
        with patch.object(validator, 'validate_request') as mock_validate:
            mock_validate.return_value = {"is_valid": True, "issues": []}
            
            result = validator.validate_request(request_data)
            assert result["is_valid"] is True
            assert result["issues"] == []
            mock_validate.assert_called_once_with(request_data)
    
    def test_validate_request_invalid(self):
        """Test validating invalid request"""
        validator = SecurityValidator()
        
        request_data = {"ip": "invalid", "path": ""}
        
        with patch.object(validator, 'validate_request') as mock_validate:
            mock_validate.return_value = {"is_valid": False, "issues": ["Invalid IP"]}
            
            result = validator.validate_request(request_data)
            assert result["is_valid"] is False
            assert "Invalid IP" in result["issues"]
            mock_validate.assert_called_once_with(request_data)
    
    def test_add_validation_rule(self):
        """Test adding validation rule"""
        validator = SecurityValidator()
        
        with patch.object(validator, 'add_validation_rule') as mock_add:
            mock_add.return_value = True
            
            result = validator.add_validation_rule("test_rule", lambda x: True)
            assert result is True
            mock_add.assert_called_once()
    
    def test_remove_validation_rule(self):
        """Test removing validation rule"""
        validator = SecurityValidator()
        
        with patch.object(validator, 'remove_validation_rule') as mock_remove:
            mock_remove.return_value = True
            
            result = validator.remove_validation_rule("test_rule")
            assert result is True
            mock_remove.assert_called_once_with("test_rule")
    
    def test_get_validation_stats(self):
        """Test getting validation statistics"""
        validator = SecurityValidator()
        
        with patch.object(validator, 'get_validation_stats') as mock_stats:
            mock_stats.return_value = {
                "total_validated": 0,
                "valid_count": 0,
                "invalid_count": 0
            }
            
            result = validator.get_validation_stats()
            assert "total_validated" in result
            assert "valid_count" in result
            assert "invalid_count" in result
            mock_stats.assert_called_once()
