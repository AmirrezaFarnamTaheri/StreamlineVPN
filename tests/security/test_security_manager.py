import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from streamline_vpn.security.manager import SecurityManager

@pytest.fixture
def mock_dependencies():
    """Provides a fixture with mocked dependencies for SecurityManager."""
    with patch('streamline_vpn.security.threat_analyzer.ThreatAnalyzer') as mock_threat_analyzer, \
         patch('streamline_vpn.security.validator.SecurityValidator') as mock_validator, \
         patch('streamline_vpn.security.pattern_analyzer.PatternAnalyzer') as mock_pattern_analyzer, \
         patch('streamline_vpn.security.rate_limiter.RateLimiter') as mock_rate_limiter, \
         patch('streamline_vpn.security.blocklist_manager.BlocklistManager') as mock_blocklist_manager:

        yield {
            "threat_analyzer": mock_threat_analyzer.return_value,
            "validator": mock_validator.return_value,
            "pattern_analyzer": mock_pattern_analyzer.return_value,
            "rate_limiter": mock_rate_limiter.return_value,
            "blocklist_manager": mock_blocklist_manager.return_value,
        }

class TestSecurityManager:
    """Tests for the SecurityManager class."""

    def test_init_with_defaults(self, mock_dependencies):
        """Test that SecurityManager initializes with default components."""
        manager = SecurityManager()
        assert manager.threat_analyzer is not None
        assert manager.validator is not None
        assert manager.pattern_analyzer is not None
        assert manager.rate_limiter is not None
        assert manager.blocklist_manager is not None

    def test_init_with_custom_components(self):
        """Test that SecurityManager initializes with custom (mocked) components."""
        mocks = {
            "threat_analyzer": MagicMock(),
            "validator": MagicMock(),
            "pattern_analyzer": MagicMock(),
            "rate_limiter": MagicMock(),
            "blocklist_manager": MagicMock(),
        }
        manager = SecurityManager(**mocks)
        assert manager.threat_analyzer == mocks["threat_analyzer"]
        assert manager.validator == mocks["validator"]
        assert manager.pattern_analyzer == mocks["pattern_analyzer"]
        assert manager.rate_limiter == mocks["rate_limiter"]
        assert manager.blocklist_manager == mocks["blocklist_manager"]

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test the initialize method."""
        manager = SecurityManager()
        result = await manager.initialize()
        assert result is True
        assert manager.is_initialized is True

    def test_analyze_configuration_safe(self, mock_dependencies):
        """Test analyze_configuration with a safe configuration."""
        manager = SecurityManager()
        mock_dependencies["threat_analyzer"].analyze.return_value = []
        mock_dependencies["pattern_analyzer"].check_suspicious_patterns.return_value = []
        mock_dependencies["pattern_analyzer"].analyze_urls.return_value = {}

        config = "safe config"
        result = manager.analyze_configuration(config)

        assert result["is_safe"] is True
        assert result["risk_score"] < 0.5

    def test_analyze_configuration_unsafe(self, mock_dependencies):
        """Test analyze_configuration with an unsafe configuration."""
        manager = SecurityManager()
        mock_dependencies["threat_analyzer"].analyze.return_value = [{"threat": "some_threat"}]
        mock_dependencies["pattern_analyzer"].check_suspicious_patterns.return_value = ["suspicious"]
        mock_dependencies["pattern_analyzer"].analyze_urls.return_value = {"blocked_urls": ["http://bad.com"]}

        config = "unsafe config"
        result = manager.analyze_configuration(config)

        assert result["is_safe"] is False
        assert result["risk_score"] > 0.5

    def test_analyze_configuration_empty_config(self, mock_dependencies):
        """Test analyze_configuration with an empty configuration string."""
        manager = SecurityManager()
        result = manager.analyze_configuration("")
        assert result["is_safe"] is False
        assert result["risk_score"] == 1.0

    def test_validate_source_safe(self, mock_dependencies):
        """Test validate_source with a safe URL."""
        manager = SecurityManager()
        mock_dependencies["validator"].validate_url.return_value = True
        mock_dependencies["blocklist_manager"].is_domain_blocked.return_value = False
        mock_dependencies["rate_limiter"].check_rate_limit.return_value = False
        mock_dependencies["pattern_analyzer"].analyze_domain.return_value = {"is_safe": True}

        source_url = "http://good.com"
        result = manager.validate_source(source_url)

        assert result["is_safe"] is True

    def test_validate_source_blocked(self, mock_dependencies):
        """Test validate_source with a blocked domain."""
        manager = SecurityManager()
        mock_dependencies["validator"].validate_url.return_value = True
        mock_dependencies["blocklist_manager"].is_domain_blocked.return_value = True

        source_url = "http://blocked.com"
        result = manager.validate_source(source_url)

        assert result["is_safe"] is False
        assert result["is_blocked"] is True

    def test_block_ip(self, mock_dependencies):
        """Test the block_ip method."""
        manager = SecurityManager()
        manager.block_ip("1.2.3.4", "test reason")
        mock_dependencies["blocklist_manager"].block_ip.assert_called_once_with("1.2.3.4", "test reason")

    def test_block_domain(self, mock_dependencies):
        """Test the block_domain method."""
        manager = SecurityManager()
        manager.block_domain("bad.com", "test reason")
        mock_dependencies["blocklist_manager"].block_domain.assert_called_once_with("bad.com", "test reason")

    def test_unblock_ip(self, mock_dependencies):
        """Test the unblock_ip method."""
        manager = SecurityManager()
        manager.unblock_ip("1.2.3.4")
        mock_dependencies["blocklist_manager"].unblock_ip.assert_called_once_with("1.2.3.4")

    def test_unblock_domain(self, mock_dependencies):
        """Test the unblock_domain method."""
        manager = SecurityManager()
        manager.unblock_domain("bad.com")
        mock_dependencies["blocklist_manager"].unblock_domain.assert_called_once_with("bad.com")

    def test_get_security_statistics(self, mock_dependencies):
        """Test the get_security_statistics method."""
        manager = SecurityManager()
        mock_dependencies["blocklist_manager"].get_blocklist_stats.return_value = {"blocked_ips": 1}
        mock_dependencies["rate_limiter"].get_rate_limit_stats.return_value = {"active_limits": 2}
        mock_dependencies["pattern_analyzer"].suspicious_patterns = ["p1", "p2", "p3"]

        stats = manager.get_security_statistics()

        assert stats["blocked_ips"] == 1
        assert stats["active_limits"] == 2
        assert stats["suspicious_patterns"] == 3

    @pytest.mark.asyncio
    async def test_get_security_metrics(self, mock_dependencies):
        """Test the get_security_metrics method."""
        manager = SecurityManager()
        mock_dependencies["blocklist_manager"].blocked_ips = {"1.1.1.1": "reason"}
        mock_dependencies["blocklist_manager"].blocked_domains = {"d.com": "reason"}
        mock_dependencies["rate_limiter"].rate_limits = {"key": "data"}
        # The code first checks for 'patterns', then 'suspicious_patterns'.
        # MagicMock's getattr behavior returns a new mock for unset attributes
        # instead of letting the default value in getattr work.
        # So we must set the attribute the code looks for first.
        mock_dependencies["pattern_analyzer"].patterns = ["p1"]

        metrics = await manager.get_security_metrics()

        assert metrics["blocked_ips"] == 1
        assert metrics["blocked_domains"] == 1
        assert metrics["rate_limit_keys"] == 1
        assert metrics["patterns"] == 1

    @pytest.mark.asyncio
    async def test_send_security_alert(self):
        """Test the send_security_alert method."""
        manager = SecurityManager()
        with patch('streamline_vpn.security.manager.logger') as mock_logger:
            result = await manager.send_security_alert("Test Alert", "high")
            assert result is True
            mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_security_incident(self):
        """Test the handle_security_incident method."""
        manager = SecurityManager()
        with patch('streamline_vpn.security.manager.logger') as mock_logger:
            result = await manager.handle_security_incident("Test Incident", {})
            assert result is True
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_audit_security_logs(self):
        """Test the audit_security_logs method."""
        manager = SecurityManager()
        result = await manager.audit_security_logs()
        assert "total_events" in result

    @pytest.mark.asyncio
    async def test_enforce_security_policy(self):
        """Test the enforce_security_policy method."""
        manager = SecurityManager()
        result = await manager.enforce_security_policy("policy", {})
        assert result is True

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self):
        """Test the get_performance_metrics method."""
        manager = SecurityManager()
        result = await manager.get_performance_metrics()
        assert "total_validations" in result

    @pytest.mark.asyncio
    async def test_comprehensive_security_check_safe(self, mock_dependencies):
        """Test comprehensive_security_check with safe inputs."""
        manager = SecurityManager()
        mock_dependencies["blocklist_manager"].is_ip_blocked.return_value = False
        mock_dependencies["rate_limiter"].check_rate_limit.return_value = False
        # Mock the result of analyze_configuration
        with patch.object(manager, 'analyze_configuration', return_value={"is_safe": True, "risk_score": 0.1, "threats": []}):
            result = await manager.comprehensive_security_check("1.2.3.4", "agent", "content")
            assert result["is_safe"] is True

    @pytest.mark.asyncio
    async def test_comprehensive_security_check_blocked(self, mock_dependencies):
        """Test comprehensive_security_check with a blocked IP."""
        manager = SecurityManager()
        mock_dependencies["blocklist_manager"].is_ip_blocked.return_value = True
        result = await manager.comprehensive_security_check("1.2.3.4", "agent", "content")
        assert result["is_safe"] is False
        assert result["blocked"] is True

    @pytest.mark.asyncio
    async def test_comprehensive_security_check_rate_limited(self, mock_dependencies):
        """Test comprehensive_security_check with a rate-limited IP."""
        manager = SecurityManager()
        mock_dependencies["blocklist_manager"].is_ip_blocked.return_value = False
        mock_dependencies["rate_limiter"].check_rate_limit.return_value = True
        result = await manager.comprehensive_security_check("1.2.3.4", "agent", "content")
        assert result["is_safe"] is False
        assert result["rate_limited"] is True
