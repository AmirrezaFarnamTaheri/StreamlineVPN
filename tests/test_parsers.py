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

if "aiohttp" not in sys.modules:
    aiohttp_stub = types.ModuleType("aiohttp")
    aiohttp_stub.ClientSession = object
    sys.modules["aiohttp"] = aiohttp_stub

from advanced_methods.http_injector_merger import parse_ehi
from advanced_methods.tunnel_bridge_merger import parse_line


def test_parse_ehi_plain():
    data = b"payload1\npayload2\n"
    result = parse_ehi(data)
    assert result == ["payload1", "payload2"]


def test_parse_line():
    assert parse_line("ssh://user:pass@host:22") == "ssh://user:pass@host:22"


def test_parse_ehi_base64():
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


import pytest


def test_parse_line_none():
    with pytest.raises(AttributeError):
        parse_line(None)


def test_parse_line_non_string():
    with pytest.raises(AttributeError):
        parse_line(123)
