import pytest


@pytest.mark.asyncio
@pytest.mark.network
async def test_discovery_returns_candidates():
    try:
        from vpn_merger.core.source_discovery import discover_sources  # type: ignore
    except Exception:
        pytest.skip("discovery module unavailable")

    urls = await discover_sources()
    assert isinstance(urls, list)
    # Conservative lower bound in CI/network-restricted envs
    assert len(urls) >= 20
