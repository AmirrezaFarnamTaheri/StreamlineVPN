from streamline_vpn.core.processing.deduplicator import ConfigurationDeduplicator
from streamline_vpn.models.configuration import VPNConfiguration, Protocol


def cfg(p: Protocol, s: str, port: int, uid: str = "u", pwd: str = ""):
    return VPNConfiguration(protocol=p, server=s, port=port, user_id=uid, password=pwd)


def test_deduplicator_strategies_and_stats():
    d = ConfigurationDeduplicator()
    c1 = cfg(Protocol.VMESS, "a.com", 443, uid="x")
    c2 = cfg(Protocol.VMESS, "a.com", 443, uid="x")  # exact dup
    c3 = cfg(Protocol.VMESS, "a.com", 443, uid="y")  # server_port dup
    c4 = cfg(Protocol.VLESS, "a.com", 443, uid="z")  # server_protocol dup with c1? no (different protocol)
    c5 = cfg(Protocol.VLESS, "b.com", 443, uid="z")
    configs = [c1, c2, c3, c4, c5]

    # exact
    out_exact = d.deduplicate_configurations(configs, "exact")
    assert len(out_exact) < len(configs)
    dup_exact = d.find_duplicates(configs, "exact")
    assert any(len(v) > 1 for v in dup_exact.values())

    # server_port
    out_sp = d.deduplicate_configurations(configs, "server_port")
    assert len(out_sp) <= len(configs)
    # server_protocol
    out_sprot = d.deduplicate_configurations(configs, "server_protocol")
    assert len(out_sprot) <= len(configs)
    # content_hash
    out_hash = d.deduplicate_configurations(configs, "content_hash")
    assert len(out_hash) <= len(configs)

    stats = d.get_deduplication_stats(configs)
    assert stats["total_configs"] == len(configs)
    assert isinstance(stats["strategies"], dict)
    assert set(["exact", "server_port", "server_protocol", "content_hash"]).issubset(stats["strategies"].keys())

