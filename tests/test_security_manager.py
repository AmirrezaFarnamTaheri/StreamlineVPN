"""
Test security-related functionality of the VPN merger.
"""

from vpn_merger import ConfigurationProcessor


class TestSecurityFeatures:
    """Test security-related functionality."""

    def test_config_validation_security(self):
        """Test that configuration validation prevents malicious inputs."""
        processor = ConfigurationProcessor()

        # Test that invalid/malicious configs are rejected
        malicious_configs = [
            "",  # Empty config
            "javascript:alert('xss')",  # JavaScript injection
            "data:text/html,<script>alert('xss')</script>",  # Data URI injection
            "file:///etc/passwd",  # File protocol injection
            "ftp://malicious.com",  # Unwanted protocols
            "http://malicious.com",  # HTTP protocol
            "https://malicious.com",  # HTTPS protocol
        ]

        for config in malicious_configs:
            result = processor.process_config(config)
            assert result is None, f"Malicious config {config} was accepted"

    def test_protocol_whitelist(self):
        """Test that only allowed protocols are accepted."""
        processor = ConfigurationProcessor()

        # Allowed protocols
        allowed_protocols = [
            "vmess://test",
            "vless://test",
            "trojan://test",
            "ss://test",
            "ssr://test",
            "hysteria://test",
            "hysteria2://test",
            "tuic://test",
        ]

        for config in allowed_protocols:
            result = processor.process_config(config)
            assert result is not None, f"Allowed protocol {config} was rejected"

        # Disallowed protocols
        disallowed_protocols = [
            "http://test",
            "https://test",
            "ftp://test",
            "file://test",
            "javascript:test",
            "data:text/plain,test",
        ]

        for config in disallowed_protocols:
            result = processor.process_config(config)
            assert result is None, f"Disallowed protocol {config} was accepted"

    def test_input_sanitization(self):
        """Test that inputs are properly sanitized."""
        processor = ConfigurationProcessor()

        # Test with various input types and edge cases
        test_cases = [
            ("vmess://test1", True),  # Normal config
            (" vless://test2 ", True),  # Whitespace around
            ("\ntrojan://test3\n", True),  # Newlines around
            ("\tss://test4\t", True),  # Tabs around
            ("", False),  # Empty
            ("   ", False),  # Only whitespace
            ("vmess://", False),  # Incomplete
            ("vmess://" + "a" * 10000, False),  # Too long
        ]

        for config, should_accept in test_cases:
            result = processor.process_config(config)
            if should_accept:
                assert result is not None, f"Valid config {config} was rejected"
            else:
                assert result is None, f"Invalid config {config} was accepted"

    def test_quality_score_security(self):
        """Test that quality scoring doesn't introduce security vulnerabilities."""
        processor = ConfigurationProcessor()

        # Test that quality scores are bounded and reasonable
        config = "vmess://eyJhZGQiOiAidGVzdC5leGFtcGxlLmNvbSIsICJwb3J0IjogNDQzfQ=="
        result = processor.process_config(config)

        assert result is not None
        assert 0 <= result.quality_score <= 1, "Quality score out of bounds"
        assert isinstance(result.quality_score, float), "Quality score not a float"

    def test_deduplication_security(self):
        """Test that deduplication doesn't introduce security issues."""
        processor = ConfigurationProcessor()

        # Test that deduplication works correctly and safely
        config1 = "vmess://test1@example.com:443"
        config2 = "vmess://test2@example.com:443"

        # Process first config
        result1 = processor.process_config(config1)
        assert result1 is not None

        # Process second config
        result2 = processor.process_config(config2)
        assert result2 is not None

        # Process first config again (should be deduplicated)
        result3 = processor.process_config(config1)
        assert result3 is None

        # Verify deduplication doesn't affect other configs
        result4 = processor.process_config(config2)
        assert result4 is None

        # Verify we can still process new configs
        config3 = "vless://test3@example.com:443"
        result5 = processor.process_config(config3)
        assert result5 is not None
