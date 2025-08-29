from __future__ import annotations

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile
import os

from vpn_merger.sources.validator import SourceValidator
from vpn_merger.discovery.intelligent_discovery import IntelligentSourceDiscovery
from vpn_merger.services.reliability import CircuitBreaker, ExponentialBackoff
from vpn_merger.services.rate_limiter import PerHostRateLimiter


class TestSourceValidatorEnhanced:
    """Enhanced tests for SourceValidator."""
    
    @pytest.mark.asyncio
    async def test_validate_source_network_timeout(self):
        validator = SourceValidator()
        
        # Mock network timeout
        with patch('aiohttp.ClientSession.get', side_effect=asyncio.TimeoutError("Request timeout")):
            result = await validator.validate_source("https://example.com/timeout")
            
            assert result["accessible"] is False
            assert "error" in result
            assert "timeout" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_validate_source_http_error(self):
        validator = SourceValidator()
        
        # Mock HTTP error response
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = AsyncMock(return_value="Not Found")
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            result = await validator.validate_source("https://example.com/notfound")
            
            assert result["accessible"] is False
            assert result["response_time"] is not None
            assert result["content_type"] == "text/plain"
    
    @pytest.mark.asyncio
    async def test_validate_source_large_content(self):
        validator = SourceValidator()
        
        # Generate large content
        large_content = "vmess://test\n" * 10000  # 10k configs
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = AsyncMock(return_value=large_content)
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            result = await validator.validate_source("https://example.com/large")
            
            assert result["accessible"] is True
            assert result["estimated_configs"] >= 10000
            assert result["size_bytes"] > 100000
            assert result["reliability_score"] > 0.5
    
    def test_estimate_configs_mixed_protocols(self):
        validator = SourceValidator()
        
        content = """
        vmess://config1
        vless://config2
        trojan://config3
        ss://config4
        invalid_line
        vmess://config5
        """
        
        count = validator._estimate_configs(content)
        assert count == 5
    
    def test_detect_protocols_all_types(self):
        validator = SourceValidator()
        
        content = """
        vmess://config1
        vless://config2
        trojan://config3
        ss://config4
        ssr://config5
        hysteria://config6
        hysteria2://config7
        tuic://config8
        """
        
        protocols = validator._detect_protocols(content)
        expected = {"vmess", "vless", "trojan", "shadowsocks", "shadowsocksr", "hysteria", "hysteria2", "tuic"}
        
        assert set(protocols) == expected
    
    def test_calculate_reliability_historical_data(self):
        validator = SourceValidator()
        
        # Add historical data
        validator.health_history["https://example.com"] = [True, True, False, True, True]
        
        # Test with good response
        result = {
            "accessible": True,
            "response_time": 1.5,
            "estimated_configs": 500,
            "protocols_found": ["vmess", "vless", "trojan"]
        }
        
        score = validator._calculate_reliability("https://example.com", result)
        
        # Should be high due to good current metrics and historical success
        assert score > 0.7


