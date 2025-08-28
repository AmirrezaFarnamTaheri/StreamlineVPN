import base64
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Undo stub injection from other tests if present
_vm = sys.modules.get("vpn_merger")
if _vm is not None and not hasattr(_vm, "__path__"):
    del sys.modules["vpn_merger"]

from vpn_merger.core.protocol_handler import EnhancedConfigProcessor


def b64_json(obj) -> str:
    raw = base64.b64encode(str(obj).replace("'", '"').encode('utf-8')).decode('utf-8')
    return raw


def test_categorize_protocol_prefixes():
    p = EnhancedConfigProcessor()
    assert p.categorize_protocol('vmess://...') == 'VMess'
    assert p.categorize_protocol('vless://...') == 'VLESS'
    assert p.categorize_protocol('trojan://host:443') == 'Other'
    assert p.categorize_protocol('ss://host:443') == 'Shadowsocks'
    assert p.categorize_protocol('unknown://x') == 'Other'


def test_extract_host_port_vmess_base64():
    p = EnhancedConfigProcessor()
    payload = {"add": "example.com", "port": 443}
    cfg = 'vmess://' + base64.b64encode(str(payload).replace("'", '"').encode('utf-8')).decode('utf-8')
    host, port = p.extract_host_port(cfg)
    assert host == 'example.com'
    assert port == 443


def test_extract_host_port_uri_forms():
    p = EnhancedConfigProcessor()
    host, port = p.extract_host_port('trojan://user@my.host:8443')
    assert host == 'my.host'
    assert port == 8443
    host, port = p.extract_host_port('trojan://user@my.host')
    assert host is None or port is None


def test_extract_host_port_invalid_b64():
    p = EnhancedConfigProcessor()
    host, port = p.extract_host_port('vmess://!!!!!')
    assert host is None and port is None
