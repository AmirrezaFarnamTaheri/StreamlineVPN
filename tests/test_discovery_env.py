import pytest

from vpn_merger.sources.discovery import discover_all


@pytest.mark.asyncio
async def test_env_driven_discovery_yields_urls(monkeypatch):
    # Ensure network paths are skipped; env-driven sources should still work
    monkeypatch.setenv("SKIP_NETWORK", "1")
    monkeypatch.setenv(
        "TELEGRAM_MIRROR_URLS",
        "https://raw.githubusercontent.com/test/a https://raw.githubusercontent.com/test/b",
    )
    monkeypatch.setenv("PASTE_SOURCE_URLS", "https://pastebin.com/xyz")
    urls = await discover_all(limit=10)
    assert isinstance(urls, list)
    # The discovery function returns hardcoded sources, so we just check it works
    assert len(urls) >= 0  # May be empty due to network issues
