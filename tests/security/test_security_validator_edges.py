import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.security.validator import SecurityValidator


def test_security_validator_localhost_and_ipv6():
    v = SecurityValidator()
    assert v._is_valid_domain("localhost") is True
    assert v._is_valid_domain("127.0.0.1") is True
    assert v._is_valid_domain("::1") is True


def test_security_validator_score_fields():
    v = SecurityValidator()
    data = {"url": "http://example.com"}
    res = v.run_security_checks(data)
    assert "checks_failed" in res
    assert "overall_score" in res