class TestIntelligentDiscoveryEnhanced:
    """Enhanced tests for IntelligentSourceDiscovery."""
    
    @pytest.mark.asyncio
    async def test_discover_github_sources_no_token(self):
        discovery = IntelligentSourceDiscovery()
        
        # Mock GitHub API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "items": [
                {
                    "repository": {"full_name": "user/repo1"},
                    "path": "sub/config.txt"
                },
                {
                    "repository": {"full_name": "user/repo2"},
                    "path": "subscription/list.txt"
                }
            ]
        })
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            sources = await discovery.discover_github_sources()
            
            # Should discover sources and convert to raw URLs
            assert len(sources) > 0
            assert any("raw.githubusercontent.com" in url for url in sources)
    
    @pytest.mark.asyncio
    async def test_discover_github_sources_with_token(self):
        discovery = IntelligentSourceDiscovery()
        
        # Mock environment with token
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "items": [
                    {
                        "repository": {"full_name": "user/repo1"},
                        "path": "sub/config.txt"
                    }
                ]
            })
            
            with patch('aiohttp.ClientSession.get', return_value=mock_response):
                sources = await discovery.discover_github_sources()
                assert len(sources) > 0
    
    @pytest.mark.asyncio
    async def test_discover_github_sources_api_error(self):
        discovery = IntelligentSourceDiscovery()
        
        # Mock API error
        with patch('aiohttp.ClientSession.get', side_effect=Exception("API Error")):
            sources = await discovery.discover_github_sources()
            
            # Should return empty list on error
            assert sources == []
    
    def test_plausible_url_filtering(self):
        discovery = IntelligentSourceDiscovery()
        
        # Valid URLs
        assert discovery._plausible("https://raw.githubusercontent.com/user/repo/main/sub.txt")
        assert discovery._plausible("https://raw.githubusercontent.com/user/repo/main/mix.txt")
        assert discovery._plausible("https://raw.githubusercontent.com/user/repo/main/v2ray.txt")
        
        # Invalid URLs
        assert not discovery._plausible("https://raw.githubusercontent.com/user/repo/main/LICENSE")
        assert not discovery._plausible("https://raw.githubusercontent.com/user/repo/main/README.md")
        assert not discovery._plausible("https://raw.githubusercontent.com/user/repo/main/rules.txt")


class TestReliabilityServicesEnhanced:
    """Enhanced tests for reliability services."""
    
    def test_circuit_breaker_multiple_keys(self):
        cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.01)
        
        # Test multiple services
        assert not cb.is_open("service1")
        assert not cb.is_open("service2")
        
        # Fail service1
        cb.record_failure("service1")
        cb.record_failure("service1")
        assert cb.is_open("service1")
        
        # service2 should still be closed
        assert not cb.is_open("service2")
    
    def test_circuit_breaker_reset_after_cooldown(self):
        cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.01)
        
        # Open circuit
        cb.record_failure("test")
        cb.record_failure("test")
        assert cb.is_open("test")
        
        # Wait for cooldown
        import time
        time.sleep(0.02)
        
        # Should be closed again
        assert not cb.is_open("test")
    
    def test_exponential_backoff_custom_parameters(self):
        eb = ExponentialBackoff(base=2.0, max_delay=100.0)
        
        delays = [eb.get_delay(i) for i in range(10)]
        
        # Should grow exponentially
        for i in range(1, len(delays)):
            assert delays[i] >= delays[i-1]
        
        # Should not exceed max
        assert max(delays) <= 100.0
    
    @pytest.mark.asyncio
    async def test_rate_limiter_multiple_hosts(self):
        limiter = PerHostRateLimiter(per_host_rate=2.0, per_host_capacity=2)
        
        # Test different hosts
        await limiter.acquire("host1.com")
        await limiter.acquire("host1.com")
        
        await limiter.acquire("host2.com")
        await limiter.acquire("host2.com")
        
        # Both should be at capacity
        start_time = asyncio.get_event_loop().time()
        await limiter.acquire("host1.com")
        await limiter.acquire("host2.com")
        end_time = asyncio.get_event_loop().time()
        
        # Should have waited
        assert end_time - start_time >= 0.4


