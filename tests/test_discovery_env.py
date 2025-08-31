import os
import pytest
import asyncio

from vpn_merger.sources.discovery import discover_all


@pytest.mark.asyncio
async def test_env_driven_discovery_yields_urls(monkeypatch):
    # Ensure network paths are skipped; env-driven sources should still work
    monkeypatch.setenv('SKIP_NETWORK', '1')
    monkeypatch.setenv('TELEGRAM_MIRROR_URLS', 'https://raw.githubusercontent.com/test/a https://raw.githubusercontent.com/test/b')
    monkeypatch.setenv('PASTE_SOURCE_URLS', 'https://pastebin.com/xyz')
    urls = await discover_all(limit=10)
    assert isinstance(urls, list)
    assert any(u.endswith('/a') for u in urls)
    assert any('pastebin.com' in u for u in urls)
