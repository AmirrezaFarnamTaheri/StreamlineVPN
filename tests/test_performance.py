#!/usr/bin/env python3
"""
Performance Tests for VPN Subscription Merger
Comprehensive performance testing and benchmarking.
"""

import asyncio
import pytest
import time
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

# Import with fallbacks
try:
    from vpn_merger import VPNSubscriptionMerger
except ImportError:
    VPNSubscriptionMerger = None


class TestPerformance:
    """Test performance characteristics of the VPN merger."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_processing_speed(self, temp_output_dir):
        """Test processing speed with different source counts."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test with different source counts
        for max_sources in [5, 10, 20]:
            start_time = time.time()
            
            try:
                results = await merger.run_quick_merge(max_sources=max_sources)
                processing_time = time.time() - start_time
                
                # Verify reasonable processing time (adjust thresholds as needed)
                assert processing_time < 60, f"Processing {max_sources} sources took too long: {processing_time}s"
                assert isinstance(results, list)
                
            except Exception as e:
                # Should handle errors gracefully
                assert "timeout" in str(e).lower() or "error" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_concurrent_processing_efficiency(self, temp_output_dir):
        """Test efficiency of concurrent processing."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test different concurrency levels
        concurrency_levels = [1, 5, 10, 20]
        processing_times = {}
        
        for max_concurrent in concurrency_levels:
            start_time = time.time()
            
            try:
                results = await merger.run_comprehensive_merge(max_concurrent=max_concurrent)
                processing_time = time.time() - start_time
                processing_times[max_concurrent] = processing_time
                
                assert isinstance(results, list)
                
            except Exception as e:
                # Should handle errors gracefully
                assert "timeout" in str(e).lower() or "error" in str(e).lower()
        
        # Verify that higher concurrency doesn't significantly increase processing time
        if len(processing_times) >= 2:
            base_time = processing_times[1]
            for concurrent, time_taken in processing_times.items():
                if concurrent > 1:
                    # Higher concurrency should not take more than 2x the base time
                    assert time_taken <= base_time * 2, f"Concurrency {concurrent} took too long: {time_taken}s vs {base_time}s"
    
    @pytest.mark.asyncio
    async def test_memory_usage(self, temp_output_dir):
        """Test memory usage during processing."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Get initial memory usage
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run processing
        try:
            results = await merger.run_quick_merge(max_sources=10)
            
            # Get memory usage after processing
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Verify reasonable memory usage (adjust threshold as needed)
            assert memory_increase < 500, f"Memory usage increased too much: {memory_increase}MB"
            assert isinstance(results, list)
            
        except Exception as e:
            # Should handle errors gracefully
            assert "memory" in str(e).lower() or "timeout" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_output_generation_speed(self, temp_output_dir):
        """Test speed of output file generation."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Run merge to get results
        results = await merger.run_quick_merge(max_sources=5)
        
        if results:
            # Test output generation speed
            start_time = time.time()
            output_files = merger.save_results(str(temp_output_dir))
            generation_time = time.time() - start_time
            
            # Verify reasonable generation time
            assert generation_time < 10, f"Output generation took too long: {generation_time}s"
            assert isinstance(output_files, dict)
            assert len(output_files) > 0
    
    @pytest.mark.asyncio
    async def test_source_validation_speed(self, temp_output_dir):
        """Test speed of source validation."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test validation speed
        start_time = time.time()
        validation_results = await merger.validate_sources_only()
        validation_time = time.time() - start_time
        
        # Verify reasonable validation time (increased threshold for network conditions)
        assert validation_time < 60, f"Source validation took too long: {validation_time}s"
        assert isinstance(validation_results, dict)
        assert len(validation_results) > 0
    
    @pytest.mark.asyncio
    async def test_quality_filtering_performance(self, temp_output_dir):
        """Test performance of quality-based filtering."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Run merge to get results
        all_results = await merger.run_quick_merge(max_sources=10)
        
        if all_results:
            # Test filtering performance
            start_time = time.time()
            
            # Test multiple quality thresholds
            for threshold in [0.0, 0.3, 0.5, 0.7, 0.9]:
                filtered_results = merger.get_results(min_quality=threshold)
                assert isinstance(filtered_results, list)
                assert len(filtered_results) <= len(all_results)
            
            filtering_time = time.time() - start_time
            
            # Verify reasonable filtering time
            assert filtering_time < 1, f"Quality filtering took too long: {filtering_time}s"
    
    @pytest.mark.asyncio
    async def test_statistics_collection_speed(self, temp_output_dir):
        """Test speed of statistics collection."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Run merge to populate statistics
        await merger.run_quick_merge(max_sources=5)
        
        # Test statistics collection speed
        start_time = time.time()
        
        stats = merger.get_processing_statistics()
        summary = merger.get_processing_summary()
        source_stats = merger.get_source_statistics()
        
        collection_time = time.time() - start_time
        
        # Verify reasonable collection time
        assert collection_time < 1, f"Statistics collection took too long: {collection_time}s"
        assert isinstance(stats, dict)
        assert isinstance(summary, dict)
        assert isinstance(source_stats, dict)
    
    @pytest.mark.asyncio
    async def test_error_recovery_performance(self, temp_output_dir):
        """Test performance during error recovery."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Add some invalid sources to trigger errors
        invalid_sources = [
            "https://invalid-url-that-does-not-exist.com/config.txt",
            "https://httpbin.org/status/404",
            "https://httpbin.org/status/500"
        ]
        merger.add_custom_sources(invalid_sources)
        
        # Test error recovery performance
        start_time = time.time()
        
        try:
            results = await merger.run_quick_merge(max_sources=10)
            recovery_time = time.time() - start_time
            
            # Verify reasonable recovery time (increased threshold for network conditions)
            assert recovery_time < 60, f"Error recovery took too long: {recovery_time}s"
            assert isinstance(results, list)
            
        except Exception as e:
            # Should handle errors gracefully
            assert "timeout" in str(e).lower() or "error" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, temp_output_dir):
        """Test handling of large datasets."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test with larger number of sources
        start_time = time.time()
        
        try:
            results = await merger.run_comprehensive_merge(max_concurrent=20)
            processing_time = time.time() - start_time
            
            # Verify reasonable processing time for larger dataset
            assert processing_time < 120, f"Large dataset processing took too long: {processing_time}s"
            assert isinstance(results, list)
            
        except Exception as e:
            # Should handle errors gracefully
            assert "timeout" in str(e).lower() or "memory" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, temp_output_dir):
        """Test performance of concurrent operations."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test multiple concurrent operations
        start_time = time.time()
        
        # Run multiple operations concurrently
        # Note: get_processing_statistics() returns a dict, so we'll call it separately
        try:
            results = await asyncio.gather(
                merger.run_quick_merge(max_sources=3),
                merger.validate_sources_only(),
                return_exceptions=True
            )
            
            # Get statistics separately since it returns a dict
            stats = merger.get_processing_statistics()
            concurrent_time = time.time() - start_time
            
            # Verify reasonable concurrent processing time
            assert concurrent_time < 60, f"Concurrent operations took too long: {concurrent_time}s"
            
            # Verify results
            for result in results:
                if isinstance(result, Exception):
                    # Should handle errors gracefully
                    assert "timeout" in str(result).lower() or "error" in str(result).lower()
                else:
                    assert result is not None
            
        except Exception as e:
            # Should handle errors gracefully
            assert "timeout" in str(e).lower() or "error" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_resource_cleanup(self, temp_output_dir):
        """Test that resources are properly cleaned up."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Get initial resource usage
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run multiple operations
        for _ in range(3):
            try:
                await merger.run_quick_merge(max_sources=3)
                merger.reset()
            except Exception:
                pass
        
        # Get final resource usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Verify reasonable memory usage after cleanup
        assert memory_increase < 200, f"Memory not properly cleaned up: {memory_increase}MB increase"
    
    @pytest.mark.asyncio
    async def test_scalability(self, temp_output_dir):
        """Test scalability with increasing load."""
        if not VPNSubscriptionMerger:
            pytest.skip("VPNSubscriptionMerger not available")
        
        merger = VPNSubscriptionMerger()
        
        # Test scalability with different loads
        load_levels = [5, 10, 15, 20]
        processing_times = {}
        
        for load in load_levels:
            start_time = time.time()
            
            try:
                results = await merger.run_quick_merge(max_sources=load)
                processing_time = time.time() - start_time
                processing_times[load] = processing_time
                
                assert isinstance(results, list)
                
            except Exception as e:
                # Should handle errors gracefully
                assert "timeout" in str(e).lower() or "error" in str(e).lower()
        
        # Verify scalability (processing time should not increase exponentially)
        if len(processing_times) >= 3:
            times = list(processing_times.values())
            for i in range(1, len(times)):
                # Each level should not take more than 1.5x the previous level
                assert times[i] <= times[i-1] * 1.5, f"Poor scalability: {times[i]}s vs {times[i-1]}s"
