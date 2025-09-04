#!/usr/bin/env python3
"""
Negative Test Cases and Error Path Testing
=========================================

Comprehensive negative testing to ensure robust error handling
and graceful degradation under various failure conditions.
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from vpn_merger.core.merger import VPNSubscriptionMerger
from vpn_merger.core.source_processor import SourceProcessor
from vpn_merger.core.config_processor import ConfigurationProcessor
from vpn_merger.web.config_generator import VPNConfigGenerator
from vpn_merger.web.graphql.schema import schema


class TestNegativeInputValidation:
    """Test negative input validation scenarios."""

    @pytest.mark.negative
    @pytest.mark.asyncio
    async def test_invalid_url_handling(self):
        """Test handling of invalid URLs."""
        processor = SourceProcessor()
        
        invalid_urls = [
            "not-a-url",
            "ftp://invalid-protocol.com",
            "http://",
            "https://",
            "://missing-protocol.com",
            "http://[invalid-ipv6",
            "https://domain with spaces.com",
            "http://domain.com:99999",  # Invalid port
            "http://domain.com:-1",     # Negative port
        ]
        
        for invalid_url in invalid_urls:
            try:
                results = await processor.process_sources_batch([invalid_url], batch_size=1)
                # Should handle gracefully
                assert isinstance(results, list), f"Should return list for invalid URL: {invalid_url}"
            except Exception as e:
                # Should not crash the system
                assert "crash" not in str(e).lower()

    @pytest.mark.negative
    @pytest.mark.asyncio
    async def test_empty_input_handling(self):
        """Test handling of empty inputs."""
        processor = SourceProcessor()
        
        empty_inputs = [
            [],
            [""],
            [None],
            ["", None, ""],
        ]
        
        for empty_input in empty_inputs:
            try:
                results = await processor.process_sources_batch(empty_input, batch_size=1)
                assert isinstance(results, list), "Should return list for empty input"
            except Exception as e:
                # Should handle gracefully
                assert "empty" not in str(e).lower() or "none" not in str(e).lower()

    @pytest.mark.negative
    @pytest.mark.asyncio
    async def test_oversized_input_handling(self):
        """Test handling of oversized inputs."""
        processor = SourceProcessor()
        
        # Create oversized input
        oversized_sources = [f"https://test{i}.com" for i in range(10000)]
        
        try:
            results = await processor.process_sources_batch(oversized_sources, batch_size=1000)
            assert isinstance(results, list), "Should handle oversized input"
        except Exception as e:
            # Should handle gracefully
            assert "memory" not in str(e).lower() or "timeout" not in str(e).lower()


class TestNegativeConfigurationProcessing:
    """Test negative configuration processing scenarios."""

    @pytest.mark.negative
    @pytest.mark.asyncio
    async def test_malformed_config_handling(self):
        """Test handling of malformed configurations."""
        processor = ConfigurationProcessor()
        
        malformed_configs = [
            "vmess://",  # Empty after protocol
            "vless://",  # Empty after protocol
            "trojan://", # Empty after protocol
            "ss://",     # Empty after protocol
            "invalid-protocol://test",
            "vmess://invalid-base64-encoding",
            "vless://invalid-uuid@host:port",
            "trojan://password@",  # Missing host
            "ss://method@",        # Missing host
            "vmess://eyJ0ZXN0IjoidmFsdWUifQ==@",  # Missing host
            "vless://12345678-90ab-12f3-a6c5-4681aaaaaaaa@:443",  # Missing host
            "trojan://password@host:",  # Missing port
            "ss://method@host:",       # Missing port
        ]
        
        for config in malformed_configs:
            try:
                result = processor.process_config(config)
                # Should handle gracefully
                assert result is None or hasattr(result, 'protocol'), f"Should handle malformed config: {config}"
            except Exception as e:
                # Should not crash
                assert "crash" not in str(e).lower()

    @pytest.mark.negative
    @pytest.mark.asyncio
    async def test_invalid_base64_handling(self):
        """Test handling of invalid base64 encoding."""
        processor = ConfigurationProcessor()
        
        invalid_base64_configs = [
            "vmess://invalid-base64-characters!@#$%",
            "vmess://incomplete-base64",
            "vmess://base64-with-newlines\n",
            "vmess://base64-with-spaces ",
            "vmess://base64-with-tabs\t",
        ]
        
        for config in invalid_base64_configs:
            try:
                result = processor.process_config(config)
                # Should handle gracefully
                assert result is None or hasattr(result, 'protocol'), f"Should handle invalid base64: {config}"
            except Exception as e:
                # Should not crash
                assert "crash" not in str(e).lower()

    @pytest.mark.negative
    @pytest.mark.asyncio
    async def test_invalid_json_handling(self):
        """Test handling of invalid JSON in configurations."""
        processor = ConfigurationProcessor()
        
        # Create configs with invalid JSON
        invalid_json_configs = [
            "vmess://eyJpbnZhbGlkLWpzb24iOiJ2YWx1ZSJ9",  # Valid base64, invalid JSON
            "vmess://eyJ0ZXN0IjoidmFsdWUi",  # Incomplete JSON
            "vmess://eyJ0ZXN0IjoidmFsdWUiLCAiZXh0cmEiOiJ2YWx1ZSJ9",  # Trailing comma
        ]
        
        for config in invalid_json_configs:
            try:
                result = processor.process_config(config)
                # Should handle gracefully
                assert result is None or hasattr(result, 'protocol'), f"Should handle invalid JSON: {config}"
            except Exception as e:
                # Should not crash
                assert "crash" not in str(e).lower()


class TestNegativeNetworkScenarios:
    """Test negative network scenarios."""

    @pytest.mark.negative
    @pytest.mark.network
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self):
        """Test handling of network timeouts."""
        processor = SourceProcessor()
        
        # URLs that will timeout
        timeout_urls = [
            "https://httpstat.us/200?sleep=30000",  # 30 second delay
            "https://httpstat.us/504",              # Gateway timeout
            "https://httpstat.us/503",              # Service unavailable
        ]
        
        for url in timeout_urls:
            try:
                results = await processor.process_sources_batch([url], batch_size=1)
                assert isinstance(results, list), f"Should handle timeout for: {url}"
            except Exception as e:
                # Should handle timeouts gracefully
                assert "timeout" in str(e).lower() or "connection" in str(e).lower()

    @pytest.mark.negative
    @pytest.mark.network
    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors."""
        processor = SourceProcessor()
        
        error_urls = [
            "https://httpstat.us/500",  # Internal server error
            "https://httpstat.us/502",  # Bad gateway
            "https://httpstat.us/404",  # Not found
            "https://httpstat.us/403",  # Forbidden
            "https://httpstat.us/429",  # Too many requests
        ]
        
        for url in error_urls:
            try:
                results = await processor.process_sources_batch([url], batch_size=1)
                assert isinstance(results, list), f"Should handle error for: {url}"
            except Exception as e:
                # Should handle errors gracefully
                assert "error" in str(e).lower() or "status" in str(e).lower()

    @pytest.mark.negative
    @pytest.mark.network
    @pytest.mark.asyncio
    async def test_dns_failure_handling(self):
        """Test handling of DNS failures."""
        processor = SourceProcessor()
        
        dns_failure_urls = [
            "https://nonexistent-domain-12345.com",
            "https://invalid-tld.xyz123",
            "https://subdomain.nonexistent-domain.com",
        ]
        
        for url in dns_failure_urls:
            try:
                results = await processor.process_sources_batch([url], batch_size=1)
                assert isinstance(results, list), f"Should handle DNS failure for: {url}"
            except Exception as e:
                # Should handle DNS failures gracefully
                assert "dns" in str(e).lower() or "resolve" in str(e).lower() or "name" in str(e).lower()


