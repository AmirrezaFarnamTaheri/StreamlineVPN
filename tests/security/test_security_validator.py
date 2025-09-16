"""
Tests for SecurityValidator.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from streamline_vpn.security.validator import SecurityValidator


class TestSecurityValidator:
    """Test SecurityValidator class"""
    
    def test_initialization(self):
        """Test security validator initialization"""
        validator = SecurityValidator()
        assert hasattr(validator, 'validation_rules')
        assert hasattr(validator, 'security_checks')
    
    def test_validate_configuration(self):
        """Test validating configuration"""
        validator = SecurityValidator()
        
        # Test valid configuration
        valid_config = {
            "server": "example.com",
            "port": 443,
            "protocol": "vmess",
            "uuid": "12345678-1234-1234-1234-123456789012"
        }
        
        result = validator.validate_configuration(valid_config)
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        
        # Test invalid configuration
        invalid_config = {
            "server": "",  # Empty server
            "port": -1,    # Invalid port
            "protocol": "unknown"  # Unknown protocol
        }
        
        result = validator.validate_configuration(invalid_config)
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
    
    def test_validate_url(self):
        """Test validating URL"""
        validator = SecurityValidator()
        
        # Test valid URLs
        assert validator.validate_url("https://example.com") is True
        assert validator.validate_url("http://localhost:8080") is True
        
        # Test invalid URLs
        assert validator.validate_url("invalid-url") is False
        assert validator.validate_url("ftp://example.com") is False
        assert validator.validate_url("") is False
    
    def test_validate_ip_address(self):
        """Test validating IP address"""
        validator = SecurityValidator()
        
        # Test valid IPs
        assert validator.validate_ip_address("192.168.1.1") is True
        assert validator.validate_ip_address("127.0.0.1") is True
        
        # Test invalid IPs
        assert validator.validate_ip_address("999.999.999.999") is False
        assert validator.validate_ip_address("192.168.1") is False
        assert validator.validate_ip_address("") is False
    
    def test_validate_domain(self):
        """Test validating domain"""
        validator = SecurityValidator()
        
        # Test valid domains
        assert validator.validate_domain("example.com") is True
        assert validator.validate_domain("sub.example.com") is True
        
        # Test invalid domains
        assert validator.validate_domain("") is False
        assert validator.validate_domain("invalid..domain") is False
        assert validator.validate_domain("domain-with-dash.com") is True
    
    def test_validate_port(self):
        """Test validating port"""
        validator = SecurityValidator()
        
        # Test valid ports
        assert validator.validate_port(80) is True
        assert validator.validate_port(443) is True
        assert validator.validate_port(8080) is True
        
        # Test invalid ports
        assert validator.validate_port(-1) is False
        assert validator.validate_port(0) is False
        assert validator.validate_port(65536) is False
    
    def test_validate_uuid(self):
        """Test validating UUID"""
        validator = SecurityValidator()
        
        # Test valid UUIDs
        assert validator.validate_uuid("12345678-1234-1234-1234-123456789012") is True
        assert validator.validate_uuid("00000000-0000-0000-0000-000000000000") is True
        
        # Test invalid UUIDs
        assert validator.validate_uuid("invalid-uuid") is False
        assert validator.validate_uuid("12345678-1234-1234-1234") is False
        assert validator.validate_uuid("") is False
    
    def test_run_security_checks(self):
        """Test running security checks"""
        validator = SecurityValidator()
        
        config = {
            "server": "example.com",
            "port": 443,
            "protocol": "vmess",
            "uuid": "12345678-1234-1234-1234-123456789012"
        }
        
        result = validator.run_security_checks(config)
        assert "checks_passed" in result
        assert "checks_failed" in result
        assert "overall_score" in result
        assert isinstance(result["overall_score"], (int, float))

