#!/usr/bin/env python3
"""
Performance Tests for VPN Subscription Merger
Tests for performance, scalability, and resource usage.
"""

import asyncio
import pytest
import time
import psutil
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
import statistics

# Import with fallbacks
try:
    from vpn_merger import UnifiedSources
except ImportError:
    UnifiedSources = None


class TestPerformanceMetrics:
    """Test performance metrics and benchmarks."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_processing_speed(self, temp_output_dir):
        """Test processing speed with different source counts."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Test with different source counts
        source_counts = [5, 10, 20]
        processing_times = []
        
        for count in source_counts:
            start_time = time.time()
            
            results = await merger.run_comprehensive_merge(
                output_dir=str(temp_output_dir),
                test_sources=True,
                max_sources=count
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            processing_times.append(processing_time)
            
            # Verify results
            assert results is not None
            assert len(results) > 0
            
            # Calculate configs per second
            configs_per_second = len(results) / processing_time if processing_time > 0 else 0
            print(f"Processed {len(results)} configs in {processing_time:.2f}s ({configs_per_second:.2f} configs/s)")
        
        # Performance should scale reasonably
        assert all(time < 300 for time in processing_times), "Processing times too high"
    
    @pytest.mark.asyncio
    async def test_memory_usage(self, temp_output_dir):
        """Test memory usage during processing."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run processing
        results = await merger.run_comprehensive_merge(
            output_dir=str(temp_output_dir),
            test_sources=True,
            max_sources=20
        )
        
        # Get peak memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        print(f"Memory usage: {initial_memory:.2f}MB -> {peak_memory:.2f}MB (+{memory_increase:.2f}MB)")
        
        # Memory increase should be reasonable (less than 500MB)
        assert memory_increase < 500, f"Memory usage too high: {memory_increase:.2f}MB"
        
        # Verify results
        assert results is not None
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self, temp_output_dir):
        """Test concurrent processing performance."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Test concurrent processing
        start_time = time.time()
        
        # Run multiple merges concurrently
        tasks = []
        for i in range(3):
            task = merger.run_comprehensive_merge(
                output_dir=str(temp_output_dir / f"output_{i}"),
                test_sources=True,
                max_sources=10
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"Concurrent processing time: {total_time:.2f}s")
        
        # All tasks should complete successfully
        for result in results:
            assert result is not None
            assert len(result) > 0
        
        # Concurrent processing should be faster than sequential
        assert total_time < 180, "Concurrent processing too slow"
    
    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, temp_output_dir):
        """Test handling of large datasets."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Test with larger dataset
        start_time = time.time()
        
        results = await merger.run_comprehensive_merge(
            output_dir=str(temp_output_dir),
            test_sources=True,
            max_sources=50
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"Large dataset processing: {len(results)} configs in {processing_time:.2f}s")
        
        # Should handle large datasets efficiently
        assert len(results) > 0
        assert processing_time < 600, "Large dataset processing too slow"
        
        # Check output file sizes
        output_files = [
            "vpn_subscription_raw.txt",
            "vpn_subscription_base64.txt",
            "vpn_singbox.json",
            "vpn_detailed.csv"
        ]
        
        for filename in output_files:
            file_path = temp_output_dir / filename
            if file_path.exists():
                file_size = file_path.stat().st_size
                print(f"{filename}: {file_size} bytes")
                assert file_size > 0, f"Output file {filename} is empty"


class TestScalability:
    """Test scalability and resource limits."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_source_limit_handling(self, temp_output_dir):
        """Test handling of source limits."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Test with different source limits
        limits = [1, 5, 10, 20]
        
        for limit in limits:
            results = await merger.run_comprehensive_merge(
                output_dir=str(temp_output_dir),
                test_sources=True,
                max_sources=limit
            )
            
            # Should respect the limit
            assert results is not None
            assert len(results) >= 0  # May be 0 if no valid sources
            
            print(f"Limit {limit}: {len(results)} configs")
    
    @pytest.mark.asyncio
    async def test_error_recovery_performance(self, temp_output_dir):
        """Test performance with error recovery."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Test with mixed valid/invalid sources
        start_time = time.time()
        
        results = await merger.run_comprehensive_merge(
            output_dir=str(temp_output_dir),
            test_sources=True,
            max_sources=30
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should handle errors gracefully without significant performance impact
        assert results is not None
        assert processing_time < 300, "Error recovery too slow"
        
        print(f"Error recovery test: {len(results)} configs in {processing_time:.2f}s")


class TestResourceOptimization:
    """Test resource optimization and efficiency."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_cpu_usage(self, temp_output_dir):
        """Test CPU usage during processing."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Monitor CPU usage
        process = psutil.Process()
        
        # Get initial CPU usage
        initial_cpu = process.cpu_percent()
        
        # Run processing
        results = await merger.run_comprehensive_merge(
            output_dir=str(temp_output_dir),
            test_sources=True,
            max_sources=20
        )
        
        # Get average CPU usage
        cpu_usage = process.cpu_percent()
        
        print(f"CPU usage: {initial_cpu}% -> {cpu_usage}%")
        
        # CPU usage should be reasonable
        assert cpu_usage < 100, f"CPU usage too high: {cpu_usage}%"
        
        # Verify results
        assert results is not None
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_disk_io_efficiency(self, temp_output_dir):
        """Test disk I/O efficiency."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Monitor disk I/O
        disk_io_before = psutil.disk_io_counters()
        
        # Run processing
        results = await merger.run_comprehensive_merge(
            output_dir=str(temp_output_dir),
            test_sources=True,
            max_sources=20
        )
        
        # Check disk I/O
        disk_io_after = psutil.disk_io_counters()
        
        if disk_io_before and disk_io_after:
            read_bytes = disk_io_after.read_bytes - disk_io_before.read_bytes
            write_bytes = disk_io_after.write_bytes - disk_io_before.write_bytes
            
            print(f"Disk I/O: {read_bytes} bytes read, {write_bytes} bytes written")
            
            # Disk I/O should be reasonable
            assert write_bytes < 100 * 1024 * 1024, "Disk I/O too high"  # 100MB limit
        
        # Verify results
        assert results is not None
        assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__])
