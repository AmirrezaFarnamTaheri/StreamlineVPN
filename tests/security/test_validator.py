import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import socket

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.security.validator import SecurityValidator

@pytest.fixture
def validator():
    """Fixture for SecurityValidator."""
    with patch('streamline_vpn.settings.get_settings') as mock_get_settings:
        mock_settings = mock_get_settings.return_value
        mock_settings.security.suspicious_tlds = ['.badtld']
        validator = SecurityValidator()
        return validator

class TestSecurityValidator:
    def test_validate_url_valid(self, validator):
        with patch('socket.getaddrinfo', return_value=[(2, 1, 6, '', ('1.2.3.4', 0))]):
            assert validator.validate_url("http://example.com") is True

    def test_validate_url_invalid(self, validator):
        assert validator.validate_url("invalid-url") is False

    def test_validate_url_with_exception(self, validator):
        with patch('streamline_vpn.security.validator.urlparse', side_effect=Exception("test error")):
            assert validator.validate_url("http://example.com") is False

    def test_validate_ip_address_valid(self, validator):
        assert validator.validate_ip_address("1.2.3.4") is True

    def test_validate_ip_address_invalid(self, validator):
        assert validator.validate_ip_address("invalid-ip") is False

    def test_validate_domain_valid(self, validator):
        with patch('socket.getaddrinfo', return_value=[(2, 1, 6, '', ('1.2.3.4', 0))]):
            assert validator.validate_domain("example.com") is True

    def test_validate_domain_localhost(self, validator):
        assert validator.validate_domain("localhost") is True

    def test_validate_domain_suspicious_tld(self, validator):
        from streamline_vpn.settings import Settings, SecuritySettings

        custom_security_settings = SecuritySettings(suspicious_tlds=[".badtld"])
        custom_settings = Settings(security=custom_security_settings)

        with patch('streamline_vpn.security.validator.get_settings', return_value=custom_settings):
            validator.__init__() # Re-initialize with patched settings
            assert validator.validate_domain("example.badtld") is False

    def test_validate_domain_invalid(self, validator):
        assert validator.validate_domain("invalid-domain") is False

    def test_validate_port_valid(self, validator):
        assert validator.validate_port(80) is True

    def test_validate_port_invalid(self, validator):
        assert validator.validate_port(99999) is False

    def test_validate_port_with_exception(self, validator):
        assert validator.validate_port("invalid") is False

    def test_validate_protocol_valid(self, validator):
        assert validator.validate_protocol("http") is True

    def test_validate_protocol_invalid(self, validator):
        assert validator.validate_protocol("invalid") is False

    def test_validate_encryption_valid(self, validator):
        assert validator.validate_encryption("aes-256-gcm") is True

    def test_validate_encryption_invalid(self, validator):
        assert validator.validate_encryption("invalid") is False

    def test_run_security_checks_safe(self, validator):
        with patch('socket.getaddrinfo', return_value=[(2, 1, 6, '', ('1.2.3.4', 0))]):
            result = validator.run_security_checks({"server": "example.com", "port": 80, "protocol": "http", "encryption": "aes-256-gcm"})
            assert result["is_valid"] is True

    def test_run_security_checks_unsafe(self, validator):
        result = validator.run_security_checks({"server": "example.com", "port": 99999, "protocol": "invalid", "encryption": "invalid"})
        assert result["is_valid"] is False

    def test_validate_uuid_valid(self, validator):
        assert validator.validate_uuid("123e4567-e89b-12d3-a456-426614174000") is True

    def test_validate_uuid_invalid(self, validator):
        assert validator.validate_uuid("invalid-uuid") is False

    def test_validate_configuration(self, validator):
        with patch('socket.getaddrinfo', return_value=[(2, 1, 6, '', ('1.2.3.4', 0))]):
            result = validator.validate_configuration({"server": "example.com", "port": 80, "protocol": "http", "encryption": "aes-256-gcm"})
            assert result["is_valid"] is True

    def test_validate_configuration_with_tls(self, validator):
        with patch('socket.getaddrinfo', return_value=[(2, 1, 6, '', ('1.2.3.4', 0))]):
            result = validator.validate_configuration({"server": "example.com", "port": 443, "protocol": "https", "encryption": "aes-256-gcm", "tls": True})
            assert result["security_score"] == 1.0

    def test_validate_configuration_with_suspicious_fields(self, validator):
        result = validator.validate_configuration({"script": "do_evil()"})
        assert result["is_valid"] is False
        assert "Suspicious field detected: script" in result["errors"]

    def test_validate_configuration_with_exception(self, validator):
        with patch.object(validator, '_is_valid_server', side_effect=Exception("test error")):
            result = validator.validate_configuration({"server": "example.com"})
            assert result["is_valid"] is False
            assert "Validation error: test error" in result["errors"]

    def test_has_suspicious_patterns(self, validator):
        assert validator._has_suspicious_patterns("<script>") is True
        assert validator._has_suspicious_patterns("http://example.com") is False

    def test_get_validation_statistics(self, validator):
        stats = validator.get_validation_statistics()
        assert "safe_ports" in stats
        assert "safe_protocols" in stats
        assert "safe_encryptions" in stats

    @patch('socket.getaddrinfo')
    def test_is_valid_domain_dns_timeout(self, mock_getaddrinfo, validator):
        mock_getaddrinfo.side_effect = socket.timeout
        assert validator._is_valid_domain("example.com") is True

    @patch('socket.getaddrinfo')
    def test_is_valid_domain_dns_error(self, mock_getaddrinfo, validator):
        mock_getaddrinfo.side_effect = socket.gaierror
        assert validator._is_valid_domain("example.com") is True

    @patch('socket.getaddrinfo')
    def test_is_valid_domain_private_ip(self, mock_getaddrinfo, validator):
        mock_getaddrinfo.return_value = [(2, 1, 6, '', ('192.168.1.1', 0))]
        assert validator._is_valid_domain("example.com") is False