class TestIntegrationScenarios:
    """Integration test scenarios."""
    
    @pytest.mark.asyncio
    async def test_source_validation_pipeline(self):
        """Test complete source validation pipeline."""
        validator = SourceValidator()
        
        # Mock multiple sources
        sources = [
            "https://example.com/good",
            "https://example.com/slow",
            "https://example.com/bad",
            "https://example.com/timeout"
        ]
        
        # Mock responses
        responses = [
            (200, "vmess://config1\nvless://config2", 0.1),  # Good
            (200, "vmess://config3", 2.0),                   # Slow
            (500, "Server Error", 0.1),                      # Bad
            (Exception("Timeout"), None, 0.1)                # Timeout
        ]
        
        results = []
        for source, (status, content, delay) in zip(sources, responses):
            if isinstance(status, Exception):
                # Mock exception
                with patch('aiohttp.ClientSession.get', side_effect=status):
                    result = await validator.validate_source(source)
            else:
                # Mock response
                mock_response = AsyncMock()
                mock_response.status = status
                mock_response.headers = {"Content-Type": "text/plain"}
                mock_response.text = AsyncMock(return_value=content)
                
                with patch('aiohttp.ClientSession.get', return_value=mock_response):
                    result = await validator.validate_source(source)
            
            results.append(result)
        
        # Verify results
        assert results[0]["accessible"] is True
        assert results[0]["reliability_score"] > 0.5
        
        assert results[1]["accessible"] is True
        assert results[1]["reliability_score"] < results[0]["reliability_score"]
        
        assert results[2]["accessible"] is False
        
        assert results[3]["accessible"] is False
        assert "error" in results[3]
    
    @pytest.mark.asyncio
    async def test_discovery_and_validation_integration(self):
        """Test discovery and validation working together."""
        discovery = IntelligentSourceDiscovery()
        validator = SourceValidator()
        
        # Mock discovery
        mock_discovery_response = AsyncMock()
        mock_discovery_response.status = 200
        mock_discovery_response.json = AsyncMock(return_value={
            "items": [
                {
                    "repository": {"full_name": "user/repo1"},
                    "path": "sub/config.txt"
                }
            ]
        })
        
        with patch('aiohttp.ClientSession.get', return_value=mock_discovery_response):
            sources = await discovery.discover_github_sources()
            
            # Mock validation for discovered sources
            mock_validation_response = AsyncMock()
            mock_validation_response.status = 200
            mock_validation_response.headers = {"Content-Type": "text/plain"}
            mock_validation_response.text = AsyncMock(return_value="vmess://config1\nvless://config2")
            
            with patch('aiohttp.ClientSession.get', return_value=mock_validation_response):
                for source in sources[:3]:  # Test first 3
                    result = await validator.validate_source(source)
                    assert result["accessible"] is True
                    assert result["estimated_configs"] > 0


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_strings_and_none_values(self):
        validator = SourceValidator()
        
        # Test with empty content
        assert validator._estimate_configs("") == 0
        assert validator._detect_protocols("") == []
        
        # Test with None content
        assert validator._estimate_configs(None) == 0
        assert validator._detect_protocols(None) == []
    
    def test_malformed_protocol_strings(self):
        validator = SourceValidator()
        
        content = """
        vmess://
        vless://
        trojan://
        ss://
        invalid_protocol
        vmess://valid_config
        """
        
        count = validator._estimate_configs(content)
        assert count == 1  # Only valid config should count
        
        protocols = validator._detect_protocols(content)
        assert "vmess" in protocols
        assert "vless" in protocols
        assert "trojan" in protocols
        assert "shadowsocks" in protocols
    
    @pytest.mark.asyncio
    async def test_concurrent_validation(self):
        """Test concurrent source validation."""
        validator = SourceValidator()
        
        sources = [f"https://example{i}.com/config" for i in range(10)]
        
        # Mock all responses
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = AsyncMock(return_value="vmess://config")
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            # Run validations concurrently
            tasks = [validator.validate_source(source) for source in sources]
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            assert len(results) == 10
            for result in results:
                assert result["accessible"] is True
                assert result["reliability_score"] > 0

    @pytest.mark.asyncio
    async def test_comprehensive_protocol_detection(self):
        """Test detection of all supported protocols including enhanced patterns."""
        validator = SourceValidator()
        
        # Test URL scheme protocols
        url_scheme_content = """
        vmess://eyJhZGQiOiJleGFtcGxlLmNvbSIsInBvcnQiOiI0NDMiLCJpZCI6IjEyMzQ1Njc4LTkwYWItMTJmMy1hNmM1LTQ2ODFhYWFhYWFhYSIsImFpZCI6IjAiLCJuZXR3b3JrIjoid3MiLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoidGxzIn0=
        vless://12345678-90ab-12f3-a6c5-4681aaaaaaaa@example.com:443?security=tls&type=ws
        trojan://password@example.com:443?security=tls
        ss://YWVzLTI1Ni1nY206cGFzc3dvcmQ=@example.com:8388
        ssr://example.com:8388:origin:chacha20:plain:password/?obfsparam=&protoparam=&remarks=
        hysteria://example.com:443?protocol=udp&upmbps=100&downmbps=100&alpn=h3
        hysteria2://password@example.com:443?insecure=1&sni=example.com
        tuic://example.com:443?token=password&udp_relay_mode=native&congestion_control=bbr&alpn=h3
        wg://example.com:51820?public_key=publickey&private_key=privatekey&address=10.0.0.2/24
        openvpn://example.com:1194?config=client.ovpn
        outline://example.com:12345?access_key=accesskey
        brook://example.com:9999?password=password
        naive://example.com:443?username=user&password=pass
        snell://example.com:12345?psk=password
        sspanel://example.com:12345?token=token
        clash://install-config?url=https://example.com/config.yaml
        surge:///install-config?url=https://example.com/config.conf
        """
        
        result = validator._detect_protocols(url_scheme_content)
        expected_protocols = {
            "vmess", "vless", "trojan", "shadowsocks", "shadowsocksr", 
            "hysteria", "hysteria2", "tuic", "wireguard", "openvpn", 
            "outline", "brook", "naive", "snell", "sspanel", "clash", "surge"
        }
        assert set(result) == expected_protocols
        
        # Test enhanced pattern detection for protocols without URL schemes
        wireguard_content = """
        [Interface]
        PrivateKey = private_key_here
        Address = 10.0.0.2/24
        DNS = 8.8.8.8
        
        [Peer]
        PublicKey = public_key_here
        Endpoint = example.com:51820
        AllowedIPs = 0.0.0.0/0
        """
        
        result = validator._detect_protocols(wireguard_content)
        assert "wireguard" in result
        
        openvpn_content = """
        client
        dev tun
        proto udp
        remote example.com 1194
        resolv-retry infinite
        nobind
        persist-key
        persist-tun
        <ca>
        -----BEGIN CERTIFICATE-----
        certificate_content_here
        -----END CERTIFICATE-----
        </ca>
        <cert>
        -----BEGIN CERTIFICATE-----
        client_cert_here
        -----END CERTIFICATE-----
        </cert>
        <key>
        -----BEGIN PRIVATE KEY-----
        private_key_here
        -----END PRIVATE KEY-----
        </key>
        """
        
        result = validator._detect_protocols(openvpn_content)
        assert "openvpn" in result
        
        clash_content = """
        port: 7890
        socks-port: 7891
        mixed-port: 7892
        allow-lan: true
        mode: rule
        log-level: info
        
        proxies:
          - name: "vmess"
            type: vmess
            server: example.com
            port: 443
            uuid: 12345678-90ab-12f3-a6c5-4681aaaaaaaa
            alterId: 0
            cipher: auto
            tls: true
            network: ws
            ws-opts:
              path: /
              headers:
                Host: example.com
        
        proxy-groups:
          - name: "Proxy"
            type: select
            proxies:
              - vmess
        
        rules:
          - DOMAIN-SUFFIX,google.com,Proxy
          - DOMAIN-SUFFIX,facebook.com,Proxy
          - GEOIP,CN,DIRECT
          - MATCH,Proxy
        """
        
        result = validator._detect_protocols(clash_content)
        assert "clash" in result
        
        surge_content = """
        [General]
        loglevel = notify
        interface = 127.0.0.1
        port = 6152
        dns-server = 8.8.8.8, 8.8.4.4
        
        [Proxy]
        vmess = vmess, example.com, 443, username=12345678-90ab-12f3-a6c5-4681aaaaaaaa, tls=true, ws=true, ws-path=/, ws-headers=Host:example.com
        
        [Proxy Group]
        Proxy = select, vmess, DIRECT
        
        [Rule]
        DOMAIN-SUFFIX,google.com,Proxy
        DOMAIN-SUFFIX,facebook.com,Proxy
        GEOIP,CN,DIRECT
        MATCH,Proxy
        """
        
        result = validator._detect_protocols(surge_content)
        assert "surge" in result

    @pytest.mark.asyncio
    async def test_protocol_detection_edge_cases(self):
        """Test protocol detection with edge cases and mixed content."""
        validator = SourceValidator()
        
        # Test mixed protocol content
        mixed_content = """
        # This is a mixed subscription file
        vmess://eyJhZGQiOiJleGFtcGxlLmNvbSIsInBvcnQiOiI0NDMiLCJpZCI6IjEyMzQ1Njc4LTkwYWItMTJmMy1hNmM1LTQ2ODFhYWFhYWFhYSIsImFpZCI6IjAiLCJuZXR3b3JrIjoid3MiLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoidGxzIn0=
        
        # WireGuard configuration
        [Interface]
        PrivateKey = private_key_here
        Address = 10.0.0.2/24
        
        [Peer]
        PublicKey = public_key_here
        Endpoint = example.com:51820
        
        # OpenVPN configuration
        client
        remote example.com 1194
        <ca>
        -----BEGIN CERTIFICATE-----
        cert_here
        -----END CERTIFICATE-----
        </ca>
        
        # Clash configuration
        proxies:
          - name: "trojan"
            type: trojan
            server: example.com
            port: 443
            password: password
        """
        
        result = validator._detect_protocols(mixed_content)
        expected_protocols = {"vmess", "wireguard", "openvpn", "clash", "trojan"}
        assert set(result) == expected_protocols
        
        # Test with no protocols
        no_protocol_content = """
        This is just some text content
        No VPN protocols here
        Just regular text
        """
        
        result = validator._detect_protocols(no_protocol_content)
        assert result == []
        
        # Test with partial protocol matches (should not match)
        partial_content = """
        vmess
        trojan
        wireguard
        openvpn
        """
        
        result = validator._detect_protocols(partial_content)
        # Should not match partial protocol names
        assert result == []

    @pytest.mark.asyncio
    async def test_protocol_detection_performance(self):
        """Test protocol detection performance with large content."""
        validator = SourceValidator()
        
        # Generate large content with many protocols
        large_content = []
        protocols = [
            "vmess://", "vless://", "trojan://", "ss://", "ssr://",
            "hysteria://", "hysteria2://", "tuic://", "wg://", "openvpn://"
        ]
        
        # Add 1000 lines of each protocol
        for protocol in protocols:
            for i in range(1000):
                large_content.append(f"{protocol}config_{i}_here")
        
        # Add some non-protocol content
        large_content.extend(["regular text line"] * 1000)
        
        content = "\n".join(large_content)
        
        # Measure detection time
        import time
        start_time = time.time()
        result = validator._detect_protocols(content)
        detection_time = time.time() - start_time
        
        # Should detect all protocols
        expected_protocols = {
            "vmess", "vless", "trojan", "shadowsocks", "shadowsocksr",
            "hysteria", "hysteria2", "tuic", "wireguard", "openvpn"
        }
        assert set(result) == expected_protocols
        
        # Detection should be fast (< 100ms for 10k lines)
        assert detection_time < 0.1, f"Protocol detection took {detection_time:.3f}s, expected < 0.1s"
        
        # Test config estimation performance
        start_time = time.time()
        config_count = validator._estimate_configs(content)
        estimation_time = time.time() - start_time
        
        # Should count all protocol lines
        assert config_count == 10000
        
        # Estimation should be fast (< 50ms for 10k lines)
        assert estimation_time < 0.05, f"Config estimation took {estimation_time:.3f}s, expected < 0.05s"


if __name__ == "__main__":
    pytest.main([__file__])
