"""Tests for merger utils module."""

import base64
import json
import pytest
from unittest.mock import patch, MagicMock

from streamline_vpn.merger.utils import (
    print_public_source_warning,
    is_valid_config,
    parse_configs_from_text,
    choose_proxy
)


class TestPrintPublicSourceWarning:
    """Test cases for print_public_source_warning function."""

    def test_print_warning_first_time(self):
        """Test that warning is printed on first call."""
        # Reset the global warning flag
        import streamline_vpn.merger.utils as utils_module
        utils_module._warning_printed = False
        
        with patch('builtins.print') as mock_print:
            print_public_source_warning()
            
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "WARNING" in call_args
            assert "public sources" in call_args
            assert "Use at your own risk" in call_args

    def test_print_warning_second_time(self):
        """Test that warning is not printed on subsequent calls."""
        # Ensure warning was already printed
        import streamline_vpn.merger.utils as utils_module
        utils_module._warning_printed = True
        
        with patch('builtins.print') as mock_print:
            print_public_source_warning()
            
            mock_print.assert_not_called()

    def test_warning_flag_persistence(self):
        """Test that warning flag persists across calls."""
        import streamline_vpn.merger.utils as utils_module
        utils_module._warning_printed = False
        
        with patch('builtins.print'):
            print_public_source_warning()
            assert utils_module._warning_printed is True
            
            print_public_source_warning()
            assert utils_module._warning_printed is True


class TestIsValidConfig:
    """Test cases for is_valid_config function."""

    def test_warp_protocol_rejected(self):
        """Test that warp:// protocol is rejected."""
        assert is_valid_config("warp://some-config") is False

    def test_valid_vmess_config(self):
        """Test valid VMess configuration."""
        vmess_data = {
            "v": "2",
            "ps": "test",
            "add": "example.com",
            "port": "443",
            "id": "test-uuid",
            "aid": "0",
            "net": "ws",
            "type": "none",
            "host": "",
            "path": "/",
            "tls": "tls"
        }
        encoded = base64.b64encode(json.dumps(vmess_data).encode()).decode()
        vmess_url = f"vmess://{encoded}"
        
        assert is_valid_config(vmess_url) is True

    def test_invalid_vmess_config_bad_json(self):
        """Test invalid VMess config with bad JSON."""
        invalid_json = base64.b64encode(b"not json").decode()
        vmess_url = f"vmess://{invalid_json}"
        
        with patch('logging.warning') as mock_warning:
            assert is_valid_config(vmess_url) is False
            mock_warning.assert_called_once()

    def test_invalid_vmess_config_bad_base64(self):
        """Test invalid VMess config with bad base64."""
        vmess_url = "vmess://invalid_base64!"
        
        with patch('logging.warning') as mock_warning:
            assert is_valid_config(vmess_url) is False
            mock_warning.assert_called_once()

    def test_valid_ssr_config(self):
        """Test valid SSR configuration."""
        # Create valid SSR config: host:port:protocol:method:obfs:password_base64
        ssr_data = "example.com:443:origin:aes-256-cfb:plain:cGFzc3dvcmQ"
        encoded = base64.urlsafe_b64encode(ssr_data.encode()).decode().rstrip('=')
        ssr_url = f"ssr://{encoded}"
        
        assert is_valid_config(ssr_url) is True

    def test_invalid_ssr_config_bad_encoding(self):
        """Test invalid SSR config with bad encoding."""
        ssr_url = "ssr://invalid_base64!"
        
        with patch('logging.warning') as mock_warning:
            assert is_valid_config(ssr_url) is False
            mock_warning.assert_called_once()

    def test_invalid_ssr_config_no_port(self):
        """Test invalid SSR config without port."""
        ssr_data = "example.com"  # No port
        encoded = base64.urlsafe_b64encode(ssr_data.encode()).decode()
        ssr_url = f"ssr://{encoded}"
        
        assert is_valid_config(ssr_url) is False

    def test_invalid_ssr_config_no_host(self):
        """Test invalid SSR config without host."""
        ssr_data = ":443:origin:aes-256-cfb:plain:cGFzc3dvcmQ"  # Empty host
        encoded = base64.urlsafe_b64encode(ssr_data.encode()).decode()
        ssr_url = f"ssr://{encoded}"
        
        assert is_valid_config(ssr_url) is False

    def test_valid_vless_config(self):
        """Test valid VLESS configuration."""
        vless_url = "vless://uuid@example.com:443?security=tls&type=ws&path=/path"
        assert is_valid_config(vless_url) is True

    def test_invalid_vless_config_no_at_symbol(self):
        """Test invalid VLESS config without @ symbol."""
        vless_url = "vless://uuid-example.com:443"
        assert is_valid_config(vless_url) is False

    def test_invalid_vless_config_no_port(self):
        """Test invalid VLESS config without port."""
        vless_url = "vless://uuid@example.com"
        assert is_valid_config(vless_url) is False

    def test_valid_trojan_config(self):
        """Test valid Trojan configuration."""
        trojan_url = "trojan://password@example.com:443"
        assert is_valid_config(trojan_url) is True

    def test_valid_ss_config(self):
        """Test valid Shadowsocks configuration."""
        ss_url = "ss://YWVzLTI1Ni1nY206cGFzc3dvcmQ@example.com:443"
        assert is_valid_config(ss_url) is True

    def test_valid_http_config(self):
        """Test valid HTTP configuration."""
        http_url = "http://example.com:8080"
        assert is_valid_config(http_url) is True

    def test_invalid_http_config_no_port(self):
        """Test invalid HTTP config without port."""
        http_url = "http://example.com"
        assert is_valid_config(http_url) is False

    def test_valid_socks5_config(self):
        """Test valid SOCKS5 configuration."""
        socks_url = "socks5://example.com:1080"
        assert is_valid_config(socks_url) is True

    def test_valid_wireguard_config(self):
        """Test valid WireGuard configuration."""
        wg_url = "wireguard://config-data"
        assert is_valid_config(wg_url) is True

    def test_invalid_wireguard_config_empty(self):
        """Test invalid WireGuard config with empty data."""
        wg_url = "wireguard://"
        assert is_valid_config(wg_url) is False

    def test_unknown_protocol_with_data(self):
        """Test unknown protocol with data."""
        unknown_url = "unknown://some-data"
        assert is_valid_config(unknown_url) is True

    def test_unknown_protocol_empty(self):
        """Test unknown protocol with empty data."""
        unknown_url = "unknown://"
        assert is_valid_config(unknown_url) is False

    def test_config_with_query_params(self):
        """Test config with query parameters."""
        vless_url = "vless://uuid@example.com:443?security=tls&type=ws&path=/path#fragment"
        assert is_valid_config(vless_url) is True

    def test_config_with_fragment_only(self):
        """Test config with fragment only."""
        vless_url = "vless://uuid@example.com:443#fragment"
        assert is_valid_config(vless_url) is True

    def test_case_insensitive_protocol(self):
        """Test case insensitive protocol handling."""
        vmess_data = {"v": "2", "add": "example.com", "port": "443"}
        encoded = base64.b64encode(json.dumps(vmess_data).encode()).decode()
        vmess_url = f"VMESS://{encoded}"
        
        assert is_valid_config(vmess_url) is True


