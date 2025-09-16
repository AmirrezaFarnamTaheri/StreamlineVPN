import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.security.blocklist_manager import BlocklistManager


def test_blocklist_manager_block_unblock_and_stats():
    bm = BlocklistManager()
    bm.block_ip("1.2.3.4", "test")
    bm.block_domain("bad.example", "test")
    bm.add_blocked_pattern("*.malicious", "wildcard")
    assert bm.is_ip_blocked("1.2.3.4") is True
    assert bm.is_domain_blocked("very.bad.example") is True
    assert bm.is_pattern_blocked("x.malicious") is True
    stats = bm.get_blocklist_stats()
    assert stats["blocked_ips"] == 1 and stats["blocked_domains"] == 1
    bm.unblock_ip("1.2.3.4")
    bm.unblock_domain("bad.example")
    bm.remove_blocked_pattern("*.malicious")
    assert bm.get_blocked_count() == 0


