"""
Focused tests for SecurityManager
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.security.manager import SecurityManager


class TestSecurityManager:
    """Test SecurityManager class"""
    
    def test_initialization(self):
        """Test security manager initialization"""
        manager = SecurityManager()
        assert hasattr(manager, 'blocklist_manager')
        assert hasattr(manager, 'pattern_analyzer')
        assert hasattr(manager, 'rate_limiter')
        assert hasattr(manager, 'threat_analyzer')
        assert hasattr(manager, 'validator')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test security manager initialization"""
        manager = SecurityManager()
        result = await manager.initialize()
        assert result is True
    
    def test_validate_request(self):
        """Test validating request"""
        manager = SecurityManager()
        
        request_data = {
            "ip": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "path": "/api/test"
        }
        
        with patch.object(manager, 'validate_request') as mock_validate:
            mock_validate.return_value = {"is_valid": True, "risk_score": 0.1}
            
            result = manager.validate_request(request_data)
            assert result["is_valid"] is True
            assert result["risk_score"] == 0.1
            mock_validate.assert_called_once_with(request_data)
    
    def test_analyze_threat(self):
        """Test analyzing threat"""
        manager = SecurityManager()
        
        threat_data = {
            "ip": "192.168.1.1",
            "pattern": "suspicious_pattern",
            "severity": "high"
        }
        
        with patch.object(manager, 'analyze_threat') as mock_analyze:
            mock_analyze.return_value = {"is_threat": True, "confidence": 0.9}
            
            result = manager.analyze_threat(threat_data)
            assert result["is_threat"] is True
            assert result["confidence"] == 0.9
            mock_analyze.assert_called_once_with(threat_data)
    
    def test_check_rate_limit(self):
        """Test checking rate limit"""
        manager = SecurityManager()
        
        with patch.object(manager, 'check_rate_limit') as mock_check:
            mock_check.return_value = {"is_allowed": True, "remaining": 100}
            
            result = manager.check_rate_limit("192.168.1.1")
            assert result["is_allowed"] is True
            assert result["remaining"] == 100
            mock_check.assert_called_once_with("192.168.1.1")
    
    def test_validate_configuration(self):
        """Test validating configuration"""
        manager = SecurityManager()
        
        config = {"type": "vmess", "name": "test"}
        
        with patch.object(manager, 'validate_configuration') as mock_validate:
            mock_validate.return_value = {"is_valid": True, "issues": []}
            
            result = manager.validate_configuration(config)
            assert result["is_valid"] is True
            assert result["issues"] == []
            mock_validate.assert_called_once_with(config)
    
    def test_scan_for_threats(self):
        """Test scanning for threats"""
        manager = SecurityManager()
        
        data = {"content": "test content", "source": "test"}
        
        with patch.object(manager, 'scan_for_threats') as mock_scan:
            mock_scan.return_value = {"threats_found": 0, "threats": []}
            
            result = manager.scan_for_threats(data)
            assert result["threats_found"] == 0
            assert result["threats"] == []
            mock_scan.assert_called_once_with(data)
    
    def test_get_security_status(self):
        """Test getting security status"""
        manager = SecurityManager()
        
        with patch.object(manager, 'get_security_status') as mock_status:
            mock_status.return_value = {
                "status": "healthy",
                "threats_blocked": 0,
                "rate_limits_active": 0
            }
            
            result = manager.get_security_status()
            assert result["status"] == "healthy"
            assert "threats_blocked" in result
            assert "rate_limits_active" in result
            mock_status.assert_called_once()
    
    def test_shutdown(self):
        """Test shutting down security manager"""
        manager = SecurityManager()
        
        with patch.object(manager, 'shutdown') as mock_shutdown:
            mock_shutdown.return_value = None
            
            result = manager.shutdown()
            assert result is None
            mock_shutdown.assert_called_once()
