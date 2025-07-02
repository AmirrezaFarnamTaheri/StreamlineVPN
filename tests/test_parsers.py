import base64
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from advanced_methods.http_injector_merger import parse_ehi
from advanced_methods.tunnel_bridge_merger import parse_line


def test_parse_ehi_plain():
    data = b"payload1\npayload2\n"
    result = parse_ehi(data)
    assert result == ["payload1", "payload2"]


def test_parse_ehi_base64():
    raw = "line1\nline2"
    b64 = base64.b64encode(raw.encode())
    result = parse_ehi(b64)
    assert result == ["line1", "line2"]


def test_parse_ehi_zip(tmp_path):
    import zipfile, json
    payload = {"payload": "zipline"}
    zpath = tmp_path / "test.ehi"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("config.json", json.dumps(payload))
    data = zpath.read_bytes()
    result = parse_ehi(data)
    assert result == ["zipline"]


def test_parse_line():
    assert parse_line("ssh://user:pass@host:22") == "ssh://user:pass@host:22"