class TestParseConfigsFromText:
    """Test cases for parse_configs_from_text function."""

    def test_parse_single_config(self):
        """Test parsing single config from text."""
        text = "Here is a config: vmess://eyJ2IjoiMiIsImFkZCI6ImV4YW1wbGUuY29tIn0="
        
        with patch('streamline_vpn.merger.utils.PROTOCOL_RE') as mock_regex:
            mock_regex.findall.return_value = ["vmess://eyJ2IjoiMiIsImFkZCI6ImV4YW1wbGUuY29tIn0="]
            
            configs = parse_configs_from_text(text)
            
            assert len(configs) == 1
            assert "vmess://eyJ2IjoiMiIsImFkZCI6ImV4YW1wbGUuY29tIn0=" in configs

    def test_parse_multiple_configs(self):
        """Test parsing multiple configs from text."""
        text = """
        Config 1: vmess://config1
        Config 2: vless://config2
        Config 3: trojan://config3
        """
        
        with patch('streamline_vpn.merger.utils.PROTOCOL_RE') as mock_regex:
            # Create a function to handle multiple calls
            call_count = 0
            def mock_findall_side_effect(line):
                nonlocal call_count
                call_count += 1
                if "Config 1" in line:
                    return ["vmess://config1"]
                elif "Config 2" in line:
                    return ["vless://config2"]
                elif "Config 3" in line:
                    return ["trojan://config3"]
                else:
                    return []
            
            mock_regex.findall.side_effect = mock_findall_side_effect
            
            configs = parse_configs_from_text(text)
            
            assert len(configs) == 3
            assert "vmess://config1" in configs
            assert "vless://config2" in configs
            assert "trojan://config3" in configs

    def test_parse_base64_encoded_configs(self):
        """Test parsing base64 encoded configs."""
        # Create base64 encoded content with configs
        config_text = "vmess://config1\nvless://config2"
        encoded_text = base64.urlsafe_b64encode(config_text.encode()).decode()
        
        text = f"Base64 content:\n{encoded_text}"
        
        with patch('streamline_vpn.merger.utils.PROTOCOL_RE') as mock_regex:
            with patch('streamline_vpn.merger.utils.BASE64_RE') as mock_base64_regex:
                # Mock findall calls - first for each line, then for decoded content
                call_count = 0
                def mock_findall_side_effect(line):
                    nonlocal call_count
                    call_count += 1
                    if call_count <= 2:  # First two calls for the lines themselves
                        return []
                    else:  # Call for decoded content
                        return ["vmess://config1", "vless://config2"]
                
                mock_regex.findall.side_effect = mock_findall_side_effect
                mock_base64_regex.match.side_effect = [None, True]  # First line no match, second line matches
                
                configs = parse_configs_from_text(text)
                
                assert len(configs) == 2
                assert "vmess://config1" in configs
                assert "vless://config2" in configs

    def test_parse_oversized_base64_line(self):
        """Test parsing oversized base64 line."""
        # Create oversized base64 line
        large_content = "x" * 10000
        encoded_text = base64.urlsafe_b64encode(large_content.encode()).decode()
        
        text = f"Large content:\n{encoded_text}"
        
        with patch('streamline_vpn.merger.utils.PROTOCOL_RE') as mock_regex:
            with patch('streamline_vpn.merger.utils.BASE64_RE') as mock_base64_regex:
                with patch('streamline_vpn.merger.utils.MAX_DECODE_SIZE', 1000):
                    with patch('logging.debug') as mock_debug:
                        mock_regex.findall.return_value = []
                        mock_base64_regex.match.side_effect = [None, True]
                        
                        configs = parse_configs_from_text(text)
                        
                        assert len(configs) == 0
                        mock_debug.assert_called_once()
                        assert "Skipping oversized base64 line" in mock_debug.call_args[0][0]

    def test_parse_invalid_base64_line(self):
        """Test parsing invalid base64 line."""
        text = "Invalid base64:\ninvalid_base64_content!"
        
        with patch('streamline_vpn.merger.utils.PROTOCOL_RE') as mock_regex:
            with patch('streamline_vpn.merger.utils.BASE64_RE') as mock_base64_regex:
                with patch('logging.debug') as mock_debug:
                    mock_regex.findall.return_value = []
                    mock_base64_regex.match.side_effect = [None, True]
                    
                    configs = parse_configs_from_text(text)
                    
                    assert len(configs) == 0
                    mock_debug.assert_called_once()
                    assert "Failed to decode base64 line" in mock_debug.call_args[0][0]

    def test_parse_empty_text(self):
        """Test parsing empty text."""
        configs = parse_configs_from_text("")
        assert len(configs) == 0

    def test_parse_whitespace_only_text(self):
        """Test parsing text with only whitespace."""
        text = "   \n\t  \n   "
        configs = parse_configs_from_text(text)
        assert len(configs) == 0

    def test_parse_mixed_content(self):
        """Test parsing mixed content with configs and base64."""
        config_text = "vmess://inline-config"
        encoded_text = base64.urlsafe_b64encode(b"vless://encoded-config").decode()
        
        text = f"""
        Some text here
        {config_text}
        More text
        {encoded_text}
        End text
        """
        
        with patch('streamline_vpn.merger.utils.PROTOCOL_RE') as mock_regex:
            with patch('streamline_vpn.merger.utils.BASE64_RE') as mock_base64_regex:
                # Mock responses for each line - need to handle multiple calls
                call_count = 0
                def mock_findall_side_effect(line):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:  # "Some text here"
                        return []
                    elif call_count == 2:  # config line
                        return ["vmess://inline-config"]
                    elif call_count == 3:  # "More text"
                        return []
                    elif call_count == 4:  # base64 line (no direct match)
                        return []
                    elif call_count == 5:  # decoded base64 content
                        return ["vless://encoded-config"]
                    else:  # "End text"
                        return []
                
                mock_regex.findall.side_effect = mock_findall_side_effect
                mock_base64_regex.match.side_effect = [
                    None, None, None, True, None  # Only base64 line matches
                ]
                
                configs = parse_configs_from_text(text)
                
                assert len(configs) == 2
                assert "vmess://inline-config" in configs
                assert "vless://encoded-config" in configs

    def test_parse_unicode_decode_error(self):
        """Test parsing with unicode decode error in base64."""
        # Create base64 that will cause unicode decode error
        invalid_bytes = b'\xff\xfe\xfd'
        encoded_text = base64.urlsafe_b64encode(invalid_bytes).decode()
        
        text = f"Invalid unicode:\n{encoded_text}"
        
        with patch('streamline_vpn.merger.utils.PROTOCOL_RE') as mock_regex:
            with patch('streamline_vpn.merger.utils.BASE64_RE') as mock_base64_regex:
                with patch('logging.debug') as mock_debug:
                    mock_regex.findall.return_value = []
                    mock_base64_regex.match.side_effect = [None, True]
                    
                    configs = parse_configs_from_text(text)
                    
                    assert len(configs) == 0
                    mock_debug.assert_called_once()


