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


def test_parse_line():
    assert parse_line("ssh://user:pass@host:22") == "ssh://user:pass@host:22"
