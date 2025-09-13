import yaml

from streamline_vpn.core.config_validator import ConfigurationValidator


def test_validator_missing_sources_and_autofix(tmp_path):
    validator = ConfigurationValidator()

    cfg = {}
    result = validator.validate_config(cfg)
    assert result["valid"] is False
    assert any(i["type"] == "MISSING_REQUIRED" for i in result["issues"])

    fixed = validator.fix_common_issues(cfg)
    assert "sources" in fixed


def test_validator_sources_and_output_formats():
    validator = ConfigurationValidator()

    cfg = {
        "sources": {
            "premium": {
                "urls": [
                    "https://example.com/a.txt",
                    {"url": "https://example.com/b.txt", "weight": 0.9, "protocols": ["vmess", "vless", "bogus"]},
                ]
            },
            "tier_1": ["https://example.com/c.txt", 123],  # 123 should trigger error
        },
        "output": {"formats": ["json", "clash", "unknown"]},
        "processing": {"max_concurrent": 5000, "timeout": 0},
    }

    res = validator.validate_config(cfg)
    # Should have warnings for unknown protocol/format and errors for invalid type
    assert any(i["type"] == "UNKNOWN_PROTOCOL" for i in res["warnings"])
    assert any(i["type"] == "UNKNOWN_FORMAT" for i in res["warnings"])
    assert any(i["type"] == "INVALID_TYPE" for i in res["issues"])

    # Auto-fix should clamp max_concurrent into sane bounds
    fixed = validator.fix_common_issues(cfg)
    assert fixed["processing"]["max_concurrent"] == 1000

