from streamline_vpn.core.config_validator import ConfigurationValidator

def test_validator_missing_sources():
    validator = ConfigurationValidator()
    cfg = {}
    errors = validator.validate_config(cfg)
    assert len(errors) > 0
    assert "Missing 'sources' section" in errors[0]

def test_validator_sources_and_output_formats():
    validator = ConfigurationValidator()
    cfg = {
        "sources": {
            "premium": {
                "urls": [
                    "https://test-server.example/a.txt",
                    {"url": "https://test-server.example/b.txt", "weight": 0.9, "protocols": ["vmess", "vless", "bogus"]},
                ]
            },
            "tier_1": ["https://test-server.example/c.txt", 123],
        },
        "output": {"formats": ["json", "clash", "unknown"]},
        "processing": {"max_concurrent": 5000, "timeout": 0},
    }
    errors = validator.validate_config(cfg)
    assert len(errors) > 0
