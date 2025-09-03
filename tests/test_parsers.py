import base64
import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Provide minimal stubs for external dependencies so the modules under test can
# be imported without installing the real packages.
if "vpn_merger" not in sys.modules:
    stub = types.ModuleType("vpn_merger")
    stub.CONFIG = types.SimpleNamespace(proxy=None, test_timeout=1)
    sys.modules["vpn_merger"] = stub

from advanced_methods.http_injector_merger import parse_ehi
from advanced_methods.tunnel_bridge_merger import parse_line


def test_parse_ehi_plain():
    data = b"payload1\npayload2\n"
    result = parse_ehi(data)
    assert result == ["payload1", "payload2"]


def test_parse_ehi_base64_simple():
    raw = "line1\nline2"
    b64 = base64.b64encode(raw.encode())
    result = parse_ehi(b64)
    assert result == ["line1", "line2"]


def test_parse_ehi_zip(tmp_path):
    import json
    import zipfile

    payload = {"payload": "zipline"}
    zpath = tmp_path / "test.ehi"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("config.json", json.dumps(payload))
    data = zpath.read_bytes()
    result = parse_ehi(data)
    assert result == ["zipline"]


def test_parse_line_valid():
    assert parse_line("ssh://user:pass@host:22") == "ssh://user:pass@host:22"
    assert parse_line(" SSH://user@host:2222 ") == "ssh://user@host:2222"
    assert parse_line("socks5://host:1080") == "socks5://host:1080"


def test_parse_ehi_base64_advanced():
    text = "payload1\npayload2\n"
    b64 = base64.b64encode(text.encode("utf-8"))
    result = parse_ehi(b64)
    assert result == ["payload1", "payload2"]


def test_parse_ehi_zip():
    import io
    import json
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("cfg.json", json.dumps({"payload": "zip_payload"}))
    data = buf.getvalue()
    result = parse_ehi(data)
    assert result == ["zip_payload"]


def test_parse_ehi_base64_zip():
    """Base64 string containing a ZIP archive should not crash."""
    import io
    import json
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("cfg.json", json.dumps({"payload": "zip_payload"}))
    b64 = base64.b64encode(buf.getvalue())
    result = parse_ehi(b64)
    assert len(result) == 1
    assert result[0].startswith("PK")


import pytest


@pytest.mark.parametrize(
    "line",
    [
        "noscheme",
        "ssh://host",
        "ssh://user@:22",
        "ssh://user:pass@host:notnum",
        None,
        123,
    ],
)
def test_parse_line_invalid(line):
    with pytest.raises((ValueError, TypeError)):
        parse_line(line)


def test_parse_ehi_invalid_base64():
    data = b"!notbase64!"
    assert parse_ehi(data) == ["!notbase64!"]


def test_parse_ehi_zip_invalid_json():
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("cfg.json", "notjson")
    with pytest.raises(Exception):
        parse_ehi(buf.getvalue())


def test_parse_ehi_none():
    with pytest.raises(AttributeError):
        parse_ehi(None)


def test_parse_ehi_base64_payloads():
    """Base64-encoded text should yield payload lines."""
    text = "alpha\nbeta\n"
    b64 = base64.b64encode(text.encode("utf-8"))
    result = parse_ehi(b64)
    assert result == ["alpha", "beta"]


def test_parse_ehi_zip_json_payload(tmp_path):
    """A small .ehi ZIP archive containing config.json with a payload."""
    import json
    import zipfile

    path = tmp_path / "small.ehi"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("config.json", json.dumps({"payload": "tiny"}))

    data = path.read_bytes()
    result = parse_ehi(data)
    assert result == ["tiny"]
