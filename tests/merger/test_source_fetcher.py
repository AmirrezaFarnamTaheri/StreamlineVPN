import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from contextlib import asynccontextmanager
import aiohttp

from streamline_vpn.merger.source_fetcher import (
    fetch_text,
    parse_first_configs,
    UnifiedSources,
    AsyncSourceFetcher,
)
from streamline_vpn.merger.result_processor import EnhancedConfigProcessor

@pytest.mark.asyncio
async def test_fetch_text_success():
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.text = AsyncMock(return_value="some text")

    @asynccontextmanager
    async def mock_get_cm(*args, **kwargs):
        yield mock_resp

    with patch("aiohttp.ClientSession.get", side_effect=lambda *args, **kwargs: mock_get_cm()):
        async with aiohttp.ClientSession() as session:
            text = await fetch_text(session, "http://example.com")
            assert text == "some text"


@pytest.mark.asyncio
async def test_fetch_text_retry_and_fail():
    mock_resp = AsyncMock()
    mock_resp.status = 500

    @asynccontextmanager
    async def mock_get_cm(*args, **kwargs):
        yield mock_resp

    with patch("aiohttp.ClientSession.get", side_effect=lambda *args, **kwargs: mock_get_cm()), patch("asyncio.sleep", new_callable=AsyncMock):
        async with aiohttp.ClientSession() as session:
            text = await fetch_text(session, "http://example.com", retries=3)
            assert text is None

def test_parse_first_configs():
    text = """
    vmess://config1
    vless://config2
    ss://config3
    """
    configs = parse_first_configs(text, limit=2)
    assert len(configs) == 2
    assert configs == ["vmess://config1", "vless://config2"]

def test_parse_first_configs_base64():
    text = "dm1lc3M6Ly9jb25maWc0CnZtZXNzOi8vY29uZmlnNQ==" # vmess://config4\nvmess://config5
    configs = parse_first_configs(text)
    assert len(configs) == 2
    assert configs == ["vmess://config4", "vmess://config5"]


def test_unified_sources_load_from_file(tmp_path):
    sources_file = tmp_path / "sources.txt"
    sources_file.write_text("http://source1.com\nhttp://source2.com")
    sources = UnifiedSources.load(sources_file)
    assert sources == ["http://source1.com", "http://source2.com"]

def test_unified_sources_load_fallback():
    # Using a non-existent file path to trigger fallback
    with patch("pathlib.Path.exists", return_value=False):
        sources = UnifiedSources.load("non_existent_file.txt")
        assert sources == UnifiedSources.FALLBACK_SOURCES

def test_unified_sources_get_all_sources(tmp_path):
    sources_file = tmp_path / "sources.txt"
    sources_file.write_text("http://source1.com\nhttp://source2.com")
    sources = UnifiedSources.get_all_sources(sources_file)
    assert sources == ["http://source1.com", "http://source2.com"]

    # Test fallback
    with patch("pathlib.Path.exists", return_value=False):
        sources = UnifiedSources.get_all_sources("non_existent_file.txt")
        assert sources == UnifiedSources.FALLBACK_SOURCES

@pytest.fixture
def mock_processor():
    return EnhancedConfigProcessor()

@pytest.mark.asyncio
async def test_async_source_fetcher_init_and_close(mock_processor):
    fetcher = AsyncSourceFetcher(processor=mock_processor, seen_hashes=set())
    # In an async context, the session is created eagerly.
    assert fetcher.session is not None
    assert fetcher._own_session is True

    session = fetcher.session
    async with fetcher:
        assert not session.closed

    assert fetcher.session is None
    assert session.closed

@pytest.mark.asyncio
async def test_async_source_fetcher_with_external_session(mock_processor):
    mock_session = AsyncMock()
    fetcher = AsyncSourceFetcher(processor=mock_processor, seen_hashes=set(), session=mock_session)
    assert fetcher.session is mock_session
    assert not fetcher._own_session

    await fetcher.close()
    # external session should not be closed
    mock_session.close.assert_not_called()

@pytest.mark.asyncio
async def test_test_source_availability_success():
    mock_resp = AsyncMock()
    mock_resp.status = 200

    @asynccontextmanager
    async def mock_head_cm(*args, **kwargs):
        yield mock_resp

    with patch("aiohttp.ClientSession.head", side_effect=lambda *args, **kwargs: mock_head_cm()):
        async with aiohttp.ClientSession() as session:
            fetcher = AsyncSourceFetcher(EnhancedConfigProcessor(), set(), session=session)
            is_available = await fetcher.test_source_availability("http://example.com")
            assert is_available is True

@pytest.mark.asyncio
async def test_test_source_availability_fail():
    mock_resp = AsyncMock()
    mock_resp.status = 404

    mock_get_resp = AsyncMock()
    mock_get_resp.status = 404

    @asynccontextmanager
    async def mock_head_cm(*args, **kwargs):
        yield mock_resp

    @asynccontextmanager
    async def mock_get_cm(*args, **kwargs):
        yield mock_get_resp

    with patch("aiohttp.ClientSession.head", side_effect=lambda *args, **kwargs: mock_head_cm()), patch("aiohttp.ClientSession.get", side_effect=lambda *args, **kwargs: mock_get_cm()):
        async with aiohttp.ClientSession() as session:
            fetcher = AsyncSourceFetcher(EnhancedConfigProcessor(), set(), session=session)
            is_available = await fetcher.test_source_availability("http://example.com")
            assert is_available is False