class TestChooseProxy:
    """Test cases for choose_proxy function."""

    def test_choose_socks_proxy_when_both_available(self):
        """Test that SOCKS proxy is chosen when both are available."""
        mock_cfg = MagicMock()
        mock_cfg.SOCKS_PROXY = "socks5://localhost:1080"
        mock_cfg.HTTP_PROXY = "http://localhost:8080"
        
        result = choose_proxy(mock_cfg)
        
        assert result == "socks5://localhost:1080"

    def test_choose_http_proxy_when_socks_unavailable(self):
        """Test that HTTP proxy is chosen when SOCKS is unavailable."""
        mock_cfg = MagicMock()
        mock_cfg.SOCKS_PROXY = None
        mock_cfg.HTTP_PROXY = "http://localhost:8080"
        
        result = choose_proxy(mock_cfg)
        
        assert result == "http://localhost:8080"

    def test_choose_none_when_both_unavailable(self):
        """Test that None is returned when both proxies are unavailable."""
        mock_cfg = MagicMock()
        mock_cfg.SOCKS_PROXY = None
        mock_cfg.HTTP_PROXY = None
        
        result = choose_proxy(mock_cfg)
        
        assert result is None

    def test_choose_socks_proxy_when_http_empty_string(self):
        """Test SOCKS proxy chosen when HTTP is empty string."""
        mock_cfg = MagicMock()
        mock_cfg.SOCKS_PROXY = "socks5://localhost:1080"
        mock_cfg.HTTP_PROXY = ""
        
        result = choose_proxy(mock_cfg)
        
        assert result == "socks5://localhost:1080"

    def test_choose_http_proxy_when_socks_empty_string(self):
        """Test HTTP proxy chosen when SOCKS is empty string."""
        mock_cfg = MagicMock()
        mock_cfg.SOCKS_PROXY = ""
        mock_cfg.HTTP_PROXY = "http://localhost:8080"
        
        result = choose_proxy(mock_cfg)
        
        assert result == "http://localhost:8080"


