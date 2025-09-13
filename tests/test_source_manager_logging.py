import logging
from unittest.mock import Mock

from streamline_vpn.core.source_manager import SourceManager


def _security_ok():
    sec = Mock()
    sec.validate_source = Mock(return_value={"is_safe": True})
    return sec


def test_load_sources_logs_distribution(tmp_path, caplog):
    config = tmp_path / "sources.yaml"
    config.write_text(
        """
sources:
  tier_1_premium:
    urls:
      - https://example.com/a
  tier_5_unknown:
    urls:
      - https://example.com/b
  tier_bad: {}
""",
        encoding="utf-8",
    )

    with caplog.at_level(logging.INFO):
        SourceManager(str(config), security_manager=_security_ok(), fetcher_service=None)

    assert "Tier distribution" in caplog.text
    assert "Unknown tier 'tier_5_unknown'" in caplog.text
    assert "Invalid tier configuration for tier_bad" in caplog.text

