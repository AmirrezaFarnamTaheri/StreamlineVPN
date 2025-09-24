from streamline_vpn.core.processing.deduplicator import ConfigurationDeduplicator
from streamline_vpn.models.configuration import VPNConfiguration, Protocol

def test_deduplicate_by_server():
    deduplicator = ConfigurationDeduplicator()
    configs = [
        VPNConfiguration(protocol=Protocol.VMESS, server="server1", port=443, user_id="user1"),
        VPNConfiguration(protocol=Protocol.VLESS, server="server1", port=8443, user_id="user2"),
        VPNConfiguration(protocol=Protocol.TROJAN, server="server2", port=443, user_id="user3"),
    ]
    unique_configs = deduplicator.deduplicate_configurations(configs, strategy="server")
    assert len(unique_configs) == 2
    assert unique_configs[0].server == "server1"
    assert unique_configs[1].server == "server2"

def test_deduplicate_by_user_id():
    deduplicator = ConfigurationDeduplicator()
    configs = [
        VPNConfiguration(protocol=Protocol.VMESS, server="server1", port=443, user_id="user1"),
        VPNConfiguration(protocol=Protocol.VLESS, server="server2", port=8443, user_id="user1"),
        VPNConfiguration(protocol=Protocol.TROJAN, server="server3", port=443, user_id="user2"),
    ]
    unique_configs = deduplicator.deduplicate_configurations(configs, strategy="user_id")
    assert len(unique_configs) == 2
    assert unique_configs[0].user_id == "user1"
    assert unique_configs[1].user_id == "user2"

def test_deduplicate_by_name():
    deduplicator = ConfigurationDeduplicator()
    configs = [
        VPNConfiguration(protocol=Protocol.VMESS, server="server1", port=443, name="config1"),
        VPNConfiguration(protocol=Protocol.VLESS, server="server2", port=8443, name="config1"),
        VPNConfiguration(protocol=Protocol.TROJAN, server="server3", port=443, name="config2"),
    ]
    unique_configs = deduplicator.deduplicate_configurations(configs, strategy="name")
    assert len(unique_configs) == 2
    assert unique_configs[0].name == "config1"
    assert unique_configs[1].name == "config2"
