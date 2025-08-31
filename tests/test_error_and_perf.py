#!/usr/bin/env python3
"""
Error Handling and Performance Tests
===================================

Comprehensive tests for error handling, performance, and edge cases.
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

# Import with fallbacks
try:
    import vpn_merger as vm
    from vpn_merger import VPNSubscriptionMerger
except ImportError:
    vm = None
    VPNSubscriptionMerger = None


class TestErrorHandling:
    """Test error handling and recovery mechanisms."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_invalid_sources_handling(self, temp_output_dir):
        """Test handling of invalid source URLs."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test with various invalid sources
        invalid_sources = [
            "not-a-url",
            "ftp://invalid-protocol.com",
            "https://invalid-domain-that-does-not-exist-12345.com",
            "https://httpbin.org/status/404",
            "https://httpbin.org/status/500",
            "https://httpbin.org/status/503"
        ]
        
        # Add invalid sources
        merger.add_custom_sources(invalid_sources)
        
        # Should handle gracefully without crashing
        try:
            results = await merger.run_quick_merge(max_sources=10)
            assert isinstance(results, list)
            # May be empty due to invalid sources, but should not crash
        except Exception as e:
            # Should handle errors gracefully
            assert "timeout" in str(e).lower() or "error" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, temp_output_dir):
        """Test handling of network timeouts."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test with sources that might timeout
        timeout_sources = [
            "https://httpbin.org/delay/10",  # 10 second delay
            "https://httpbin.org/delay/30"   # 30 second delay
        ]
        
        # Add timeout sources
        merger.add_custom_sources(timeout_sources)
        
        # Should handle timeouts gracefully
        try:
            results = await merger.run_quick_merge(max_sources=5)
            assert isinstance(results, list)
        except Exception as e:
            # Should handle timeouts gracefully
            assert "timeout" in str(e).lower() or "error" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_malformed_config_handling(self, temp_output_dir):
        """Test handling of malformed configuration data."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test with sources that return malformed data
        malformed_sources = [
            "https://httpbin.org/html",  # Returns HTML instead of configs
            "https://httpbin.org/json",  # Returns JSON instead of configs
            "https://httpbin.org/xml"    # Returns XML instead of configs
        ]
        
        # Add malformed sources
        merger.add_custom_sources(malformed_sources)
        
        # Should handle malformed data gracefully
        try:
            results = await merger.run_quick_merge(max_sources=5)
            assert isinstance(results, list)
        except Exception as e:
            # Should handle malformed data gracefully
            assert "error" in str(e).lower() or "timeout" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self, temp_output_dir):
        """Test error handling under concurrent load."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test with mixed valid/invalid sources under concurrent load
        mixed_sources = [
            "https://httpbin.org/status/200",  # Valid
            "https://httpbin.org/status/404",  # Invalid
            "https://httpbin.org/status/500",  # Invalid
            "https://httpbin.org/status/200",  # Valid
            "https://httpbin.org/status/503"   # Invalid
        ]
        
        # Add mixed sources
        merger.add_custom_sources(mixed_sources)
        
        # Should handle concurrent errors gracefully
        try:
            results = await merger.run_comprehensive_merge(max_concurrent=10)
            assert isinstance(results, list)
        except Exception as e:
            # Should handle concurrent errors gracefully
            assert "error" in str(e).lower() or "timeout" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_memory_error_recovery(self, temp_output_dir):
        """Test recovery from memory-related errors."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test with large number of sources to potentially trigger memory issues
        try:
            results = await merger.run_comprehensive_merge(max_concurrent=50)
            assert isinstance(results, list)
        except Exception as e:
            # Should handle memory errors gracefully
            assert "memory" in str(e).lower() or "error" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self, temp_output_dir):
        """Test graceful degradation when some components fail."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test that the system continues to work even if some sources fail
        # Note: get_processing_statistics() returns a dict, so we'll call it directly
        try:
            results = await asyncio.gather(
                merger.run_quick_merge(max_sources=3),
                merger.validate_sources_only(),
                return_exceptions=True
            )
            
            # Get statistics separately since they return dicts
            stats = merger.get_processing_statistics()
            
            # Should handle partial failures gracefully
            for result in results:
                if isinstance(result, Exception):
                    # Should be a handled exception
                    assert "error" in str(result).lower() or "timeout" in str(result).lower()
                else:
                    assert result is not None
            
        except Exception as e:
            # Should handle overall failures gracefully
            assert "error" in str(e).lower() or "timeout" in str(e).lower()


