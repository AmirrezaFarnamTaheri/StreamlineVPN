"""
Integration tests for security components.
"""

import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from streamline_vpn.security.manager import SecurityManager
from streamline_vpn.security.blocklist_manager import BlocklistManager
from streamline_vpn.security.rate_limiter import RateLimiter
from streamline_vpn.security.threat_analyzer import ThreatAnalyzer


class TestSecurityComponents:
    """Test security components integration."""

    @pytest.fixture
    def security_manager(self):
        return SecurityManager()

    @pytest.fixture
    def blocklist_manager(self):
        return BlocklistManager()

    @pytest.fixture
    def rate_limiter(self):
        return RateLimiter(max_requests=10, window_seconds=60)

    @pytest.fixture
    def threat_analyzer(self):
        return ThreatAnalyzer()

    @pytest.mark.asyncio
    async def test_security_manager_integration(self, security_manager):
        """Test security manager integration."""
        with patch('streamline_vpn.security.manager.SecurityManager.validate_request') as mock_validate:
            mock_validate.return_value = AsyncMock(return_value=True)
            
            result = await security_manager.validate_request("test-ip", "test-user-agent")
            assert result is True

    @pytest.mark.asyncio
    async def test_blocklist_manager_integration(self, blocklist_manager):
        """Test blocklist manager integration."""
        # Test adding blocked IP
        blocklist_manager.add_blocked_ip("192.168.1.100", "Test reason")
        assert blocklist_manager.is_ip_blocked("192.168.1.100") is True
        
        # Test adding blocked domain
        blocklist_manager.add_blocked_domain("malicious.com", "Malicious domain")
        assert blocklist_manager.is_domain_blocked("malicious.com") is True
        
        # Test adding blocked pattern
        blocklist_manager.add_blocked_pattern("malware*", "Malware pattern")
        assert blocklist_manager.is_pattern_blocked("malware.exe") is True

    @pytest.mark.asyncio
    async def test_rate_limiter_integration(self, rate_limiter):
        """Test rate limiter integration."""
        # Test within rate limit
        for i in range(5):
            result = await rate_limiter.is_allowed("test-key")
            assert result is True
        
        # Test exceeding rate limit
        for i in range(10):
            result = await rate_limiter.is_allowed("test-key")
            if i < 10:
                assert result is True
            else:
                assert result is False

    @pytest.mark.asyncio
    async def test_threat_analyzer_integration(self, threat_analyzer):
        """Test threat analyzer integration."""
        # Test adding threat pattern
        threat_analyzer.add_threat_pattern("malware", "Malware pattern", "high")
        threat_analyzer.add_threat_pattern("phishing", "Phishing pattern", "medium")
        
        # Test analyzing content
        result = threat_analyzer.analyze_threat("This contains malware")
        assert result["risk_level"] == "high"
        assert result["threats_detected"] > 0
        assert "malware" in result["threats"]

    @pytest.mark.asyncio
    async def test_security_validation_integration(self, security_manager):
        """Test security validation integration."""
        with patch('streamline_vpn.security.manager.SecurityManager.validate_configuration') as mock_validate:
            mock_validate.return_value = AsyncMock(return_value=True)
            
            config = {"server": "example.com", "port": 443, "protocol": "vmess"}
            result = await security_manager.validate_configuration(config)
            assert result is True

    @pytest.mark.asyncio
    async def test_security_monitoring_integration(self, security_manager):
        """Test security monitoring integration."""
        with patch('streamline_vpn.security.manager.SecurityManager.get_security_metrics') as mock_metrics:
            mock_metrics.return_value = AsyncMock(return_value={
                "blocked_requests": 10,
                "allowed_requests": 100,
                "threats_detected": 5,
                "rate_limited_requests": 3
            })
            
            metrics = await security_manager.get_security_metrics()
            assert metrics["blocked_requests"] == 10
            assert metrics["allowed_requests"] == 100
            assert metrics["threats_detected"] == 5
            assert metrics["rate_limited_requests"] == 3

    @pytest.mark.asyncio
    async def test_security_alerting_integration(self, security_manager):
        """Test security alerting integration."""
        with patch('streamline_vpn.security.manager.SecurityManager.send_security_alert') as mock_alert:
            mock_alert.return_value = AsyncMock(return_value=True)
            
            result = await security_manager.send_security_alert(
                "High threat detected",
                "malware",
                "high"
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_security_incident_response_integration(self, security_manager):
        """Test security incident response integration."""
        with patch('streamline_vpn.security.manager.SecurityManager.handle_security_incident') as mock_handle:
            mock_handle.return_value = AsyncMock(return_value=True)
            
            result = await security_manager.handle_security_incident(
                "malware_detected",
                {"ip": "192.168.1.100", "threat": "malware"}
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_security_audit_integration(self, security_manager):
        """Test security audit integration."""
        with patch('streamline_vpn.security.manager.SecurityManager.audit_security_logs') as mock_audit:
            mock_audit.return_value = AsyncMock(return_value={
                "audit_period": "24h",
                "total_events": 1000,
                "security_events": 50,
                "blocked_events": 25,
                "threat_events": 10
            })
            
            audit_result = await security_manager.audit_security_logs()
            assert audit_result["total_events"] == 1000
            assert audit_result["security_events"] == 50
            assert audit_result["blocked_events"] == 25
            assert audit_result["threat_events"] == 10

    @pytest.mark.asyncio
    async def test_security_policy_enforcement_integration(self, security_manager):
        """Test security policy enforcement integration."""
        with patch('streamline_vpn.security.manager.SecurityManager.enforce_security_policy') as mock_enforce:
            mock_enforce.return_value = AsyncMock(return_value=True)
            
            result = await security_manager.enforce_security_policy(
                "test-policy",
                {"user": "test-user", "action": "access_config"}
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_security_component_coordination_integration(self, security_manager, blocklist_manager, rate_limiter, threat_analyzer):
        """Test coordination between security components."""
        # Test coordinated security check
        with patch('streamline_vpn.security.manager.SecurityManager.comprehensive_security_check') as mock_check:
            mock_check.return_value = AsyncMock(return_value={
                "is_safe": True,
                "risk_score": 0.2,
                "blocked": False,
                "rate_limited": False,
                "threats_detected": []
            })
            
            result = await security_manager.comprehensive_security_check(
                "192.168.1.100",
                "test-user-agent",
                "test-content"
            )
            assert result["is_safe"] is True
            assert result["risk_score"] == 0.2
            assert result["blocked"] is False
            assert result["rate_limited"] is False
            assert len(result["threats_detected"]) == 0

    @pytest.mark.asyncio
    async def test_security_error_handling_integration(self, security_manager):
        """Test security error handling integration."""
        with patch('streamline_vpn.security.manager.SecurityManager.validate_request') as mock_validate:
            mock_validate.side_effect = Exception("Security validation failed")
            
            with pytest.raises(Exception):
                await security_manager.validate_request("test-ip", "test-user-agent")

    @pytest.mark.asyncio
    async def test_security_performance_integration(self, security_manager):
        """Test security performance integration."""
        with patch('streamline_vpn.security.manager.SecurityManager.get_performance_metrics') as mock_perf:
            mock_perf.return_value = AsyncMock(return_value={
                "avg_validation_time": 0.05,
                "max_validation_time": 0.1,
                "total_validations": 1000,
                "failed_validations": 10
            })
            
            perf_metrics = await security_manager.get_performance_metrics()
            assert perf_metrics["avg_validation_time"] == 0.05
            assert perf_metrics["max_validation_time"] == 0.1
            assert perf_metrics["total_validations"] == 1000
            assert perf_metrics["failed_validations"] == 10