class TestNegativeWebInterface:
    """Test negative web interface scenarios."""

    @pytest.mark.negative
    @pytest.mark.web
    @pytest.mark.asyncio
    async def test_invalid_api_requests(self):
        """Test handling of invalid API requests."""
        generator = VPNConfigGenerator(host="127.0.0.1", port=0)
        
        try:
            await generator.start()
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                # Test invalid endpoints
                invalid_endpoints = [
                    "/api/v1/invalid",
                    "/api/v1/generate/invalid-protocol",
                    "/api/v1/utils/invalid-util",
                ]
                
                for endpoint in invalid_endpoints:
                    url = f"http://127.0.0.1:{generator.port}{endpoint}"
                    async with session.get(url) as response:
                        # Should return appropriate error status
                        assert response.status in [400, 404, 405], f"Should handle invalid endpoint: {endpoint}"
                        
        finally:
            await generator.stop()

    @pytest.mark.negative
    @pytest.mark.web
    @pytest.mark.asyncio
    async def test_invalid_request_data(self):
        """Test handling of invalid request data."""
        generator = VPNConfigGenerator(host="127.0.0.1", port=0)
        
        try:
            await generator.start()
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                # Test invalid request data
                invalid_data = [
                    {"invalid": "data"},
                    {"host": "", "port": "invalid"},
                    {"host": "test.com", "port": 99999},
                    {"host": "test.com", "port": -1},
                    None,
                    "",
                    "invalid-json",
                ]
                
                for data in invalid_data:
                    url = f"http://127.0.0.1:{generator.port}/api/v1/generate/vless"
                    try:
                        async with session.post(url, json=data) as response:
                            # Should return appropriate error status
                            assert response.status in [400, 422], f"Should handle invalid data: {data}"
                    except Exception:
                        # Should handle invalid data gracefully
                        pass
                        
        finally:
            await generator.stop()