class TestUtilsEdgeCases:
    """Edge case tests for utils module."""

    def test_vmess_config_with_padding_edge_case(self):
        """Test VMess config with edge case padding."""
        # Create JSON that results in base64 needing different padding
        vmess_data = {"v": "2", "add": "test.com", "port": "443", "id": "a"}
        json_str = json.dumps(vmess_data, separators=(',', ':'))  # Compact JSON
        encoded = base64.b64encode(json_str.encode()).decode().rstrip('=')
        vmess_url = f"vmess://{encoded}"
        
        assert is_valid_config(vmess_url) is True

    def test_ssr_config_with_complex_path(self):
        """Test SSR config with complex path structure."""
        ssr_data = "example.com:443:origin:aes-256-cfb:plain:cGFzc3dvcmQ/path/to/resource"
        encoded = base64.urlsafe_b64encode(ssr_data.encode()).decode()
        ssr_url = f"ssr://{encoded}"
        
        assert is_valid_config(ssr_url) is True

    def test_protocol_with_multiple_at_symbols(self):
        """Test protocol handling with multiple @ symbols."""
        config_url = "trojan://user@pass@example.com:443"
        assert is_valid_config(config_url) is True

    def test_base64_line_with_exact_max_size(self):
        """Test base64 line with exactly max decode size."""
        content = "x" * 100  # Adjust based on MAX_DECODE_SIZE
        encoded_text = base64.urlsafe_b64encode(content.encode()).decode()
        
        with patch('streamline_vpn.merger.utils.MAX_DECODE_SIZE', len(encoded_text)):
            with patch('streamline_vpn.merger.utils.PROTOCOL_RE') as mock_regex:
                with patch('streamline_vpn.merger.utils.BASE64_RE') as mock_base64_regex:
                    mock_regex.findall.side_effect = [[], []]
                    mock_base64_regex.match.return_value = True
                    
                    configs = parse_configs_from_text(encoded_text)
                    
                    # Should process the line since it's exactly at the limit
                    assert len(configs) == 0  # No configs in the decoded content
