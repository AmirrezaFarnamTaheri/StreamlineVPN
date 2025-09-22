import pytest

from streamline_vpn.core.config_validator import ConfigurationValidator

def test_validator_url_and_scheme():
    validator = ConfigurationValidator()
    cfg = {
        "sources": {
            "unknownTier": {"urls": ["ftp://bad.test-server.example/list.txt", "http:///missing-host"]}
        },
    }
    errors = validator.validate_config(cfg)
    assert len(errors) > 0

def test_validator_cache_ttl_and_processing_ranges():
    v = ConfigurationValidator()
    cfg = {
        "sources": {"premium": ["https://ok.test-server.example/a.txt"]},
        "cache": {"ttl": -5},
        "processing": {
            "max_concurrent": 2000,
            "timeout": 0,
            "retry_attempts": "three",
        },
    }
    errors = v.validate_config(cfg)
    assert len(errors) > 0

def test_validator_tier_dict_and_protocols():
    v = ConfigurationValidator()
    cfg = {
        "sources": {
            "tier_1": {
                "urls": [
                    {"url": "https://ok.test-server.example/a.txt", "weight": 0.5, "protocols": ["vmess", "bogus"]},
                    {"url": "https://ok.test-server.example/b.txt", "weight": 2.0},
                ]
            },
        }
    }
    errors = v.validate_config(cfg)
    assert len(errors) > 0

def test_validator_validate_config_file_not_found(tmp_path):
    v = ConfigurationValidator()
    errors = v.validate_config_file(str(tmp_path / "missing.yaml"))
    assert len(errors) > 0
