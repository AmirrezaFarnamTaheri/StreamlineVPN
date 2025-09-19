import pytest
import asyncio
from unittest.mock import patch, MagicMock, mock_open, AsyncMock

from streamline_vpn.merger.aggregator_tool import Aggregator
from streamline_vpn.merger.config import Settings

@pytest.fixture
def mock_settings():
    """Provides a default Settings object for tests."""
    return Settings()

@pytest.fixture
async def mock_aiohttp_session():
    """Provides a mock aiohttp.ClientSession."""
    session = MagicMock()
    # Create a future on the running loop
    future = asyncio.get_running_loop().create_future()
    future.set_result("vless://config1")
    session.request.return_value.__aenter__.return_value.text = future
    session.request.return_value.__aenter__.return_value.status = 200
    return session

class TestAggregator:
    """Tests for the Aggregator class."""

    def test_init(self, mock_settings):
        """Test the initialization of the Aggregator."""
        aggregator = Aggregator(cfg=mock_settings)
        assert aggregator.cfg == mock_settings
        assert aggregator.stats["valid_sources"] == 0

    @pytest.mark.asyncio
    async def test_check_and_update_sources_simple(self, mock_settings, mock_aiohttp_session):
        """Test a simple case of checking and updating sources."""
        aggregator = Aggregator(cfg=mock_settings)

        sources_content = "http://source1.com\nhttp://source2.com"

        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        # Let's make the mock for the failures file more explicit
        failures_path_mock = mock_path_instance.with_suffix.return_value
        failures_path_mock.read_text.return_value = "{}"
        failures_path_mock.write_text = MagicMock()

        # This is the key to the fix. The `open` context manager in the code
        # is on the `path` object itself, not `builtins.open`.
        mock_path_instance.open = mock_open(read_data=sources_content)

        with patch('streamline_vpn.merger.aggregator_tool.Path', return_value=mock_path_instance), \
             patch('streamline_vpn.merger.aggregator_tool.fetch_text', new_callable=AsyncMock) as mock_fetch_text, \
             patch('streamline_vpn.merger.aggregator_tool.parse_configs_from_text') as mock_parse_configs, \
             patch('streamline_vpn.merger.aggregator_tool.tqdm') as mock_tqdm:

            mock_fetch_text.side_effect = ["vless://config1", ""]
            mock_parse_configs.side_effect = [True, False]

            valid_sources = await aggregator.check_and_update_sources(
                path=mock_path_instance,
                session=mock_aiohttp_session
            )

            assert valid_sources == ["http://source1.com"]
            assert mock_fetch_text.call_count == 2
            # parse_configs is only called for the first source due to short-circuiting
            assert mock_parse_configs.call_count == 1
            failures_path_mock.write_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_and_parse_configs_simple(self, mock_settings, mock_aiohttp_session):
        """Test a simple case of fetching and parsing configs."""
        aggregator = Aggregator(cfg=mock_settings)
        sources = ["http://source1.com", "http://source2.com"]

        with patch('streamline_vpn.merger.aggregator_tool.fetch_text', new_callable=AsyncMock) as mock_fetch_text, \
             patch('streamline_vpn.merger.aggregator_tool.tqdm') as mock_tqdm:

            # Each source returns one valid config
            mock_fetch_text.side_effect = ["vless://config1", "vless://config2"]

            configs = await aggregator.fetch_and_parse_configs(
                sources=sources,
                session=mock_aiohttp_session
            )

            assert configs == {"vless://config1", "vless://config2"}
            assert mock_fetch_text.call_count == 2
