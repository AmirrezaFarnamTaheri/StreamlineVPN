import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.security.threat_analyzer import ThreatAnalyzer

@pytest.fixture
def threat_analyzer():
    """Fixture for ThreatAnalyzer."""
    with patch('streamline_vpn.settings.get_settings'):
        analyzer = ThreatAnalyzer()
        return analyzer

class TestThreatAnalyzer:
    def test_initialization(self, threat_analyzer):
        assert threat_analyzer.malicious_patterns is not None
        assert threat_analyzer.suspicious_domains is not None
        assert threat_analyzer.suspicious_ports is not None

    def test_analyze_no_threats(self, threat_analyzer):
        result = threat_analyzer.analyze("safe content")
        assert result == []

    def test_analyze_with_threats(self, threat_analyzer):
        result = threat_analyzer.analyze("<script>alert('xss')</script>")
        assert len(result) > 0

    def test_check_malicious_patterns(self, threat_analyzer):
        result = threat_analyzer._check_malicious_patterns("<script>alert('xss')</script>")
        assert len(result) > 0

    def test_check_malicious_patterns_no_threats(self, threat_analyzer):
        result = threat_analyzer._check_malicious_patterns("safe content")
        assert result == []

    def test_check_suspicious_urls(self, threat_analyzer):
        result = threat_analyzer._check_suspicious_urls("http://malware.com")
        assert len(result) > 0

    def test_check_suspicious_urls_no_threats(self, threat_analyzer):
        result = threat_analyzer._check_suspicious_urls("http://example.com")
        assert result == []

    def test_check_suspicious_ports(self, threat_analyzer):
        result = threat_analyzer._check_suspicious_ports(":22")
        assert len(result) > 0

    def test_check_suspicious_ports_no_threats(self, threat_analyzer):
        threat_analyzer.suspicious_ports = [21]
        result = threat_analyzer._check_suspicious_ports(":8080")
        assert len(result) == 0

    def test_check_encoded_content(self, threat_analyzer):
        result = threat_analyzer._check_encoded_content("PHNjcmlwdD5hbGVydCgneHNzJyk8L3NjcmlwdD4=") # "<script>alert('xss')</script>" in base64
        assert len(result) > 0

    def test_check_encoded_content_no_threats(self, threat_analyzer):
        result = threat_analyzer._check_encoded_content("c2FmZSBjb250ZW50") # "safe content" in base64
        assert len(result) == 0

    def test_check_suspicious_protocols(self, threat_analyzer):
        result = threat_analyzer._check_suspicious_protocols("ftp://example.com")
        assert len(result) > 0

    def test_check_suspicious_protocols_no_threats(self, threat_analyzer):
        result = threat_analyzer._check_suspicious_protocols("http://example.com")
        assert result == []

    def test_get_threat_statistics(self, threat_analyzer):
        stats = threat_analyzer.get_threat_statistics()
        assert "malicious_patterns" in stats
        assert "suspicious_domains" in stats
        assert "suspicious_ports" in stats

    def test_add_threat_pattern(self, threat_analyzer):
        threat_analyzer.add_threat_pattern("test_pattern", "test", "high")
        assert "test_pattern" in threat_analyzer.threat_patterns
        assert "test" in threat_analyzer.malicious_patterns

    def test_remove_threat_pattern(self, threat_analyzer):
        threat_analyzer.add_threat_pattern("test_pattern", "test", "high")
        threat_analyzer.remove_threat_pattern("test_pattern")
        assert "test_pattern" not in threat_analyzer.threat_patterns
        assert "test" not in threat_analyzer.malicious_patterns

    def test_get_threat_count(self, threat_analyzer):
        threat_analyzer.add_threat_pattern("test_pattern", "test", "high")
        assert threat_analyzer.get_threat_count() == 1

    def test_clear_threats(self, threat_analyzer):
        threat_analyzer.add_threat_pattern("test_pattern", "test", "high")
        threat_analyzer.clear_threats()
        assert threat_analyzer.get_threat_count() == 0

    def test_analyze_threat(self, threat_analyzer):
        result = threat_analyzer.analyze_threat("<script>alert('xss')</script>")
        assert result["is_safe"] is False
        assert result["risk_level"] == "high"

    def test_analyze_threat_custom_pattern(self, threat_analyzer):
        threat_analyzer.add_threat_pattern("test_pattern", "test", "medium")
        result = threat_analyzer.analyze_threat("this is a test")
        assert result["is_safe"] is False
        assert result["risk_level"] == "medium"

    def test_analyze_threat_no_threats(self, threat_analyzer):
        result = threat_analyzer.analyze_threat("safe content")
        assert result["is_safe"] is True
        assert result["risk_level"] == "none"
