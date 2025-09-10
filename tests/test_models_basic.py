import json
from datetime import datetime

import pytest

from streamline_vpn.models.configuration import VPNConfiguration, Protocol
from streamline_vpn.models.processing_result import ProcessingResult, ProcessingStatistics
from streamline_vpn.models.formats import OutputFormat
from streamline_vpn.models.source import SourceMetadata, SourceTier


def test_vpn_configuration_valid_roundtrip():
    cfg = VPNConfiguration(
        protocol=Protocol.VMESS,
        server="test.example.com",
        port=443,
        user_id="uuid-123",
        encryption="auto",
        network="ws",
        path="/path",
        tls=True,
        quality_score=0.75,
        source_url="https://source.example.com",
        metadata={"region": "us"},
    )
    assert cfg.is_valid
    d = cfg.to_dict()
    assert d["protocol"] == "vmess"
    assert d["tls"] is True
    j = cfg.to_json()
    cfg2 = VPNConfiguration.from_json(j)
    assert cfg2.server == cfg.server
    assert cfg2.protocol == Protocol.VMESS


def test_vpn_configuration_invalid_port_and_quality():
    with pytest.raises(ValueError):
        VPNConfiguration(protocol=Protocol.VLESS, server="s", port=70000)
    with pytest.raises(ValueError):
        VPNConfiguration(protocol=Protocol.VLESS, server="s", port=443, quality_score=1.5)


def test_processing_result_and_stats():
    pr = ProcessingResult(url="https://s", success=True)
    assert pr.config_count == 0
    pr.add_config("vmess://a", 0.8)
    pr.add_config("vmess://b", 0.6)
    assert pr.config_count == 2
    assert 0.69 < pr.avg_quality_score < 0.71
    d = pr.to_dict()
    pr2 = ProcessingResult.from_dict(d)
    assert pr2.config_count == 2

    stats = ProcessingStatistics(total_sources=10, successful_sources=8, total_configs=400)
    assert 0.79 < stats.success_rate < 0.81
    stats.finish()
    sd = stats.to_dict()
    assert sd["total_sources"] == 10
    assert isinstance(datetime.fromisoformat(sd["start_time"]), datetime)


def test_output_format_enum():
    vals = OutputFormat.values()
    assert "json" in vals and "clash" in vals and "singbox" in vals
    assert OutputFormat.is_valid("json")
    assert not OutputFormat.is_valid("invalid")


def test_source_metadata_basic_and_reputation():
    s = SourceMetadata(url="https://example.com", tier=SourceTier.RELIABLE, weight=0.7)
    assert s.enabled is True
    # Add some performance history
    s.add_performance_record(success=True, config_count=100, response_time=1.0)
    s.add_performance_record(success=False, config_count=0, response_time=2.0)
    s.add_performance_record(success=True, config_count=120, response_time=1.5)
    assert s.avg_response_time > 0
    assert s.avg_config_count >= 0
    assert 0 <= s.reputation_score <= 1
    # Frequency parsing
    s.update_frequency = "5m"
    assert isinstance(s.should_update(), bool)
    s.update_frequency = "1h"
    assert isinstance(s.should_update(), bool)
    s.update_frequency = "2d"
    assert isinstance(s.should_update(), bool)
    # Serialization
    j = s.to_json()
    s2 = SourceMetadata.from_json(j)
    assert s2.url == s.url

