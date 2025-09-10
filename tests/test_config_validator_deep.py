import pytest

from streamline_vpn.core.config_validator import ConfigurationValidator


def test_validator_url_and_scheme_and_deprecated_fields():
    validator = ConfigurationValidator()
    cfg = {
        # Current field containing invalid urls
        "sources": {
            "unknownTier": {"urls": ["ftp://bad.example.com/list.txt", "http:///missing-host"]}
        },
        # Deprecated alias present to ensure deprecation warning is raised
        "vpn_sources": {"legacy": ["https://ok.example.com/a.txt"]},
    }
    res = validator.validate_config(cfg)
    # Missing section error is avoided because vpn_sources exists but is deprecated
    assert any(i["type"] == "DEPRECATED_FIELD" for i in res["issues"])
    # Invalid URL and scheme detected
    assert any(i["type"] == "INVALID_SCHEME" for i in res["issues"]) or any(
        i["type"] == "INVALID_URL" for i in res["issues"]
    )

    # Suggestions include recommended sections
    assert any("Consider adding \"processing\"" in s for s in res["suggestions"])  # noqa: E501


def test_validator_cache_ttl_and_processing_ranges():
    v = ConfigurationValidator()
    cfg = {
        "sources": {"premium": ["https://ok.example.com/a.txt"]},
        "cache": {"ttl": -5},  # invalid negative ttl
        "processing": {
            "max_concurrent": 2000,  # will warn + autofix later
            "timeout": 0,  # out of range (warn)
            "retry_attempts": "three",  # invalid type (error)
            "retry_delay": -1,  # out of range (warn)
            "batch_size": 0,  # out of range (warn)
        },
    }
    res = v.validate_config(cfg)
    # TTL invalid
    assert any(i["field"] == "cache.ttl" and i["severity"] == "error" for i in res["issues"])  # noqa: E501
    # numeric field type error
    assert any(i["field"] == "processing.retry_attempts" and i["type"] == "INVALID_TYPE" for i in res["issues"])  # noqa: E501
    # out of range warnings exist
    assert any(i["type"] == "OUT_OF_RANGE" for i in res["issues"])  # at least one

    fixed, fixes = v.auto_fix_config(cfg)
    # max_concurrent clamped down
    assert fixed["processing"]["max_concurrent"] in (100,)
    # No KeyError on sources
    assert "sources" in fixed


def test_validator_tier_dict_and_protocols():
    v = ConfigurationValidator()
    cfg = {
        "sources": {
            "tier_1": {
                "urls": [
                    {"url": "https://ok.example.com/a.txt", "weight": 0.5, "protocols": ["vmess", "bogus"]},
                    {"url": "https://ok.example.com/b.txt", "weight": 2.0},  # out of range -> warning
                ]
            },
        }
    }
    res = v.validate_config(cfg)
    # Unknown protocol warning present
    assert any(i["type"] == "UNKNOWN_PROTOCOL" for i in res["issues"])
    # Weight out of range warning present
    assert any(i["field"].endswith("weight") and i["type"] == "OUT_OF_RANGE" for i in res["issues"])  # noqa: E501


def test_validator_validate_config_file_not_found(tmp_path):
    v = ConfigurationValidator()
    res = v.validate_config_file(str(tmp_path / "missing.yaml"))
    assert res["valid"] is False and res.get("error") == "FILE_NOT_FOUND"
