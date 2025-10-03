"""Tests for core processing validator module."""

import pytest
from unittest.mock import patch, MagicMock

from streamline_vpn.core.processing.validator import ConfigurationValidator
from streamline_vpn.models.configuration import VPNConfiguration, Protocol


class TestConfigurationValidator:
    """Test cases for ConfigurationValidator."""

    @pytest.fixture
    def validator(self):
        """Create ConfigurationValidator instance."""
        return ConfigurationValidator()

    @pytest.fixture
    def valid_vmess_config(self):
        """Create valid VMess configuration."""
        config = VPNConfiguration(
            server="example.com",
            port=443,
            protocol=Protocol.VMESS,
            user_id="test-uuid-12345",
            id="vmess-test"
        )
        return config

    @pytest.fixture
    def valid_vless_config(self):
        """Create valid VLESS configuration."""
        config = VPNConfiguration(
            server="192.168.1.1",
            port=8080,
            protocol=Protocol.VLESS,
            user_id="test-uuid-67890",
            id="vless-test"
        )
        return config

    @pytest.fixture
    def valid_trojan_config(self):
        """Create valid Trojan configuration."""
        config = VPNConfiguration(
            server="trojan.example.com",
            port=443,
            protocol=Protocol.TROJAN,
            password="secret-password",
            id="trojan-test"
        )
        return config

    def test_init(self, validator):
        """Test validator initialization."""
        assert validator.port_range == (1, 65535)
        assert len(validator.valid_protocols) > 0
        assert Protocol.VMESS.value in validator.valid_protocols
        assert Protocol.VLESS.value in validator.valid_protocols

    def test_validate_valid_vmess_configuration(self, validator, valid_vmess_config):
        """Test validation of valid VMess configuration."""
        is_valid, errors = validator.validate_configuration(valid_vmess_config)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_valid_vless_configuration(self, validator, valid_vless_config):
        """Test validation of valid VLESS configuration."""
        is_valid, errors = validator.validate_configuration(valid_vless_config)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_valid_trojan_configuration(self, validator, valid_trojan_config):
        """Test validation of valid Trojan configuration."""
        is_valid, errors = validator.validate_configuration(valid_trojan_config)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_invalid_protocol(self, validator):
        """Test validation with invalid protocol."""
        config = VPNConfiguration(server="example.com", port=443)
        config.protocol = None
        
        is_valid, errors = validator.validate_configuration(config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Invalid protocol" in error for error in errors)

    def test_validate_invalid_server_empty(self, validator):
        """Test validation with empty server."""
        # Use mock to bypass constructor validation
        with patch('streamline_vpn.models.configuration.VPNConfiguration.__post_init__'):
            config = VPNConfiguration(server="temp", port=443)
            config.protocol = Protocol.VMESS
            config.server = ""
            config.user_id = "test-uuid"
        
        is_valid, errors = validator.validate_configuration(config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Invalid server" in error for error in errors)

    def test_validate_invalid_server_none(self, validator):
        """Test validation with None server."""
        # Use mock to bypass constructor validation
        with patch('streamline_vpn.models.configuration.VPNConfiguration.__post_init__'):
            config = VPNConfiguration(server="temp", port=443)
            config.protocol = Protocol.VMESS
            config.server = None
            config.user_id = "test-uuid"
        
        is_valid, errors = validator.validate_configuration(config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Invalid server" in error for error in errors)

    def test_validate_invalid_port_zero(self, validator):
        """Test validation with port 0."""
        # Use mock to bypass constructor validation
        with patch('streamline_vpn.models.configuration.VPNConfiguration.__post_init__'):
            config = VPNConfiguration(server="example.com", port=443)
            config.protocol = Protocol.VMESS
            config.port = 0
            config.user_id = "test-uuid"
        
        is_valid, errors = validator.validate_configuration(config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Invalid port" in error for error in errors)

    def test_validate_invalid_port_too_high(self, validator):
        """Test validation with port too high."""
        # Use mock to bypass constructor validation
        with patch('streamline_vpn.models.configuration.VPNConfiguration.__post_init__'):
            config = VPNConfiguration(server="example.com", port=443)
            config.protocol = Protocol.VMESS
            config.port = 70000
            config.user_id = "test-uuid"
        
        is_valid, errors = validator.validate_configuration(config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Invalid port" in error for error in errors)

    def test_validate_invalid_port_non_integer(self, validator):
        """Test validation with non-integer port."""
        # Use mock to bypass constructor validation
        with patch('streamline_vpn.models.configuration.VPNConfiguration.__post_init__'):
            config = VPNConfiguration(server="example.com", port=443)
            config.protocol = Protocol.VMESS
            config.port = "443"  # String instead of int
            config.user_id = "test-uuid"
        
        is_valid, errors = validator.validate_configuration(config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Invalid port" in error for error in errors)

    def test_validate_vmess_missing_user_id(self, validator):
        """Test VMess validation without user_id."""
        config = VPNConfiguration(
            server="example.com",
            port=443,
            protocol=Protocol.VMESS,
            user_id=None
        )
        
        is_valid, errors = validator.validate_configuration(config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("VMess requires user_id" in error for error in errors)

    def test_validate_vmess_with_uuid_attribute(self, validator):
        """Test VMess validation with uuid attribute instead of user_id."""
        config = VPNConfiguration(
            server="example.com",
            port=443,
            protocol=Protocol.VMESS,
            user_id=None,
            uuid="test-uuid-12345"
        )
        
        is_valid, errors = validator.validate_configuration(config)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_vless_missing_user_id(self, validator):
        """Test VLESS validation without user_id."""
        config = VPNConfiguration(
            server="example.com",
            port=443,
            protocol=Protocol.VLESS,
            user_id=None
        )
        
        is_valid, errors = validator.validate_configuration(config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("VLESS requires user_id" in error for error in errors)

    def test_validate_trojan_missing_password(self, validator):
        """Test Trojan validation without password."""
        # Use mock to bypass constructor validation
        with patch('streamline_vpn.models.configuration.VPNConfiguration.__post_init__'):
            config = VPNConfiguration(server="example.com", port=443)
            config.protocol = Protocol.TROJAN
            config.password = None
        
        is_valid, errors = validator.validate_configuration(config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("trojan requires password" in error for error in errors)

    def test_validate_shadowsocks_missing_password(self, validator):
        """Test Shadowsocks validation without password."""
        # Use mock to bypass constructor validation
        with patch('streamline_vpn.models.configuration.VPNConfiguration.__post_init__'):
            config = VPNConfiguration(server="example.com", port=1080)
            config.protocol = Protocol.SHADOWSOCKS
            config.password = None
        
        is_valid, errors = validator.validate_configuration(config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("ss requires password" in error for error in errors)

    def test_validate_shadowsocksr_missing_password(self, validator):
        """Test ShadowsocksR validation without password."""
        # Use mock to bypass constructor validation
        with patch('streamline_vpn.models.configuration.VPNConfiguration.__post_init__'):
            config = VPNConfiguration(server="example.com", port=1080)
            config.protocol = Protocol.SHADOWSOCKSR
            config.password = None
        
        is_valid, errors = validator.validate_configuration(config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("ssr requires password" in error for error in errors)

    def test_validate_with_custom_rules_min_quality(self, validator, valid_vmess_config):
        """Test validation with custom rules - minimum quality score."""
        valid_vmess_config.quality_score = 0.5
        rules = {"min_quality_score": 0.7}
        
        is_valid, errors = validator.validate_configuration(valid_vmess_config, rules)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Quality score 0.5 below minimum 0.7" in error for error in errors)

    def test_validate_with_custom_rules_quality_passes(self, validator, valid_vmess_config):
        """Test validation with custom rules - quality score passes."""
        valid_vmess_config.quality_score = 0.8
        rules = {"min_quality_score": 0.7}
        
        is_valid, errors = validator.validate_configuration(valid_vmess_config, rules)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_with_custom_rules_quality_none(self, validator, valid_vmess_config):
        """Test validation with custom rules - quality score is None."""
        valid_vmess_config.quality_score = None
        rules = {"min_quality_score": 0.7}
        
        is_valid, errors = validator.validate_configuration(valid_vmess_config, rules)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_with_custom_rules_allowed_protocols(self, validator, valid_vmess_config):
        """Test validation with custom rules - allowed protocols."""
        rules = {"allowed_protocols": ["vless", "trojan"]}
        
        is_valid, errors = validator.validate_configuration(valid_vmess_config, rules)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Protocol vmess not in allowed list" in error for error in errors)

    def test_validate_with_custom_rules_allowed_protocols_passes(self, validator, valid_vmess_config):
        """Test validation with custom rules - allowed protocols passes."""
        rules = {"allowed_protocols": ["vmess", "vless"]}
        
        is_valid, errors = validator.validate_configuration(valid_vmess_config, rules)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_with_custom_rules_server_whitelist(self, validator, valid_vmess_config):
        """Test validation with custom rules - server whitelist."""
        rules = {"server_whitelist": ["allowed.com", "trusted.net"]}
        
        is_valid, errors = validator.validate_configuration(valid_vmess_config, rules)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Server example.com not in whitelist" in error for error in errors)

    def test_validate_with_custom_rules_server_whitelist_passes(self, validator, valid_vmess_config):
        """Test validation with custom rules - server whitelist passes."""
        rules = {"server_whitelist": ["example.com", "trusted.net"]}
        
        is_valid, errors = validator.validate_configuration(valid_vmess_config, rules)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_with_custom_rules_server_blacklist(self, validator, valid_vmess_config):
        """Test validation with custom rules - server blacklist."""
        rules = {"server_blacklist": ["example.com", "blocked.net"]}
        
        is_valid, errors = validator.validate_configuration(valid_vmess_config, rules)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Server example.com is blacklisted" in error for error in errors)

    def test_validate_with_custom_rules_server_blacklist_passes(self, validator, valid_vmess_config):
        """Test validation with custom rules - server blacklist passes."""
        rules = {"server_blacklist": ["blocked.com", "banned.net"]}
        
        is_valid, errors = validator.validate_configuration(valid_vmess_config, rules)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_is_valid_server_ipv4(self, validator):
        """Test server validation with IPv4 address."""
        assert validator._is_valid_server("192.168.1.1") is True
        assert validator._is_valid_server("8.8.8.8") is True
        assert validator._is_valid_server("127.0.0.1") is True

    def test_is_valid_server_ipv6(self, validator):
        """Test server validation with IPv6 address."""
        assert validator._is_valid_server("::1") is True
        assert validator._is_valid_server("2001:db8::1") is True
        assert validator._is_valid_server("fe80::1") is True

    def test_is_valid_server_domain(self, validator):
        """Test server validation with domain names."""
        assert validator._is_valid_server("example.com") is True
        assert validator._is_valid_server("sub.example.com") is True
        assert validator._is_valid_server("test-server.example.org") is True

    def test_is_valid_server_invalid(self, validator):
        """Test server validation with invalid addresses."""
        assert validator._is_valid_server("") is False
        assert validator._is_valid_server(None) is False
        assert validator._is_valid_server("invalid..domain") is False
        assert validator._is_valid_server("invalid@domain.com") is False
        assert validator._is_valid_server("single-word") is False

    def test_is_valid_domain_valid(self, validator):
        """Test domain validation with valid domains."""
        assert validator._is_valid_domain("example.com") is True
        assert validator._is_valid_domain("sub.example.com") is True
        assert validator._is_valid_domain("test-server.example.org") is True
        assert validator._is_valid_domain("a.b") is True

    def test_is_valid_domain_invalid_empty(self, validator):
        """Test domain validation with empty domain."""
        assert validator._is_valid_domain("") is False
        assert validator._is_valid_domain(None) is False

    def test_is_valid_domain_invalid_too_long(self, validator):
        """Test domain validation with too long domain."""
        long_domain = "a" * 250 + ".com"
        assert validator._is_valid_domain(long_domain) is False

    def test_is_valid_domain_invalid_characters(self, validator):
        """Test domain validation with invalid characters."""
        assert validator._is_valid_domain("example$.com") is False
        assert validator._is_valid_domain("example@.com") is False
        assert validator._is_valid_domain("example_.com") is False

    def test_is_valid_domain_invalid_structure(self, validator):
        """Test domain validation with invalid structure."""
        assert validator._is_valid_domain("example") is False  # No TLD
        assert validator._is_valid_domain(".com") is False  # Starts with dot
        assert validator._is_valid_domain("example.") is False  # Ends with dot

    def test_is_valid_domain_invalid_part_length(self, validator):
        """Test domain validation with invalid part length."""
        long_part = "a" * 64
        assert validator._is_valid_domain(f"{long_part}.com") is False
        assert validator._is_valid_domain(".com") is False  # Empty part

    def test_is_valid_domain_invalid_hyphen_position(self, validator):
        """Test domain validation with hyphens in wrong positions."""
        assert validator._is_valid_domain("-example.com") is False
        assert validator._is_valid_domain("example-.com") is False
        assert validator._is_valid_domain("ex-ample.com") is True  # Valid hyphen position

    def test_is_valid_port_valid(self, validator):
        """Test port validation with valid ports."""
        assert validator._is_valid_port(1) is True
        assert validator._is_valid_port(80) is True
        assert validator._is_valid_port(443) is True
        assert validator._is_valid_port(8080) is True
        assert validator._is_valid_port(65535) is True

    def test_is_valid_port_invalid(self, validator):
        """Test port validation with invalid ports."""
        assert validator._is_valid_port(0) is False
        assert validator._is_valid_port(-1) is False
        assert validator._is_valid_port(65536) is False
        assert validator._is_valid_port(100000) is False
        assert validator._is_valid_port("443") is False  # String
        assert validator._is_valid_port(None) is False
        assert validator._is_valid_port(3.14) is False  # Float

    def test_validate_configurations_all_valid(self, validator):
        """Test validation of multiple configurations - all valid."""
        configs = [
            self._create_valid_config(Protocol.VMESS, "vmess1"),
            self._create_valid_config(Protocol.VLESS, "vless1"),
            self._create_valid_config(Protocol.TROJAN, "trojan1"),
        ]
        
        with patch('streamline_vpn.core.processing.validator.logger') as mock_logger:
            valid_configs = validator.validate_configurations(configs)
            
            assert len(valid_configs) == 3
            mock_logger.info.assert_called_once()
            mock_logger.debug.assert_not_called()

    def test_validate_configurations_some_invalid(self, validator):
        """Test validation of multiple configurations - some invalid."""
        valid_config = self._create_valid_config(Protocol.VMESS, "valid1")
        
        # Use mock to bypass constructor validation for invalid config
        with patch('streamline_vpn.models.configuration.VPNConfiguration.__post_init__'):
            invalid_config = VPNConfiguration(server="temp", port=443)
            invalid_config.protocol = Protocol.VMESS
            invalid_config.server = ""  # Invalid server
            invalid_config.user_id = "test-uuid"
            invalid_config.id = "invalid1"
        
        configs = [valid_config, invalid_config]
        
        with patch('streamline_vpn.core.processing.validator.logger') as mock_logger:
            valid_configs = validator.validate_configurations(configs)
            
            assert len(valid_configs) == 1
            assert valid_configs[0].id == "valid1"
            mock_logger.info.assert_called_once()
            mock_logger.debug.assert_called_once()

    def test_validate_configurations_empty_list(self, validator):
        """Test validation of empty configuration list."""
        with patch('streamline_vpn.core.processing.validator.logger') as mock_logger:
            valid_configs = validator.validate_configurations([])
            
            assert len(valid_configs) == 0
            mock_logger.info.assert_called_once()

    def test_validate_configurations_with_rules(self, validator):
        """Test validation of configurations with custom rules."""
        config = self._create_valid_config(Protocol.VMESS, "test1")
        config.quality_score = 5.0
        
        rules = {"min_quality_score": 7.0}
        
        with patch('streamline_vpn.core.processing.validator.logger') as mock_logger:
            valid_configs = validator.validate_configurations([config], rules)
            
            assert len(valid_configs) == 0
            mock_logger.debug.assert_called_once()

    def _create_valid_config(self, protocol: Protocol, config_id: str) -> VPNConfiguration:
        """Helper to create valid configuration."""
        kwargs = {
            "server": "example.com",
            "port": 443,
            "protocol": protocol,
            "id": config_id
        }
        
        if protocol in [Protocol.VMESS, Protocol.VLESS]:
            kwargs["user_id"] = f"test-uuid-{config_id}"
        elif protocol in [Protocol.TROJAN, Protocol.SHADOWSOCKS, Protocol.SHADOWSOCKSR]:
            kwargs["password"] = f"password-{config_id}"
        
        return VPNConfiguration(**kwargs)


class TestConfigurationValidatorEdgeCases:
    """Edge case tests for ConfigurationValidator."""

    @pytest.fixture
    def validator(self):
        """Create ConfigurationValidator instance."""
        return ConfigurationValidator()

    def test_validate_multiple_errors(self, validator):
        """Test configuration with multiple validation errors."""
        # Use mock to bypass constructor validation
        with patch('streamline_vpn.models.configuration.VPNConfiguration.__post_init__'):
            config = VPNConfiguration(server="temp", port=443)
            config.protocol = None  # Invalid protocol
            config.server = ""  # Invalid server
            config.port = 0  # Invalid port
        
        is_valid, errors = validator.validate_configuration(config)
        
        assert is_valid is False
        assert len(errors) >= 3  # Should have multiple errors
        assert any("Invalid protocol" in error for error in errors)
        assert any("Invalid server" in error for error in errors)
        assert any("Invalid port" in error for error in errors)

    def test_validate_with_complex_custom_rules(self, validator):
        """Test validation with complex custom rules."""
        config = VPNConfiguration(
            server="blocked.com",
            port=443,
            protocol=Protocol.VMESS,
            user_id="test-uuid",
            quality_score=0.3  # Valid quality score between 0 and 1
        )
        
        rules = {
            "min_quality_score": 0.5,  # Valid quality score between 0 and 1
            "allowed_protocols": ["vless"],
            "server_blacklist": ["blocked.com"],
            "server_whitelist": ["allowed.com"]
        }
        
        is_valid, errors = validator.validate_configuration(config, rules)
        
        assert is_valid is False
        assert len(errors) >= 3  # Multiple rule violations
        assert any("Quality score 0.3 below minimum 0.5" in error for error in errors)
        assert any("not in allowed list" in error for error in errors)
        assert any("is blacklisted" in error for error in errors)

    def test_validate_domain_edge_cases(self, validator):
        """Test domain validation edge cases."""
        # Test maximum valid length
        max_valid_domain = "a" * 61 + "." + "b" * 61 + ".com"
        assert validator._is_valid_domain(max_valid_domain) is True
        
        # Test exactly 253 characters (maximum allowed)
        # Calculate parts to get exactly 253 characters including dots
        parts = ["a" * 63, "b" * 63, "c" * 63, "d" * 57]  # 63+1+63+1+63+1+57 = 249 chars
        max_length_domain = ".".join(parts)
        actual_length = len(max_length_domain)
        # Adjust if needed to get exactly 253
        if actual_length < 253:
            parts[-1] = "d" * (57 + (253 - actual_length))
            max_length_domain = ".".join(parts)
        
        assert len(max_length_domain) <= 253
        assert validator._is_valid_domain(max_length_domain) is True
        
        # Test 254 characters (too long)
        too_long_domain = "a" * 250 + ".com"  # 254 characters
        assert len(too_long_domain) == 254
        assert validator._is_valid_domain(too_long_domain) is False

    def test_validate_server_with_special_ips(self, validator):
        """Test server validation with special IP addresses."""
        # Test loopback addresses
        assert validator._is_valid_server("127.0.0.1") is True
        assert validator._is_valid_server("::1") is True
        
        # Test private network addresses
        assert validator._is_valid_server("192.168.1.1") is True
        assert validator._is_valid_server("10.0.0.1") is True
        assert validator._is_valid_server("172.16.0.1") is True
        
        # Test broadcast address
        assert validator._is_valid_server("255.255.255.255") is True
        
        # Test zero address
        assert validator._is_valid_server("0.0.0.0") is True

    def test_validate_port_boundary_values(self, validator):
        """Test port validation with boundary values."""
        assert validator._is_valid_port(1) is True  # Minimum valid
        assert validator._is_valid_port(65535) is True  # Maximum valid
        assert validator._is_valid_port(0) is False  # Below minimum
        assert validator._is_valid_port(65536) is False  # Above maximum

    def test_validate_configuration_with_none_rules(self, validator):
        """Test validation with None rules."""
        config = VPNConfiguration(
            server="example.com",
            port=443,
            protocol=Protocol.VMESS,
            user_id="test-uuid"
        )
        
        is_valid, errors = validator.validate_configuration(config, None)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_configuration_with_empty_rules(self, validator):
        """Test validation with empty rules dictionary."""
        config = VPNConfiguration(
            server="example.com",
            port=443,
            protocol=Protocol.VMESS,
            user_id="test-uuid"
        )
        
        is_valid, errors = validator.validate_configuration(config, {})
        
        assert is_valid is True
        assert len(errors) == 0

    def test_protocol_specific_validation_coverage(self, validator):
        """Test protocol-specific validation for all supported protocols."""
        protocols_requiring_password = [
            Protocol.TROJAN,
            Protocol.SHADOWSOCKS,
            Protocol.SHADOWSOCKSR
        ]
        
        for protocol in protocols_requiring_password:
            # Use mock to bypass constructor validation
            with patch('streamline_vpn.models.configuration.VPNConfiguration.__post_init__'):
                config = VPNConfiguration(server="example.com", port=443)
                config.protocol = protocol
                config.password = None
            
            is_valid, errors = validator.validate_configuration(config)
            
            assert is_valid is False
            assert any(f"{protocol.value} requires password" in error for error in errors)

    def test_validate_with_uuid_fallback(self, validator):
        """Test validation with uuid attribute as fallback for user_id."""
        for protocol in [Protocol.VMESS, Protocol.VLESS]:
            # Test without uuid - should fail
            config = VPNConfiguration(
                server="example.com",
                port=443,
                protocol=protocol,
                user_id=None
            )
            is_valid, errors = validator.validate_configuration(config)
            assert is_valid is False
            
            # Test with uuid attribute - should pass
            config_with_uuid = VPNConfiguration(
                server="example.com",
                port=443,
                protocol=protocol,
                user_id=None,
                uuid="test-uuid-12345"
            )
            is_valid, errors = validator.validate_configuration(config_with_uuid)
            assert is_valid is True
