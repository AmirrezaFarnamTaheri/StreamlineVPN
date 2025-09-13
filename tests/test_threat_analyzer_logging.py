"""Tests for improved logging in ThreatAnalyzer."""

import logging

import pytest

from streamline_vpn.security.auth.threat_analyzer import ThreatAnalyzer


@pytest.mark.asyncio
async def test_ip_reputation_logs_suspicious(caplog):
    analyzer = ThreatAnalyzer()
    with caplog.at_level(logging.WARNING):
        score = await analyzer._assess_ip_reputation("192.168.1.100")
    assert score == 1.0
    assert "High-risk IP detected" in caplog.text


@pytest.mark.asyncio
async def test_geolocation_invalid_ip_logs_warning(caplog):
    analyzer = ThreatAnalyzer()
    with caplog.at_level(logging.WARNING):
        score = await analyzer._assess_geolocation_risk("not-an-ip")
    assert score == 1.0
    assert "Invalid IP address" in caplog.text
