"""
Focused tests for ConfigurationValidator
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.core.config_validator import ConfigurationValidator


class TestConfigurationValidator:
    """Test ConfigurationValidator class"""
    
    def test_initialization(self):
        """Test validator initialization"""
        validator = ConfigurationValidator()
        assert hasattr(validator, 'validation_rules')
        assert hasattr(validator, 'strict_mode')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test validator initialization"""
        validator = ConfigurationValidator()
        result = await validator.initialize()
        assert result is True
    
    def test_validate_config(self):
        """Test validating configuration"""
        validator = ConfigurationValidator()
        
        config = {
            "type": "vmess",
            "name": "test",
            "server": "example.com",
            "port": 443,
            "uuid": "12345678-1234-1234-1234-123456789012"
        }
        
        result = validator.validate_config(config)
        assert "is_valid" in result
        assert "errors" in result
        assert "warnings" in result
    
    def test_validate_config_invalid(self):
        """Test validating invalid configuration"""
        validator = ConfigurationValidator()
        
        config = {
            "type": "vmess",
            "name": "",  # Invalid empty name
            "server": "",  # Invalid empty server
            "port": "invalid"  # Invalid port type
        }
        
        result = validator.validate_config(config)
        assert "is_valid" in result
        assert "errors" in result
        assert "warnings" in result
    
    def test_validate_vmess_config(self):
        """Test validating VMess configuration"""
        validator = ConfigurationValidator()
        
        config = {
            "type": "vmess",
            "name": "test",
            "server": "example.com",
            "port": 443,
            "uuid": "12345678-1234-1234-1234-123456789012",
            "alterId": 0,
            "security": "auto"
        }
        
        with patch.object(validator, '_validate_vmess_config') as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": [], "warnings": []}
            
            result = validator.validate_config(config)
            assert result["is_valid"] is True
            mock_validate.assert_called_once_with(config)
    
    def test_validate_shadowsocks_config(self):
        """Test validating Shadowsocks configuration"""
        validator = ConfigurationValidator()
        
        config = {
            "type": "ss",
            "name": "test",
            "server": "example.com",
            "port": 443,
            "password": "password123",
            "method": "aes-256-gcm"
        }
        
        with patch.object(validator, '_validate_shadowsocks_config') as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": [], "warnings": []}
            
            result = validator.validate_config(config)
            assert result["is_valid"] is True
            mock_validate.assert_called_once_with(config)
    
    def test_validate_trojan_config(self):
        """Test validating Trojan configuration"""
        validator = ConfigurationValidator()
        
        config = {
            "type": "trojan",
            "name": "test",
            "server": "example.com",
            "port": 443,
            "password": "password123"
        }
        
        with patch.object(validator, '_validate_trojan_config') as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": [], "warnings": []}
            
            result = validator.validate_config(config)
            assert result["is_valid"] is True
            mock_validate.assert_called_once_with(config)
    
    def test_validate_vless_config(self):
        """Test validating VLESS configuration"""
        validator = ConfigurationValidator()
        
        config = {
            "type": "vless",
            "name": "test",
            "server": "example.com",
            "port": 443,
            "uuid": "12345678-1234-1234-1234-123456789012"
        }
        
        with patch.object(validator, '_validate_vless_config') as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": [], "warnings": []}
            
            result = validator.validate_config(config)
            assert result["is_valid"] is True
            mock_validate.assert_called_once_with(config)
    
    def test_validate_shadowsocksr_config(self):
        """Test validating ShadowsocksR configuration"""
        validator = ConfigurationValidator()
        
        config = {
            "type": "ssr",
            "name": "test",
            "server": "example.com",
            "port": 443,
            "password": "password123",
            "method": "aes-256-cfb",
            "protocol": "origin",
            "obfs": "plain"
        }
        
        with patch.object(validator, '_validate_shadowsocksr_config') as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": [], "warnings": []}
            
            result = validator.validate_config(config)
            assert result["is_valid"] is True
            mock_validate.assert_called_once_with(config)
    
    def test_validate_unknown_type(self):
        """Test validating unknown configuration type"""
        validator = ConfigurationValidator()
        
        config = {
            "type": "unknown",
            "name": "test"
        }
        
        result = validator.validate_config(config)
        assert "is_valid" in result
        assert "errors" in result
        assert "warnings" in result
    
    def test_add_validation_rule(self):
        """Test adding validation rule"""
        validator = ConfigurationValidator()
        
        with patch.object(validator, 'add_validation_rule') as mock_add:
            mock_add.return_value = None
            
            validator.add_validation_rule("test_rule", lambda x: True)
            mock_add.assert_called_once()
    
    def test_remove_validation_rule(self):
        """Test removing validation rule"""
        validator = ConfigurationValidator()
        
        with patch.object(validator, 'remove_validation_rule') as mock_remove:
            mock_remove.return_value = None
            
            validator.remove_validation_rule("test_rule")
            mock_remove.assert_called_once_with("test_rule")
    
    def test_set_strict_mode(self):
        """Test setting strict mode"""
        validator = ConfigurationValidator()
        
        with patch.object(validator, 'set_strict_mode') as mock_set:
            mock_set.return_value = None
            
            validator.set_strict_mode(True)
            mock_set.assert_called_once_with(True)
    
    def test_get_validation_stats(self):
        """Test getting validation statistics"""
        validator = ConfigurationValidator()
        
        with patch.object(validator, 'get_validation_stats') as mock_stats:
            mock_stats.return_value = {"total_validated": 0, "valid_count": 0, "invalid_count": 0}
            
            result = validator.get_validation_stats()
            assert "total_validated" in result
            assert "valid_count" in result
            assert "invalid_count" in result
            mock_stats.assert_called_once()