class TestPerformanceUnderStress:
    """Test performance under various stress conditions."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_high_concurrency_stress(self, temp_output_dir):
        """Test performance under high concurrency stress."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test with very high concurrency
        try:
            results = await merger.run_comprehensive_merge(max_concurrent=100)
            assert isinstance(results, list)
        except Exception as e:
            # Should handle high concurrency gracefully
            assert "concurrent" in str(e).lower() or "timeout" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_large_dataset_stress(self, temp_output_dir):
        """Test performance with large datasets."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test with large number of sources
        try:
            results = await merger.run_comprehensive_merge(max_concurrent=20)
            assert isinstance(results, list)
        except Exception as e:
            # Should handle large datasets gracefully
            assert "memory" in str(e).lower() or "timeout" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_rapid_successive_operations(self, temp_output_dir):
        """Test performance with rapid successive operations."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test rapid successive operations
        try:
            for i in range(5):
                results = await merger.run_quick_merge(max_sources=3)
                assert isinstance(results, list)
                merger.reset()  # Reset between operations
        except Exception as e:
            # Should handle rapid operations gracefully
            assert "error" in str(e).lower() or "timeout" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_mixed_workload_stress(self, temp_output_dir):
        """Test performance with mixed workload types."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test mixed workload (validation + processing + statistics)
        try:
            results = await asyncio.gather(
                merger.run_quick_merge(max_sources=5),
                merger.validate_sources_only(),
                return_exceptions=True
            )
            
            # Get statistics separately since they return dicts
            stats = merger.get_processing_statistics()
            source_stats = merger.get_source_statistics()
            
            # Should handle mixed workload gracefully
            for result in results:
                if isinstance(result, Exception):
                    assert "error" in str(result).lower() or "timeout" in str(result).lower()
                else:
                    assert result is not None
                    
        except Exception as e:
            # Should handle mixed workload gracefully
            assert "error" in str(e).lower() or "timeout" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_under_stress(self, temp_output_dir):
        """Test resource cleanup under stress conditions."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test resource cleanup under stress
        try:
            # Run multiple operations to stress the system
            for i in range(10):
                results = await merger.run_quick_merge(max_sources=2)
                assert isinstance(results, list)
                merger.reset()
                
            # Check that resources are properly cleaned up
            # This is mainly a smoke test - actual resource monitoring would require psutil
            
        except Exception as e:
            # Should handle stress gracefully
            assert "error" in str(e).lower() or "timeout" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_error_cascade_prevention(self, temp_output_dir):
        """Test prevention of error cascades."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test that errors don't cascade and break the entire system
        try:
            # Add problematic sources
            problematic_sources = [
                "https://httpbin.org/status/404",
                "https://httpbin.org/status/500",
                "https://httpbin.org/status/503",
                "not-a-url",
                "https://invalid-domain.com"
            ]
            
            merger.add_custom_sources(problematic_sources)
            
            # Run operations - should not cascade into complete failure
            results = await merger.run_quick_merge(max_sources=10)
            assert isinstance(results, list)
            
            # Should still be able to get statistics
            stats = merger.get_processing_statistics()
            assert isinstance(stats, dict)
            
        except Exception as e:
            # Should handle error cascades gracefully
            assert "error" in str(e).lower() or "timeout" in str(e).lower()


