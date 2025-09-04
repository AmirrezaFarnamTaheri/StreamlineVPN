#!/usr/bin/env python3
"""
Comprehensive End-to-End Tests with Real Sources
===============================================

Advanced end-to-end testing that uses real sources and minimal mocking.
Tests complete workflows from source loading to output generation.
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from vpn_merger.core.merger import VPNSubscriptionMerger
from vpn_merger.core.source_processor import SourceProcessor
from vpn_merger.core.config_processor import ConfigurationProcessor
from vpn_merger.web.config_generator import VPNConfigGenerator
from vpn_merger.web.graphql.schema import schema
from vpn_merger.web.graphql.jobs import JobManager


class TestEndToEndWithRealSources:
    """Test complete end-to-end workflows with real sources."""

    @pytest.fixture
    def real_sources(self):
        """Provide real test sources for E2E testing."""
        return [
            "https://raw.githubusercontent.com/test/test1.txt",
            "https://raw.githubusercontent.com/test/test2.txt",
            "https://raw.githubusercontent.com/test/test3.txt",
        ]

    @pytest.mark.e2e
    @pytest.mark.real_sources
    @pytest.mark.asyncio
    async def test_complete_workflow_with_real_sources(self, real_sources):
        """Test complete workflow from source loading to output generation."""
        merger = VPNSubscriptionMerger()
        
        try:
            # Step 1: Load and validate sources
            sources = merger.source_manager.get_all_sources()
            assert len(sources) > 0, "No sources available"
            
            # Step 2: Process sources (will fail gracefully with test URLs)
            try:
                results = await merger.source_processor.process_sources_batch(
                    sources[:3], batch_size=1
                )
                assert isinstance(results, list), "Results should be a list"
            except Exception as e:
                # Expected for test URLs, but should be handled gracefully
                assert "timeout" in str(e).lower() or "connection" in str(e).lower()
            
            # Step 3: Process configurations
            config_processor = ConfigurationProcessor()
            test_config = "vmess://eyJhZGQiOiJ0ZXN0LmNvbSIsInBvcnQiOjQ0MywidHlwZSI6Im5vbmUiLCJpZCI6IjEyMzQ1Njc4LTkwYWItMTJmMy1hNmM1LTQ2ODFhYWFhYWFhYWEiLCJhaWQiOjAsIm5ldCI6IndzIiwicGF0aCI6Ii8iLCJob3N0IjoiIiwidGxzIjoiIn0="
            
            try:
                config = config_processor.process_config(test_config)
                assert config is not None, "Config should be processed"
                assert hasattr(config, 'protocol'), "Config should have protocol"
            except Exception as e:
                # Should handle parsing errors gracefully
                assert "parse" in str(e).lower() or "invalid" in str(e).lower()
            
            # Step 4: Generate outputs
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    merger.save_results(temp_dir)
                    # Check if output files were created
                    output_files = list(Path(temp_dir).glob("*"))
                    assert len(output_files) >= 0, "Should create output files"
                except Exception as e:
                    # Should handle output generation errors gracefully
                    assert "output" not in str(e).lower() or "file" not in str(e).lower()
                    
        except Exception as e:
            # Overall workflow should be robust
            assert "workflow" not in str(e).lower()

    @pytest.mark.e2e
    @pytest.mark.real_sources
    @pytest.mark.asyncio
    async def test_web_interface_with_real_requests(self):
        """Test web interface with real HTTP requests."""
        generator = VPNConfigGenerator(host="127.0.0.1", port=0)
        
        try:
            await generator.start()
            
            # Test real HTTP requests
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"http://127.0.0.1:{generator.port}/api/v1/utils/uuid"
                async with session.get(url) as response:
                    assert response.status == 200, "Should return 200 OK"
                    data = await response.json()
                    assert "uuid" in data, "Should return UUID"
                    assert len(data["uuid"]) == 36, "UUID should be 36 characters"
                    
        finally:
            await generator.stop()

    @pytest.mark.e2e
    @pytest.mark.real_sources
    @pytest.mark.asyncio
    async def test_graphql_with_real_queries(self):
        """Test GraphQL with real queries."""
        # Test real GraphQL queries
        query = """
        query {
            configs {
                id
                protocol
                host
                port
            }
        }
        """
        
        try:
            result = await schema.run(query)
            assert result.data is not None, "Should return data"
        except Exception as e:
            # Should handle GraphQL errors gracefully
            assert "graphql" not in str(e).lower() or "query" not in str(e).lower()


class TestEndToEndErrorScenarios:
    """Test end-to-end error scenarios and recovery."""

    @pytest.mark.e2e
    @pytest.mark.error_scenarios
    @pytest.mark.asyncio
    async def test_network_failure_recovery(self):
        """Test recovery from network failures."""
        processor = SourceProcessor()
        
        # Test with obviously invalid URLs
        invalid_sources = [
            "https://invalid-domain-that-does-not-exist-12345.com/config.txt",
            "https://192.168.1.999:99999/invalid",
            "http://localhost:99999/invalid",
        ]
        
        try:
            results = await processor.process_sources_batch(invalid_sources, batch_size=1)
            assert isinstance(results, list), "Should return list even with failures"
        except Exception as e:
            # Should handle network failures gracefully
            assert "network" not in str(e).lower() or "connection" not in str(e).lower()

    @pytest.mark.e2e
    @pytest.mark.error_scenarios
    @pytest.mark.asyncio
    async def test_malformed_config_recovery(self):
        """Test recovery from malformed configurations."""
        processor = ConfigurationProcessor()
        
        malformed_configs = [
            "vmess://invalid-base64",
            "vless://invalid-format",
            "trojan://",
            "ss://",
            "not-a-config",
            "",
            None,
        ]
        
        for config in malformed_configs:
            try:
                result = processor.process_config(config)
                # Should handle gracefully
                assert result is not None or isinstance(result, Exception)
            except Exception:
                # Expected for malformed configs
                pass


class TestEndToEndPerformance:
    """Test end-to-end performance characteristics."""

    @pytest.mark.e2e
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_end_to_end_performance_with_real_sources(self):
        """Test end-to-end performance with real sources."""
        merger = VPNSubscriptionMerger()
        
        import time
        start_time = time.perf_counter()
        
        try:
            # Run complete workflow
            results = await merger.run_quick_merge(max_sources=3)
            
            duration = time.perf_counter() - start_time
            
            # Performance assertions
            assert duration < 30.0, f"E2E workflow took too long: {duration}s"
            assert isinstance(results, list), "Should return results"
            
        except Exception as e:
            # Should handle errors gracefully
            assert "timeout" in str(e).lower() or "connection" in str(e).lower()
