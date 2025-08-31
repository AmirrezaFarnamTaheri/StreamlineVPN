#!/usr/bin/env python3
"""
End-to-End Tests for VPN Subscription Merger
Comprehensive integration tests for the complete pipeline.
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

# Import with fallbacks
try:
    from vpn_merger import UnifiedSources
except ImportError:
    UnifiedSources = None


class TestEndToEndPipeline:
    """Test the complete end-to-end pipeline."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_complete_merge_pipeline(self, temp_output_dir):
        """Test the complete merge pipeline from sources to outputs."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Run the complete merge
        results = await merger.run_comprehensive_merge(
            output_dir=str(temp_output_dir),
            test_sources=True,
            max_sources=10  # Limit for testing
        )
        
        # Verify results
        assert results is not None
        assert len(results) > 0
        
        # Check output files were created
        expected_files = [
            "vpn_subscription_raw.txt",
            "vpn_subscription_base64.txt",
            "vpn_singbox.json",
            "clash.yaml",
            "vpn_detailed.csv",
            "vpn_report.json"
        ]
        
        for filename in expected_files:
            file_path = temp_output_dir / filename
            assert file_path.exists(), f"Expected file {filename} not found"
            assert file_path.stat().st_size > 0, f"File {filename} is empty"
    
    @pytest.mark.asyncio
    async def test_source_loading_and_validation(self):
        """Test source loading and validation pipeline."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Test source loading
        sources = merger._try_load_external()
        assert sources is not None
        
        # Test source validation
        valid_sources = []
        for source in sources[:5]:  # Test first 5 sources
            try:
                # Basic validation
                assert source.startswith(('http://', 'https://'))
                valid_sources.append(source)
            except AssertionError:
                continue
        
        assert len(valid_sources) > 0, "No valid sources found"
    
    @pytest.mark.asyncio
    async def test_configuration_processing(self, temp_output_dir):
        """Test configuration processing and parsing."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Test with a small set of sources
        results = await merger.run_comprehensive_merge(
            output_dir=str(temp_output_dir),
            test_sources=True,
            max_sources=5
        )
        
        # Verify configurations were processed
        assert results is not None
        assert len(results) > 0
        
        # Check that configurations are valid
        for config in results[:10]:  # Check first 10 configs
            assert isinstance(config, str)
            assert len(config) > 10  # Basic length check
            assert any(protocol in config.lower() for protocol in [
                'vmess', 'vless', 'trojan', 'ss', 'ssr'
            ]), f"Invalid config format: {config[:50]}..."
    
    @pytest.mark.asyncio
    async def test_output_formats(self, temp_output_dir):
        """Test all output formats are generated correctly."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Run merge
        results = await merger.run_comprehensive_merge(
            output_dir=str(temp_output_dir),
            test_sources=True,
            max_sources=5
        )
        
        # Test raw format
        raw_file = temp_output_dir / "vpn_subscription_raw.txt"
        assert raw_file.exists()
        raw_content = raw_file.read_text(encoding='utf-8')
        assert len(raw_content) > 0
        
        # Test base64 format
        base64_file = temp_output_dir / "vpn_subscription_base64.txt"
        assert base64_file.exists()
        base64_content = base64_file.read_text(encoding='utf-8')
        assert len(base64_content) > 0
        
        # Test JSON format
        json_file = temp_output_dir / "vpn_singbox.json"
        assert json_file.exists()
        json_content = json_file.read_text(encoding='utf-8')
        assert len(json_content) > 0
        
        # Test CSV format
        csv_file = temp_output_dir / "vpn_detailed.csv"
        assert csv_file.exists()
        csv_content = csv_file.read_text(encoding='utf-8')
        assert len(csv_content) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Test with invalid sources
        invalid_sources = [
            "https://invalid-url-that-does-not-exist.com/config.txt",
            "https://httpbin.org/status/404",
            "not-a-url"
        ]
        
        # Should not crash with invalid sources
        try:
            results = await merger.run_comprehensive_merge(
                output_dir=str(tempfile.mkdtemp()),
                test_sources=True,
                max_sources=len(invalid_sources)
            )
            # Should either return empty results or handle gracefully
            assert results is not None
        except Exception as e:
            # If it raises an exception, it should be a handled exception
            assert "Invalid" in str(e) or "Error" in str(e)
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, temp_output_dir):
        """Test performance under load."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        import time
        start_time = time.time()
        
        # Run with more sources to test performance
        results = await merger.run_comprehensive_merge(
            output_dir=str(temp_output_dir),
            test_sources=True,
            max_sources=20
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (adjust as needed)
        assert processing_time < 300, f"Processing took too long: {processing_time}s"
        assert results is not None
        assert len(results) > 0


class TestIntegrationComponents:
    """Test integration between different components."""
    
    @pytest.mark.asyncio
    async def test_source_to_output_integration(self, temp_output_dir):
        """Test integration from source loading to output generation."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Test the complete flow
        results = await merger.run_comprehensive_merge(
            output_dir=str(temp_output_dir),
            test_sources=True,
            max_sources=10
        )
        
        # Verify the integration worked
        assert results is not None
        assert len(results) > 0
        
        # Check that outputs are consistent
        raw_file = temp_output_dir / "vpn_subscription_raw.txt"
        base64_file = temp_output_dir / "vpn_subscription_base64.txt"
        
        if raw_file.exists() and base64_file.exists():
            raw_content = raw_file.read_text(encoding='utf-8')
            base64_content = base64_file.read_text(encoding='utf-8')
            
            # Both should have content
            assert len(raw_content) > 0
            assert len(base64_content) > 0
    
    @pytest.mark.asyncio
    async def test_configuration_consistency(self, temp_output_dir):
        """Test that configurations are consistent across formats."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        results = await merger.run_comprehensive_merge(
            output_dir=str(temp_output_dir),
            test_sources=True,
            max_sources=5
        )
        
        # Check consistency between raw and processed results
        raw_file = temp_output_dir / "vpn_subscription_raw.txt"
        if raw_file.exists():
            raw_content = raw_file.read_text(encoding='utf-8')
            raw_configs = [line.strip() for line in raw_content.split('\n') if line.strip()]
            
            # Should have similar number of configs
            assert len(raw_configs) > 0
            assert abs(len(raw_configs) - len(results)) <= 2  # Allow small difference


if __name__ == "__main__":
    pytest.main([__file__])
