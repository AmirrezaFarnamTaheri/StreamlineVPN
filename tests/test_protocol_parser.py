from vpn_merger.processing.parser import ProtocolParser


def test_extract_endpoint_vless():
    host, port = ProtocolParser.extract_endpoint('vless://user@myhost.example:443')
    assert host == 'myhost.example' and port == 443


def test_extract_endpoint_vmess_invalid():
    host, port = ProtocolParser.extract_endpoint('vmess://not_base64')
    assert host is None and port is None


def test_categorize():
    assert ProtocolParser.categorize('trojan://u@h:443') == 'Trojan'
    assert ProtocolParser.categorize('unknown://') == 'Other'

