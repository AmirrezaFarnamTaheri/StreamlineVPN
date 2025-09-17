import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.security.blocklist_manager import BlocklistManager

@pytest.fixture
def blocklist_manager():
    """Fixture for BlocklistManager."""
    return BlocklistManager()

class TestBlocklistManager:
    def test_initialization(self, blocklist_manager):
        assert blocklist_manager.blocked_ips == {}
        assert blocklist_manager.blocked_domains == {}

    def test_block_ip(self, blocklist_manager):
        blocklist_manager.block_ip("1.2.3.4", "test reason")
        assert "1.2.3.4" in blocklist_manager.blocked_ips

    def test_add_blocked_ip(self, blocklist_manager):
        blocklist_manager.add_blocked_ip("1.2.3.4", "test reason")
        assert "1.2.3.4" in blocklist_manager.blocked_ips

    def test_block_domain(self, blocklist_manager):
        blocklist_manager.block_domain("example.com", "test reason")
        assert "example.com" in blocklist_manager.blocked_domains

    def test_add_blocked_domain(self, blocklist_manager):
        blocklist_manager.add_blocked_domain("example.com", "test reason")
        assert "example.com" in blocklist_manager.blocked_domains

    def test_unblock_ip(self, blocklist_manager):
        blocklist_manager.blocked_ips["1.2.3.4"] = {}
        blocklist_manager.unblock_ip("1.2.3.4")
        assert "1.2.3.4" not in blocklist_manager.blocked_ips

    def test_remove_blocked_ip(self, blocklist_manager):
        blocklist_manager.blocked_ips["1.2.3.4"] = {}
        blocklist_manager.remove_blocked_ip("1.2.3.4")
        assert "1.2.3.4" not in blocklist_manager.blocked_ips

    def test_unblock_domain(self, blocklist_manager):
        blocklist_manager.blocked_domains["example.com"] = {}
        blocklist_manager.unblock_domain("example.com")
        assert "example.com" not in blocklist_manager.blocked_domains

    def test_remove_blocked_domain(self, blocklist_manager):
        blocklist_manager.blocked_domains["example.com"] = {}
        blocklist_manager.remove_blocked_domain("example.com")
        assert "example.com" not in blocklist_manager.blocked_domains

    def test_is_ip_blocked(self, blocklist_manager):
        blocklist_manager.blocked_ips["1.2.3.4"] = {}
        assert blocklist_manager.is_ip_blocked("1.2.3.4") is True
        assert blocklist_manager.is_ip_blocked("5.6.7.8") is False

    def test_is_domain_blocked(self, blocklist_manager):
        blocklist_manager.blocked_domains["example.com"] = {}
        assert blocklist_manager.is_domain_blocked("sub.example.com") is True
        assert blocklist_manager.is_domain_blocked("google.com") is False

    def test_is_pattern_blocked(self, blocklist_manager):
        blocklist_manager.add_blocked_pattern("*.bad.com")
        assert blocklist_manager.is_pattern_blocked("foo.bad.com") is True
        assert blocklist_manager.is_pattern_blocked("good.com") is False

    def test_remove_blocked_pattern(self, blocklist_manager):
        blocklist_manager.add_blocked_pattern("*.bad.com")
        blocklist_manager.remove_blocked_pattern("*.bad.com")
        assert blocklist_manager.is_pattern_blocked("foo.bad.com") is False

    def test_get_blocklist_stats(self, blocklist_manager):
        blocklist_manager.blocked_ips["1.2.3.4"] = {}
        blocklist_manager.blocked_domains["example.com"] = {}
        stats = blocklist_manager.get_blocklist_stats()
        assert stats["blocked_ips"] == 1
        assert stats["blocked_domains"] == 1
        assert stats["total_blocked"] == 2

    def test_get_blocked_count(self, blocklist_manager):
        blocklist_manager.blocked_ips["1.2.3.4"] = {}
        blocklist_manager.blocked_domains["example.com"] = {}
        blocklist_manager.add_blocked_pattern("*.bad.com")
        assert blocklist_manager.get_blocked_count() == 3

    def test_clear_blocklists(self, blocklist_manager):
        blocklist_manager.blocked_ips["1.2.3.4"] = {}
        blocklist_manager.blocked_domains["example.com"] = {}
        blocklist_manager.clear_blocklists()
        assert blocklist_manager.blocked_ips == {}
        assert blocklist_manager.blocked_domains == {}

    def test_clear_all(self, blocklist_manager):
        blocklist_manager.blocked_ips["1.2.3.4"] = {}
        blocklist_manager.blocked_domains["example.com"] = {}
        blocklist_manager.add_blocked_pattern("*.bad.com")
        blocklist_manager.clear_all()
        assert blocklist_manager.blocked_ips == {}
        assert blocklist_manager.blocked_domains == {}
        assert blocklist_manager.blocked_patterns == {}