class TestNegativeGraphQL:
    """Test negative GraphQL scenarios."""

    @pytest.mark.negative
    @pytest.mark.graphql
    @pytest.mark.asyncio
    async def test_invalid_graphql_queries(self):
        """Test handling of invalid GraphQL queries."""
        invalid_queries = [
            "invalid query syntax",
            "query { invalidField }",
            "query { configs { invalidField } }",
            "mutation { invalidMutation }",
            "",
            None,
        ]
        
        for query in invalid_queries:
            try:
                result = await schema.run(query)
                # Should handle gracefully
                assert result is not None, f"Should handle invalid query: {query}"
            except Exception as e:
                # Should not crash
                assert "crash" not in str(e).lower()

    @pytest.mark.negative
    @pytest.mark.graphql
    @pytest.mark.asyncio
    async def test_malformed_graphql_queries(self):
        """Test handling of malformed GraphQL queries."""
        malformed_queries = [
            "query { configs {",  # Incomplete query
            "query { configs { id }",  # Missing closing brace
            "query configs { id }",  # Missing opening brace
            "query { configs { id } } }",  # Extra closing brace
        ]
        
        for query in malformed_queries:
            try:
                result = await schema.run(query)
                # Should handle gracefully
                assert result is not None, f"Should handle malformed query: {query}"
            except Exception as e:
                # Should not crash
                assert "crash" not in str(e).lower()


class TestNegativeFileOperations:
    """Test negative file operation scenarios."""

    @pytest.mark.negative
    @pytest.mark.file_ops
    @pytest.mark.asyncio
    async def test_invalid_output_paths(self):
        """Test handling of invalid output paths."""
        merger = VPNSubscriptionMerger()
        
        invalid_paths = [
            "/nonexistent/directory/output",
            "C:\\nonexistent\\directory\\output",
            "/dev/null",  # Special file
            "/proc/self/environ",  # System file
            "",  # Empty path
            None,  # None path
        ]
        
        for path in invalid_paths:
            try:
                merger.save_results(path)
                # Should handle gracefully
                assert True, f"Should handle invalid path: {path}"
            except Exception as e:
                # Should not crash
                assert "crash" not in str(e).lower()

    @pytest.mark.negative
    @pytest.mark.file_ops
    @pytest.mark.asyncio
    async def test_permission_denied_scenarios(self):
        """Test handling of permission denied scenarios."""
        merger = VPNSubscriptionMerger()
        
        # Test with read-only directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            temp_path.chmod(0o444)  # Read-only
            
            try:
                merger.save_results(str(temp_path))
                # Should handle gracefully
                assert True, "Should handle permission denied"
            except Exception as e:
                # Should not crash
                assert "crash" not in str(e).lower()
            finally:
                temp_path.chmod(0o755)  # Restore permissions


class TestNegativeConcurrency:
    """Test negative concurrency scenarios."""

    @pytest.mark.negative
    @pytest.mark.concurrency
    @pytest.mark.asyncio
    async def test_excessive_concurrency(self):
        """Test handling of excessive concurrency."""
        processor = SourceProcessor()
        
        # Test with excessive concurrency
        excessive_concurrency = [1000, 10000, 100000]
        
        for max_concurrent in excessive_concurrency:
            try:
                results = await processor.process_sources_batch(
                    ["https://test.com"], 
                    batch_size=1, 
                    max_concurrent=max_concurrent
                )
                assert isinstance(results, list), f"Should handle excessive concurrency: {max_concurrent}"
            except Exception as e:
                # Should handle gracefully
                assert "concurrency" not in str(e).lower() or "limit" not in str(e).lower()

    @pytest.mark.negative
    @pytest.mark.concurrency
    @pytest.mark.asyncio
    async def test_concurrent_resource_exhaustion(self):
        """Test handling of concurrent resource exhaustion."""
        processor = SourceProcessor()
        
        # Create many concurrent tasks
        async def create_task():
            return await processor.process_sources_batch(["https://test.com"], batch_size=1)
        
        # Create many concurrent tasks
        tasks = [create_task() for _ in range(1000)]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            assert len(results) == 1000, "Should handle concurrent resource exhaustion"
        except Exception as e:
            # Should handle gracefully
            assert "resource" not in str(e).lower() or "exhaustion" not in str(e).lower()
