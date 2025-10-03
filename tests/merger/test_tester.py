"""Tests for merger tester module."""

import asyncio
import pytest
import socket
import sys
import time
from unittest.mock import patch, MagicMock, AsyncMock

from streamline_vpn.merger.tester import NodeTester


class TestNodeTester:
    """Test cases for NodeTester class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = MagicMock()
        config.enable_url_testing = True
        config.connect_timeout = 5.0
        config.geoip_db = "/path/to/geoip.db"
        return config

    @pytest.fixture
    def tester(self, mock_config):
        """Create NodeTester instance."""
        return NodeTester(mock_config)

    def test_init(self, mock_config):
        """Test NodeTester initialization."""
        tester = NodeTester(mock_config)
        
        assert tester.config == mock_config
        assert tester.dns_cache == {}
        assert tester.resolver is None
        assert tester._geoip_reader is None

    @pytest.mark.asyncio
    async def test_test_connection_disabled(self, tester):
        """Test connection testing when disabled."""
        tester.config.enable_url_testing = False
        
        result = await tester.test_connection("example.com", 443)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_test_connection_success_without_aiodns(self, tester):
        """Test successful connection without aiodns."""
        with patch('sys.modules', {'aiodns': None}):
            with patch('asyncio.open_connection') as mock_open_connection:
                with patch('asyncio.wait_for') as mock_wait_for:
                    with patch('time.time', side_effect=[1000.0, 1000.5]):
                        # Mock successful connection
                        mock_writer = AsyncMock()
                        mock_wait_for.return_value = (None, mock_writer)
                        
                        result = await tester.test_connection("example.com", 443)
                        
                        assert result == 0.5
                        mock_wait_for.assert_called_once()
                        mock_writer.close.assert_called_once()
                        mock_writer.wait_closed.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_connection_success_with_aiodns(self, tester):
        """Test successful connection with aiodns."""
        with patch('sys.modules', {'aiodns': MagicMock()}):
            with patch('streamline_vpn.merger.tester.AsyncResolver') as mock_resolver_class:
                with patch('asyncio.open_connection'):
                    with patch('asyncio.wait_for') as mock_wait_for:
                        with patch('time.time', side_effect=[1000.0, 1000.3]):
                            # Mock resolver
                            mock_resolver = AsyncMock()
                            mock_resolver.resolve.return_value = [{"host": "192.168.1.1"}]
                            mock_resolver_class.return_value = mock_resolver
                            
                            # Mock successful connection
                            mock_writer = AsyncMock()
                            mock_wait_for.return_value = (None, mock_writer)
                            
                            result = await tester.test_connection("example.com", 443)
                            
                            assert abs(result - 0.3) < 0.01
                            assert tester.resolver is not None
                            assert tester.dns_cache["example.com"] == "192.168.1.1"

    @pytest.mark.asyncio
    async def test_test_connection_with_cached_dns(self, tester):
        """Test connection with cached DNS resolution."""
        tester.dns_cache["example.com"] = "192.168.1.1"
        
        with patch('sys.modules', {'aiodns': MagicMock()}):
            with patch('streamline_vpn.merger.tester.AsyncResolver') as mock_resolver_class:
                with patch('asyncio.open_connection'):
                    with patch('asyncio.wait_for') as mock_wait_for:
                        with patch('time.time', side_effect=[1000.0, 1000.2]):
                            # Mock resolver
                            mock_resolver = AsyncMock()
                            mock_resolver_class.return_value = mock_resolver
                            tester.resolver = mock_resolver
                            
                            # Mock successful connection
                            mock_writer = AsyncMock()
                            mock_wait_for.return_value = (None, mock_writer)
                            
                            result = await tester.test_connection("example.com", 443)
                            
                            assert abs(result - 0.2) < 0.01
                            # Should not call resolve since it's cached
                            mock_resolver.resolve.assert_not_called()

    @pytest.mark.asyncio
    async def test_test_connection_resolver_init_failure(self, tester):
        """Test connection when resolver initialization fails."""
        with patch('sys.modules', {'aiodns': MagicMock()}):
            with patch('streamline_vpn.merger.tester.AsyncResolver') as mock_resolver_class:
                with patch('asyncio.open_connection'):
                    with patch('asyncio.wait_for') as mock_wait_for:
                        with patch('time.time', side_effect=[1000.0, 1000.1]):
                            with patch('logging.debug') as mock_debug:
                                # Mock resolver initialization failure
                                mock_resolver_class.side_effect = Exception("Init failed")
                                
                                # Mock successful connection
                                mock_writer = AsyncMock()
                                mock_wait_for.return_value = (None, mock_writer)
                                
                                result = await tester.test_connection("example.com", 443)
                                
                                assert abs(result - 0.1) < 0.01
                                assert tester.resolver is None
                                mock_debug.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_connection_dns_resolve_failure(self, tester):
        """Test connection when DNS resolution fails."""
        with patch('sys.modules', {'aiodns': MagicMock()}):
            with patch('streamline_vpn.merger.tester.AsyncResolver') as mock_resolver_class:
                with patch('asyncio.open_connection'):
                    with patch('asyncio.wait_for') as mock_wait_for:
                        with patch('time.time', side_effect=[1000.0, 1000.4]):
                            with patch('logging.debug') as mock_debug:
                                # Mock resolver
                                mock_resolver = AsyncMock()
                                mock_resolver.resolve.side_effect = Exception("DNS failed")
                                mock_resolver_class.return_value = mock_resolver
                                
                                # Mock successful connection
                                mock_writer = AsyncMock()
                                mock_wait_for.return_value = (None, mock_writer)
                                
                                result = await tester.test_connection("example.com", 443)
                                
                                assert abs(result - 0.4) < 0.01
                                mock_debug.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_connection_timeout(self, tester):
        """Test connection timeout."""
        with patch('asyncio.wait_for') as mock_wait_for:
            with patch('logging.debug') as mock_debug:
                mock_wait_for.side_effect = asyncio.TimeoutError("Connection timeout")
                
                result = await tester.test_connection("example.com", 443)
                
                assert result is None
                mock_debug.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_connection_os_error(self, tester):
        """Test connection with OS error."""
        with patch('asyncio.wait_for') as mock_wait_for:
            with patch('logging.debug') as mock_debug:
                mock_wait_for.side_effect = OSError("Connection refused")
                
                result = await tester.test_connection("example.com", 443)
                
                assert result is None
                mock_debug.assert_called_once()

    @pytest.mark.asyncio
    async def test_lookup_country_disabled(self, tester):
        """Test country lookup when disabled."""
        tester.config.geoip_db = None
        
        result = await tester.lookup_country("example.com")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_lookup_country_empty_host(self, tester):
        """Test country lookup with empty host."""
        result = await tester.lookup_country("")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_lookup_country_import_error(self, tester):
        """Test country lookup with import error."""
        # Mock the geoip2 module import to fail
        import sys
        original_modules = sys.modules.copy()
        
        # Remove geoip2 from modules if it exists
        if 'geoip2' in sys.modules:
            del sys.modules['geoip2']
        if 'geoip2.database' in sys.modules:
            del sys.modules['geoip2.database']
        
        # Mock import to raise ImportError
        def mock_import(name, *args, **kwargs):
            if name.startswith('geoip2'):
                raise ImportError("No module named 'geoip2'")
            return original_modules.get(name)
        
        with patch('builtins.__import__', side_effect=mock_import):
            result = await tester.lookup_country("example.com")
            
            assert result is None
        
        # Restore modules
        sys.modules.update(original_modules)

    @pytest.mark.asyncio
    async def test_lookup_country_reader_init_failure(self, tester):
        """Test country lookup when reader initialization fails."""
        # Mock the Reader class after it's imported
        with patch('geoip2.database.Reader') as mock_reader_class:
            with patch('logging.debug') as mock_debug:
                mock_reader_class.side_effect = OSError("Database not found")
                
                result = await tester.lookup_country("example.com")
                
                assert result is None
                assert tester._geoip_reader is None
                mock_debug.assert_called_once()

    @pytest.mark.asyncio
    async def test_lookup_country_success_ip_address(self, tester):
        """Test successful country lookup with IP address."""
        with patch('geoip2.database.Reader') as mock_reader_class:
            # Mock reader and response
            mock_reader = MagicMock()
            mock_response = MagicMock()
            mock_response.country.iso_code = "US"
            mock_reader.country.return_value = mock_response
            mock_reader_class.return_value = mock_reader
            
            result = await tester.lookup_country("192.168.1.1")
            
            assert result == "US"
            assert tester._geoip_reader == mock_reader
            mock_reader.country.assert_called_once_with("192.168.1.1")

    @pytest.mark.asyncio
    async def test_lookup_country_success_hostname(self, tester):
        """Test successful country lookup with hostname."""
        with patch('geoip2.database.Reader') as mock_reader_class:
            with patch('asyncio.get_running_loop') as mock_get_loop:
                # Mock reader and response
                mock_reader = MagicMock()
                mock_response = MagicMock()
                mock_response.country.iso_code = "GB"
                mock_reader.country.return_value = mock_response
                mock_reader_class.return_value = mock_reader
                
                # Mock getaddrinfo
                mock_loop = AsyncMock()
                async def mock_getaddrinfo(host, port):
                    return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80))]
                
                mock_loop.getaddrinfo = mock_getaddrinfo
                mock_get_loop.return_value = mock_loop
                
                result = await tester.lookup_country("example.com")
                
                assert result == "GB"
                mock_reader.country.assert_called_once_with("93.184.216.34")

    @pytest.mark.asyncio
    async def test_lookup_country_address_not_found(self, tester):
        """Test country lookup with address not found error."""
        with patch('geoip2.database.Reader') as mock_reader_class:
            with patch('geoip2.errors.AddressNotFoundError', Exception):
                with patch('logging.debug') as mock_debug:
                    # Mock reader
                    mock_reader = MagicMock()
                    mock_reader.country.side_effect = Exception("Address not found")
                    mock_reader_class.return_value = mock_reader
                    
                    result = await tester.lookup_country("192.168.1.1")
                    
                    assert result is None
                    mock_debug.assert_called_once()

    @pytest.mark.asyncio
    async def test_lookup_country_getaddrinfo_error(self, tester):
        """Test country lookup with getaddrinfo error."""
        with patch('geoip2.database.Reader') as mock_reader_class:
            with patch('asyncio.get_running_loop') as mock_get_loop:
                with patch('logging.debug') as mock_debug:
                    # Mock reader
                    mock_reader = MagicMock()
                    mock_reader_class.return_value = mock_reader
                    
                    # Mock getaddrinfo failure
                    mock_loop = AsyncMock()
                    async def mock_getaddrinfo_fail(host, port):
                        raise socket.gaierror("Name resolution failed")
                    
                    mock_loop.getaddrinfo = mock_getaddrinfo_fail
                    mock_get_loop.return_value = mock_loop
                    
                    result = await tester.lookup_country("invalid.example")
                    
                    assert result is None
                    mock_debug.assert_called_once()

    @pytest.mark.asyncio
    async def test_lookup_country_with_cached_reader(self, tester):
        """Test country lookup with cached reader."""
        # Pre-initialize reader
        mock_reader = MagicMock()
        mock_response = MagicMock()
        mock_response.country.iso_code = "CA"
        mock_reader.country.return_value = mock_response
        tester._geoip_reader = mock_reader
        
        result = await tester.lookup_country("192.168.1.1")
        
        assert result == "CA"
        mock_reader.country.assert_called_once_with("192.168.1.1")

    @pytest.mark.asyncio
    async def test_close_no_resources(self, tester):
        """Test close with no resources to clean up."""
        await tester.close()
        
        # Should complete without error
        assert tester.resolver is None
        assert tester._geoip_reader is None

    @pytest.mark.asyncio
    async def test_close_with_async_resolver(self, tester):
        """Test close with async resolver."""
        mock_resolver = MagicMock()
        mock_close = AsyncMock()
        mock_resolver.close = mock_close
        tester.resolver = mock_resolver
        
        with patch('asyncio.iscoroutinefunction', return_value=True):
            await tester.close()
            
            mock_close.assert_called_once()
            assert tester.resolver is None

    @pytest.mark.asyncio
    async def test_close_with_sync_resolver(self, tester):
        """Test close with sync resolver."""
        mock_resolver = MagicMock()
        mock_close = MagicMock()
        mock_resolver.close = mock_close
        tester.resolver = mock_resolver
        
        with patch('asyncio.iscoroutinefunction', return_value=False):
            await tester.close()
            
            mock_close.assert_called_once()
            assert tester.resolver is None

    @pytest.mark.asyncio
    async def test_close_resolver_without_close_method(self, tester):
        """Test close with resolver that has no close method."""
        mock_resolver = MagicMock()
        del mock_resolver.close  # Remove close method
        tester.resolver = mock_resolver
        
        await tester.close()
        
        assert tester.resolver is None

    @pytest.mark.asyncio
    async def test_close_resolver_close_failure(self, tester):
        """Test close when resolver close fails."""
        mock_resolver = MagicMock()
        mock_close = MagicMock()
        mock_close.side_effect = Exception("Close failed")
        mock_resolver.close = mock_close
        tester.resolver = mock_resolver
        
        with patch('asyncio.iscoroutinefunction', return_value=False):
            with patch('logging.debug') as mock_debug:
                await tester.close()
                
                mock_debug.assert_called_once()
                assert tester.resolver is None

    @pytest.mark.asyncio
    async def test_close_with_async_geoip_reader(self, tester):
        """Test close with async GeoIP reader."""
        mock_reader = MagicMock()
        mock_close = AsyncMock()
        mock_reader.close = mock_close
        tester._geoip_reader = mock_reader
        
        with patch('asyncio.iscoroutinefunction', return_value=True):
            await tester.close()
            
            mock_close.assert_called_once()
            assert tester._geoip_reader is None

    @pytest.mark.asyncio
    async def test_close_with_sync_geoip_reader(self, tester):
        """Test close with sync GeoIP reader."""
        mock_reader = MagicMock()
        mock_close = MagicMock()
        mock_reader.close = mock_close
        tester._geoip_reader = mock_reader
        
        with patch('asyncio.iscoroutinefunction', return_value=False):
            await tester.close()
            
            mock_close.assert_called_once()
            assert tester._geoip_reader is None

    @pytest.mark.asyncio
    async def test_close_geoip_reader_without_close_method(self, tester):
        """Test close with GeoIP reader that has no close method."""
        mock_reader = MagicMock()
        del mock_reader.close  # Remove close method
        tester._geoip_reader = mock_reader
        
        await tester.close()
        
        assert tester._geoip_reader is None

    @pytest.mark.asyncio
    async def test_close_geoip_reader_close_failure(self, tester):
        """Test close when GeoIP reader close fails."""
        mock_reader = MagicMock()
        mock_close = MagicMock()
        mock_close.side_effect = Exception("Close failed")
        mock_reader.close = mock_close
        tester._geoip_reader = mock_reader
        
        with patch('asyncio.iscoroutinefunction', return_value=False):
            with patch('logging.debug') as mock_debug:
                await tester.close()
                
                mock_debug.assert_called_once()
                assert tester._geoip_reader is None

    @pytest.mark.asyncio
    async def test_close_both_resources(self, tester):
        """Test close with both resolver and GeoIP reader."""
        # Set up both resources
        mock_resolver = MagicMock()
        mock_resolver_close = MagicMock()
        mock_resolver.close = mock_resolver_close
        tester.resolver = mock_resolver
        
        mock_reader = MagicMock()
        mock_reader_close = MagicMock()
        mock_reader.close = mock_reader_close
        tester._geoip_reader = mock_reader
        
        with patch('asyncio.iscoroutinefunction', return_value=False):
            await tester.close()
            
            mock_resolver_close.assert_called_once()
            mock_reader_close.assert_called_once()
            assert tester.resolver is None
            assert tester._geoip_reader is None


class TestNodeTesterEdgeCases:
    """Edge case tests for NodeTester."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = MagicMock()
        config.enable_url_testing = True
        config.connect_timeout = 1.0
        config.geoip_db = "/path/to/geoip.db"
        return config

    @pytest.fixture
    def tester(self, mock_config):
        """Create NodeTester instance."""
        return NodeTester(mock_config)

    @pytest.mark.asyncio
    async def test_test_connection_with_ipv6_address(self, tester):
        """Test connection with IPv6 address."""
        with patch('asyncio.open_connection'):
            with patch('asyncio.wait_for') as mock_wait_for:
                with patch('time.time', side_effect=[1000.0, 1000.1]):
                    mock_writer = AsyncMock()
                    mock_wait_for.return_value = (None, mock_writer)
                    
                    result = await tester.test_connection("::1", 443)
                    
                    assert abs(result - 0.1) < 0.01

    @pytest.mark.asyncio
    async def test_lookup_country_with_ipv6_address(self, tester):
        """Test country lookup with IPv6 address."""
        with patch('geoip2.database.Reader') as mock_reader_class:
            mock_reader = MagicMock()
            mock_response = MagicMock()
            mock_response.country.iso_code = "US"
            mock_reader.country.return_value = mock_response
            mock_reader_class.return_value = mock_reader
            
            # IPv6 address should not match the IP regex
            with patch('asyncio.get_running_loop') as mock_get_loop:
                mock_loop = AsyncMock()
                async def mock_getaddrinfo_ipv6(host, port):
                    return [(socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('::1', 80, 0, 0))]
                
                mock_loop.getaddrinfo = mock_getaddrinfo_ipv6
                mock_get_loop.return_value = mock_loop
                
                result = await tester.lookup_country("::1")
                
                assert result == "US"

    @pytest.mark.asyncio
    async def test_resolver_with_empty_dns_result(self, tester):
        """Test resolver with empty DNS result."""
        with patch('sys.modules', {'aiodns': MagicMock()}):
            with patch('streamline_vpn.merger.tester.AsyncResolver') as mock_resolver_class:
                with patch('asyncio.open_connection'):
                    with patch('asyncio.wait_for') as mock_wait_for:
                        with patch('time.time', side_effect=[1000.0, 1000.2]):
                            # Mock resolver with empty result
                            mock_resolver = AsyncMock()
                            mock_resolver.resolve.return_value = []
                            mock_resolver_class.return_value = mock_resolver
                            
                            mock_writer = AsyncMock()
                            mock_wait_for.return_value = (None, mock_writer)
                            
                            result = await tester.test_connection("example.com", 443)
                            
                            assert abs(result - 0.2) < 0.01
                            # Should not cache empty result
                            assert "example.com" not in tester.dns_cache

    @pytest.mark.asyncio
    async def test_multiple_connection_tests_with_caching(self, tester):
        """Test multiple connection tests with DNS caching."""
        tester.dns_cache["example.com"] = "192.168.1.1"
        
        with patch('asyncio.open_connection'):
            with patch('asyncio.wait_for') as mock_wait_for:
                with patch('time.time', side_effect=[1000.0, 1000.1, 1000.2, 1000.3]):
                    mock_writer = AsyncMock()
                    mock_wait_for.return_value = (None, mock_writer)
                    
                    # First call
                    result1 = await tester.test_connection("example.com", 443)
                    # Second call should use cached DNS
                    result2 = await tester.test_connection("example.com", 443)
                    
                    assert abs(result1 - 0.1) < 0.01
                    assert abs(result2 - 0.1) < 0.01
                    assert mock_wait_for.call_count == 2
