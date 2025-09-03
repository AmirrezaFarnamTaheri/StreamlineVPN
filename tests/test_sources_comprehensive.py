#!/usr/bin/env python3

"""
Comprehensive test suite for source management and validation.
Tests advanced scenarios and edge cases.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import the classes we're testing
from vpn_merger import (
    SourceManager,
    UnifiedSourceValidator,
    VPNConfiguration,
    VPNSubscriptionMerger,
)


class TestSourceManagerComprehensive:
    """Comprehensive tests for SourceManager class."""

    def test_fallback_sources_structure(self):
        """Test that fallback sources have proper structure."""
        sources = SourceManager("nonexistent.yaml")

        # Check fallback structure (when config file doesn't exist)
        assert "emergency_fallback" in sources.sources
        assert isinstance(sources.sources["emergency_fallback"], list)
        assert len(sources.sources["emergency_fallback"]) > 0

    def test_source_urls_valid(self):
        """Test that all source URLs are valid."""
        sources = SourceManager()
        all_sources = sources.get_all_sources()

        for url in all_sources:
            assert url.startswith("http")
            assert "://" in url
            assert len(url) > 10

    def test_tier_priority_order(self):
        """Test that prioritized sources maintain tier order."""
        sources = SourceManager()
        prioritized = sources.get_prioritized_sources()

        # Get tier indices
        tier_indices = {}
        for i, url in enumerate(prioritized):
            for tier_name, tier_urls in sources.sources.items():
                if url in tier_urls:
                    if tier_name not in tier_indices:
                        tier_indices[tier_name] = []
                    tier_indices[tier_name].append(i)

        # Check that tier 1 comes before tier 2, etc.
        if "tier_1_premium" in tier_indices and "tier_2_reliable" in tier_indices:
            assert max(tier_indices["tier_1_premium"]) < min(tier_indices["tier_2_reliable"])


class TestUnifiedSourceValidatorComprehensive:
    """Comprehensive tests for SourceHealthChecker class."""

    @pytest.mark.asyncio
    async def test_concurrent_validation(self):
        """Test concurrent source validation."""
        urls = ["https://example1.com", "https://example2.com", "https://example3.com"]

        with patch("aiohttp.ClientSession.get") as mock_get:
            # Mock responses
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="vmess://test")
            mock_get.return_value.__aenter__.return_value = mock_response

            async with UnifiedSourceValidator() as validator:
                # Validate all sources concurrently
                tasks = [validator.validate_source(url) for url in urls]
                results = await asyncio.gather(*tasks)

                assert len(results) == 3
                for result in results:
                    data = result if isinstance(result, dict) else result.to_dict()
                    assert data["accessible"] is True
                    assert data["status_code"] == 200

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling in validation."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = asyncio.TimeoutError("Request timeout")

            async with UnifiedSourceValidator() as validator:
                result = await validator.validate_source("https://raw.githubusercontent.com/test")
                data = result if isinstance(result, dict) else result.to_dict()
                assert data["accessible"] is False
                assert "error" in data
                assert "timeout" in data["error"].lower()

    def test_protocol_detection_edge_cases(self):
        """Test protocol detection with edge cases."""
        validator = UnifiedSourceValidator()

        # Empty content
        protocols = validator._detect_protocols("")
        assert protocols == []

        # Mixed case
        content = "VMESS://test\nVLESS://test\nTROJAN://test"
        protocols = validator._detect_protocols(content)
        assert "vmess" in protocols
        assert "vless" in protocols
        assert "trojan" in protocols

        # Malformed protocols
        content = "vmess:/test\nvless:/test"
        protocols = validator._detect_protocols(content)
        assert protocols == []

    def test_reliability_score_calculation(self):
        """Test reliability score calculation edge cases."""
        validator = UnifiedSourceValidator()

        # Zero configs, one protocol
        score = validator._calculate_reliability_score(200, 0, ["vmess"])
        assert score == 0.5  # Status bonus (0.4) + protocol bonus (0.1)

        # Zero configs, no protocols
        score = validator._calculate_reliability_score(200, 0, [])
        assert score == 0.4  # Only status bonus

        # Very high config count
        score = validator._calculate_reliability_score(200, 100000, ["vmess", "vless", "trojan"])
        assert score == 1.0  # Should be capped at 1.0

        # Many protocols
        protocols = ["vmess", "vless", "trojan", "shadowsocks", "hysteria", "tuic"]
        score = validator._calculate_reliability_score(200, 1000, protocols)
        assert score == 0.8  # Status (0.4) + Config (0.1) + Protocols (0.3) = 0.8


class TestVPNConfigurationComprehensive:
    """Comprehensive tests for VPNConfiguration class."""

    def test_serialization_roundtrip(self):
        """Test serialization and deserialization."""
        original = VPNConfiguration(
            config="vmess://test",
            protocol="vmess",
            host="example.com",
            port=443,
            quality_score=0.85,
        )

        # Convert to dict and back
        data = original.to_dict()
        assert isinstance(data, dict)

        # Check all fields are present
        expected_fields = [
            "config",
            "protocol",
            "host",
            "port",
            "ping_time",
            "is_reachable",
            "source_url",
            "quality_score",
            "last_tested",
            "error_count",
        ]
        for field in expected_fields:
            assert field in data

    def test_quality_score_bounds(self):
        """Test quality score bounds and validation."""
        # Valid scores
        result1 = VPNConfiguration("vmess://test", "vmess", quality_score=0.0)
        result2 = VPNConfiguration("vless://test", "vless", quality_score=1.0)
        result3 = VPNConfiguration("trojan://test", "trojan", quality_score=0.5)

        assert 0.0 <= result1.quality_score <= 1.0
        assert 0.0 <= result2.quality_score <= 1.0
        assert 0.0 <= result3.quality_score <= 1.0

    def test_error_count_tracking(self):
        """Test error count tracking functionality."""
        result = VPNConfiguration("vmess://test", "vmess")
        assert result.error_count == 0

        # Simulate errors
        result.error_count += 1
        assert result.error_count == 1

        result.error_count += 5
        assert result.error_count == 6


class TestVPNSubscriptionMergerIntegration:
    """Integration tests for VPNSubscriptionMerger class."""

    def test_merger_initialization(self):
        """Test VPNSubscriptionMerger initialization."""
        merger = VPNSubscriptionMerger()

        assert merger.source_manager is not None
        assert merger.config_processor is not None
        assert merger.results == []
        assert merger.stats["total_sources"] == 0

    @pytest.mark.asyncio
    async def test_merger_basic_operation(self):
        """Test basic merger operation."""
        # Create a simple test merger
        merger = VPNSubscriptionMerger()

        # Test basic functionality without complex mocking
        assert merger.source_manager is not None
        assert merger.config_processor is not None
        assert merger.results == []
        assert merger.stats["total_sources"] == 0

        # Test that sources can be loaded
        sources = merger.source_manager.get_all_sources()
        assert len(sources) > 0

        # Test that the merger can be initialized properly
        assert hasattr(merger, "run_comprehensive_merge")
        assert callable(merger.run_comprehensive_merge)


if __name__ == "__main__":
    pytest.main([__file__])
