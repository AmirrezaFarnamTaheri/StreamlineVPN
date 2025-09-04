#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for VPN Merger
===================================================

Advanced integration testing including:
- End-to-end workflow testing
- Component integration testing
- API integration testing
- Database integration testing
- External service integration testing
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from vpn_merger.core.merger import VPNSubscriptionMerger
from vpn_merger.core.source_manager import SourceManager
from vpn_merger.core.source_processor import SourceProcessor
from vpn_merger.core.source_validator import UnifiedSourceValidator
from vpn_merger.core.output.manager import OutputManager
from vpn_merger.ml.enhanced_quality_predictor import EnhancedConfigQualityPredictor
from vpn_merger.web.config_generator import VPNConfigGenerator


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_merger_workflow(self):
        """Test complete VPN merger workflow from sources to output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize components
            source_manager = SourceManager()
            source_processor = SourceProcessor()
            output_manager = OutputManager(temp_dir)
            
            # Mock sources for testing
            test_sources = [
                "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge_base64.txt"
            ]
            
            # Test source processing
            results = await source_processor.process_sources_batch(test_sources, batch_size=1)
            
            # Verify results
            assert results is not None
            assert len(results) > 0
            
            # Test output generation
            output_files = output_manager.save_results(results)
            
            # Verify output files
            assert "raw" in output_files
            assert "base64" in output_files
            assert "csv" in output_files
            
            # Verify files exist
            for file_type, file_path in output_files.items():
                assert Path(file_path).exists()
                assert Path(file_path).stat().st_size > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ml_quality_prediction_workflow(self):
        """Test ML quality prediction integration."""
        # Initialize ML predictor
        predictor = EnhancedConfigQualityPredictor()
        
        # Test configuration
        test_config = "vmess://test-config"
        
        # Test quality prediction
        result = await predictor.predict_quality(test_config, source_reliability=0.8)
        
        # Verify result
        assert result is not None
        assert 0.0 <= result.quality_score <= 1.0
        assert result.confidence >= 0.0
        assert result.model_version is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_web_interface_workflow(self):
        """Test web interface integration."""
        generator = VPNConfigGenerator(host="127.0.0.1", port=8081)
        
        try:
            # Start web server
            await generator.start()
            
            # Test server is running
            assert generator.site is not None
            
            # Test configuration generation
            test_data = {
                "host": "example.com",
                "port": 443,
                "uuid": "12345678-1234-1234-1234-123456789012",
                "sni": "example.com",
                "pbk": "test_public_key"
            }
            
            # Test VLESS generation
            vless_result = await generator._handle_generate_vless(
                AsyncMock(json=lambda: test_data)
            )
            
            # Verify result
            assert vless_result.status == 200
            
        finally:
            await generator.stop()


class TestComponentIntegration:
    """Test component integration."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_source_manager_validator_integration(self):
        """Test source manager and validator integration."""
        source_manager = SourceManager(use_enhanced_validation=True)
        
        # Test source validation
        sources = source_manager.get_all_sources()
        
        if sources:
            async with UnifiedSourceValidator() as validator:
                results = await validator.validate_multiple_sources(sources[:5])
                
                # Verify validation results
                assert len(results) > 0
                for result in results:
                    assert result.url is not None
                    assert result.timestamp is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_processor_output_integration(self):
        """Test processor and output manager integration."""
        processor = SourceProcessor()
        output_manager = OutputManager()
        
        # Test processing and output
        test_sources = ["https://httpbin.org/base64/SFRUUEJJTiBpcyBhd2Vzb21l"]
        
        results = await processor.process_sources_batch(test_sources, batch_size=1)
        
        if results:
            output_files = output_manager.save_results(results)
            
            # Verify integration
            assert len(output_files) > 0
            for file_type, file_path in output_files.items():
                assert Path(file_path).exists()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ml_processor_integration(self):
        """Test ML predictor and processor integration."""
        processor = SourceProcessor()
        predictor = EnhancedConfigQualityPredictor()
        
        # Test processing with quality prediction
        test_sources = ["https://httpbin.org/base64/SFRUUEJJTiBpcyBhd2Vzb21l"]
        
        results = await processor.process_sources_batch(test_sources, batch_size=1)
        
        if results:
            # Test quality prediction for each result
            for config in results[:3]:  # Test first 3 configs
                quality_result = await predictor.predict_quality(
                    str(config), source_reliability=0.8
                )
                
                # Verify quality prediction
                assert quality_result.quality_score >= 0.0
                assert quality_result.quality_score <= 1.0


class TestAPIIntegration:
    """Test API integration."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_graphql_api_integration(self):
        """Test GraphQL API integration."""
        from vpn_merger.web.graphql.schema import schema
        
        # Test GraphQL schema
        assert schema is not None
        
        # Test basic query
        query = """
        query {
            __schema {
                types {
                    name
                }
            }
        }
        """
        
        # Verify schema is accessible
        assert len(schema.types) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rest_api_integration(self):
        """Test REST API integration."""
        generator = VPNConfigGenerator(host="127.0.0.1", port=8082)
        
        try:
            await generator.start()
            
            # Test API endpoints
            endpoints = [
                "/api/v1/generate/vless",
                "/api/v1/generate/singbox",
                "/api/v1/generate/wireguard",
                "/api/v1/generate/shadowsocks",
                "/api/v1/utils/uuid",
                "/api/v1/utils/password"
            ]
            
            # Verify endpoints are registered
            for endpoint in endpoints:
                # Check if endpoint is in router
                assert any(route.path == endpoint for route in generator.app.router.routes())
            
        finally:
            await generator.stop()


class TestErrorHandlingIntegration:
    """Test error handling integration."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_propagation_integration(self):
        """Test error propagation across components."""
        processor = SourceProcessor()
        
        # Test with invalid sources
        invalid_sources = [
            "invalid_url",
            "https://nonexistent-domain-12345.com",
            "not_a_url_at_all"
        ]
        
        results = await processor.process_sources_batch(invalid_sources, batch_size=1)
        
        # Verify error handling
        assert results is not None
        # Results may be empty due to invalid sources, which is expected

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_timeout_handling_integration(self):
        """Test timeout handling integration."""
        validator = UnifiedSourceValidator(timeout=1)  # Very short timeout
        
        try:
            async with validator:
                # Test with slow service
                result = await validator.validate_source("https://httpbin.org/delay/5")
                
                # Verify timeout handling
                assert result is not None
                assert not result.accessible
                assert "timeout" in result.error.lower() or "time" in result.error.lower()
                
        except Exception as e:
            # Timeout handling may vary
            assert "timeout" in str(e).lower() or "time" in str(e).lower()


class TestPerformanceIntegration:
    """Test performance integration."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_processing_integration(self):
        """Test concurrent processing integration."""
        processor = SourceProcessor()
        
        # Test concurrent processing
        test_sources = [
            "https://httpbin.org/json",
            "https://httpbin.org/base64/SFRUUEJJTiBpcyBhd2Vzb21l",
            "https://httpbin.org/headers"
        ] * 3  # 9 sources total
        
        import time
        start_time = time.time()
        
        results = await processor.process_sources_batch(test_sources, batch_size=5)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify concurrent processing
        assert results is not None
        assert processing_time < 30  # Should complete within 30 seconds

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_usage_integration(self):
        """Test memory usage integration."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process multiple sources
        processor = SourceProcessor()
        test_sources = ["https://httpbin.org/json"] * 10
        
        results = await processor.process_sources_batch(test_sources, batch_size=5)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Verify memory usage is reasonable (less than 100MB increase)
        assert memory_increase < 100 * 1024 * 1024  # 100MB


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])