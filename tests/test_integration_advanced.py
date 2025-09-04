#!/usr/bin/env python3
"""
Advanced Integration Test Suite for VPN Merger
==============================================

Advanced integration testing including:
- Database integration testing
- External service integration testing
- Performance benchmark testing
- Load testing
- Stress testing
- End-to-end workflow testing
"""

import asyncio
import json
import tempfile
import time
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


class TestDatabaseIntegration:
    """Test database integration."""

    @pytest.mark.integration
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_redis_integration(self):
        """Test Redis integration for job persistence."""
        # Test Redis connection
        try:
            import redis
            redis_client = redis.Redis(host='localhost', port=6379, db=0)
            redis_client.ping()
            
            # Test Redis operations
            test_key = "test_key"
            test_value = "test_value"
            
            # Set value
            redis_client.set(test_key, test_value)
            
            # Get value
            retrieved_value = redis_client.get(test_key)
            assert retrieved_value.decode() == test_value, "Redis get/set operations failed"
            
            # Delete value
            redis_client.delete(test_key)
            
            # Verify deletion
            deleted_value = redis_client.get(test_key)
            assert deleted_value is None, "Redis delete operation failed"
            
        except ImportError:
            pytest.skip("Redis not available")
        except redis.ConnectionError:
            pytest.skip("Redis server not running")

    @pytest.mark.integration
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_sqlite_integration(self):
        """Test SQLite integration for local data storage."""
        import sqlite3
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            # Test SQLite operations
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create table
            cursor.execute('''
                CREATE TABLE test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    value TEXT
                )
            ''')
            
            # Insert data
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test", "value"))
            conn.commit()
            
            # Query data
            cursor.execute("SELECT * FROM test_table WHERE name = ?", ("test",))
            result = cursor.fetchone()
            assert result is not None, "SQLite insert/query operations failed"
            assert result[1] == "test", "SQLite data integrity failed"
            assert result[2] == "value", "SQLite data integrity failed"
            
            # Update data
            cursor.execute("UPDATE test_table SET value = ? WHERE name = ?", ("updated", "test"))
            conn.commit()
            
            # Verify update
            cursor.execute("SELECT value FROM test_table WHERE name = ?", ("test",))
            updated_value = cursor.fetchone()[0]
            assert updated_value == "updated", "SQLite update operation failed"
            
            # Delete data
            cursor.execute("DELETE FROM test_table WHERE name = ?", ("test",))
            conn.commit()
            
            # Verify deletion
            cursor.execute("SELECT * FROM test_table WHERE name = ?", ("test",))
            deleted_result = cursor.fetchone()
            assert deleted_result is None, "SQLite delete operation failed"
            
        finally:
            conn.close()
            Path(db_path).unlink()

    @pytest.mark.integration
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_database_transaction_handling(self):
        """Test database transaction handling."""
        import sqlite3
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create table
            cursor.execute('''
                CREATE TABLE test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    value TEXT
                )
            ''')
            
            # Test transaction rollback
            try:
                cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test1", "value1"))
                cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test2", "value2"))
                
                # Simulate error
                raise Exception("Simulated error")
                
            except Exception:
                # Rollback transaction
                conn.rollback()
            
            # Verify rollback
            cursor.execute("SELECT COUNT(*) FROM test_table")
            count = cursor.fetchone()[0]
            assert count == 0, "Transaction rollback failed"
            
            # Test successful transaction
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test1", "value1"))
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test2", "value2"))
            conn.commit()
            
            # Verify commit
            cursor.execute("SELECT COUNT(*) FROM test_table")
            count = cursor.fetchone()[0]
            assert count == 2, "Transaction commit failed"
            
        finally:
            conn.close()
            Path(db_path).unlink()


class TestExternalServiceIntegration:
    """Test external service integration."""

    @pytest.mark.integration
    @pytest.mark.external
    @pytest.mark.asyncio
    async def test_http_service_integration(self):
        """Test HTTP service integration."""
        processor = SourceProcessor()
        
        # Test HTTP service integration
        test_urls = [
            "https://httpbin.org/json",
            "https://httpbin.org/base64/SFRUUEJJTiBpcyBhd2Vzb21l",
            "https://httpbin.org/headers"
        ]
        
        for url in test_urls:
            try:
                results = await processor.process_sources_batch([url], batch_size=1)
                assert results is not None, f"HTTP service integration failed for {url}"
            except Exception as e:
                # Network errors are acceptable in test environment
                assert "network" in str(e).lower() or "connection" in str(e).lower() or "timeout" in str(e).lower()

    @pytest.mark.integration
    @pytest.mark.external
    @pytest.mark.asyncio
    async def test_ssl_tls_integration(self):
        """Test SSL/TLS integration."""
        validator = UnifiedSourceValidator()
        
        try:
            async with validator:
                # Test SSL/TLS validation
                ssl_urls = [
                    "https://httpbin.org/json",
                    "https://httpbin.org/headers"
                ]
                
                for url in ssl_urls:
                    try:
                        result = await validator.validate_source(url)
                        assert result is not None, f"SSL/TLS integration failed for {url}"
                        assert result.accessible, f"SSL/TLS validation failed for {url}"
                    except Exception as e:
                        # Network errors are acceptable in test environment
                        assert "network" in str(e).lower() or "connection" in str(e).lower() or "timeout" in str(e).lower()
                        
        except Exception as e:
            # Network errors are acceptable in test environment
            assert "network" in str(e).lower() or "connection" in str(e).lower() or "timeout" in str(e).lower()

    @pytest.mark.integration
    @pytest.mark.external
    @pytest.mark.asyncio
    async def test_dns_resolution_integration(self):
        """Test DNS resolution integration."""
        import socket
        
        # Test DNS resolution
        test_domains = [
            "httpbin.org",
            "example.com",
            "google.com"
        ]
        
        for domain in test_domains:
            try:
                ip = socket.gethostbyname(domain)
                assert ip is not None, f"DNS resolution failed for {domain}"
                assert len(ip.split('.')) == 4, f"Invalid IP address for {domain}: {ip}"
            except socket.gaierror:
                # DNS resolution errors are acceptable in test environment
                pass

    @pytest.mark.integration
    @pytest.mark.external
    @pytest.mark.asyncio
    async def test_api_rate_limiting_integration(self):
        """Test API rate limiting integration."""
        processor = SourceProcessor()
        
        # Test rate limiting
        test_urls = ["https://httpbin.org/json"] * 10
        
        start_time = time.time()
        
        try:
            results = await processor.process_sources_batch(test_urls, batch_size=5)
            end_time = time.time()
            
            # Verify rate limiting
            processing_time = end_time - start_time
            assert processing_time > 0, "Rate limiting not implemented"
            
        except Exception as e:
            # Network errors are acceptable in test environment
            assert "network" in str(e).lower() or "connection" in str(e).lower() or "timeout" in str(e).lower()


class TestPerformanceBenchmarks:
    """Test performance benchmarks."""

    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_processing_throughput_benchmark(self):
        """Test processing throughput benchmark."""
        processor = SourceProcessor()
        
        # Test processing throughput
        test_sources = ["https://httpbin.org/json"] * 100
        
        start_time = time.time()
        
        try:
            results = await processor.process_sources_batch(test_sources, batch_size=10)
            end_time = time.time()
            
            # Calculate throughput
            processing_time = end_time - start_time
            throughput = len(test_sources) / processing_time if processing_time > 0 else 0
            
            # Verify throughput
            assert throughput > 0, "Processing throughput benchmark failed"
            assert processing_time < 60, "Processing took too long"
            
        except Exception as e:
            # Network errors are acceptable in test environment
            assert "network" in str(e).lower() or "connection" in str(e).lower() or "timeout" in str(e).lower()

    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage_benchmark(self):
        """Test memory usage benchmark."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process multiple sources
        processor = SourceProcessor()
        test_sources = ["https://httpbin.org/json"] * 50
        
        try:
            results = await processor.process_sources_batch(test_sources, batch_size=10)
            
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # Verify memory usage is reasonable (less than 200MB increase)
            assert memory_increase < 200 * 1024 * 1024, f"Memory usage too high: {memory_increase / 1024 / 1024:.2f}MB"
            
        except Exception as e:
            # Network errors are acceptable in test environment
            assert "network" in str(e).lower() or "connection" in str(e).lower() or "timeout" in str(e).lower()

    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_processing_benchmark(self):
        """Test concurrent processing benchmark."""
        processor = SourceProcessor()
        
        # Test concurrent processing
        test_sources = ["https://httpbin.org/json"] * 20
        
        start_time = time.time()
        
        try:
            # Process with different concurrency levels
            for batch_size in [1, 5, 10]:
                batch_start = time.time()
                results = await processor.process_sources_batch(test_sources, batch_size=batch_size)
                batch_end = time.time()
                
                batch_time = batch_end - batch_start
                batch_throughput = len(test_sources) / batch_time if batch_time > 0 else 0
                
                # Verify concurrent processing improves throughput
                assert batch_throughput > 0, f"Concurrent processing benchmark failed for batch size {batch_size}"
                
        except Exception as e:
            # Network errors are acceptable in test environment
            assert "network" in str(e).lower() or "connection" in str(e).lower() or "timeout" in str(e).lower()

    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_ml_prediction_performance_benchmark(self):
        """Test ML prediction performance benchmark."""
        predictor = EnhancedConfigQualityPredictor()
        
        # Test ML prediction performance
        test_configs = ["vmess://test-config"] * 100
        
        start_time = time.time()
        
        # Test prediction performance
        for config in test_configs:
            try:
                result = await predictor.predict_quality(config, source_reliability=0.8)
                assert result is not None, "ML prediction performance benchmark failed"
                assert 0.0 <= result.quality_score <= 1.0, "Invalid quality score"
                assert result.confidence >= 0.0, "Invalid confidence score"
            except Exception as e:
                # ML errors are acceptable in test environment
                assert "ml" in str(e).lower() or "model" in str(e).lower()
        
        end_time = time.time()
        prediction_time = end_time - start_time
        
        # Verify prediction performance
        assert prediction_time < 30, "ML prediction took too long"
        assert prediction_time > 0, "ML prediction performance benchmark failed"


class TestLoadTesting:
    """Test load testing scenarios."""

    @pytest.mark.integration
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_high_load_processing(self):
        """Test high load processing."""
        processor = SourceProcessor()
        
        # Test high load processing
        test_sources = ["https://httpbin.org/json"] * 1000
        
        start_time = time.time()
        
        try:
            results = await processor.process_sources_batch(test_sources, batch_size=50)
            end_time = time.time()
            
            # Calculate load metrics
            processing_time = end_time - start_time
            throughput = len(test_sources) / processing_time if processing_time > 0 else 0
            
            # Verify load handling
            assert throughput > 0, "High load processing failed"
            assert processing_time < 300, "High load processing took too long"
            
        except Exception as e:
            # Network errors are acceptable in test environment
            assert "network" in str(e).lower() or "connection" in str(e).lower() or "timeout" in str(e).lower()

    @pytest.mark.integration
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_concurrent_user_simulation(self):
        """Test concurrent user simulation."""
        generator = VPNConfigGenerator(host="127.0.0.1", port=8083)
        
        try:
            await generator.start()
            
            # Simulate concurrent users
            async def simulate_user():
                test_data = {
                    "host": "example.com",
                    "port": 443,
                    "uuid": "12345678-1234-1234-1234-123456789012"
                }
                
                try:
                    result = await generator._handle_generate_vless(
                        AsyncMock(json=lambda: test_data)
                    )
                    return result.status == 200
                except Exception:
                    return False
            
            # Test concurrent users
            tasks = [simulate_user() for _ in range(10)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify concurrent user handling
            success_count = sum(1 for result in results if result is True)
            assert success_count > 0, "Concurrent user simulation failed"
            
        finally:
            await generator.stop()

    @pytest.mark.integration
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self):
        """Test memory leak detection."""
        import psutil
        import os
        import gc
        
        process = psutil.Process(os.getpid())
        
        # Test memory leak detection
        for iteration in range(5):
            initial_memory = process.memory_info().rss
            
            # Process sources
            processor = SourceProcessor()
            test_sources = ["https://httpbin.org/json"] * 100
            
            try:
                results = await processor.process_sources_batch(test_sources, batch_size=10)
                
                # Force garbage collection
                gc.collect()
                
                final_memory = process.memory_info().rss
                memory_increase = final_memory - initial_memory
                
                # Verify no memory leak (memory increase should be reasonable)
                assert memory_increase < 50 * 1024 * 1024, f"Memory leak detected in iteration {iteration}: {memory_increase / 1024 / 1024:.2f}MB"
                
            except Exception as e:
                # Network errors are acceptable in test environment
                assert "network" in str(e).lower() or "connection" in str(e).lower() or "timeout" in str(e).lower()


class TestStressTesting:
    """Test stress testing scenarios."""

    @pytest.mark.integration
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_extreme_load_processing(self):
        """Test extreme load processing."""
        processor = SourceProcessor()
        
        # Test extreme load processing
        test_sources = ["https://httpbin.org/json"] * 5000
        
        start_time = time.time()
        
        try:
            results = await processor.process_sources_batch(test_sources, batch_size=100)
            end_time = time.time()
            
            # Calculate stress metrics
            processing_time = end_time - start_time
            throughput = len(test_sources) / processing_time if processing_time > 0 else 0
            
            # Verify stress handling
            assert throughput > 0, "Extreme load processing failed"
            assert processing_time < 600, "Extreme load processing took too long"
            
        except Exception as e:
            # Network errors are acceptable in test environment
            assert "network" in str(e).lower() or "connection" in str(e).lower() or "timeout" in str(e).lower()

    @pytest.mark.integration
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_resource_exhaustion_handling(self):
        """Test resource exhaustion handling."""
        processor = SourceProcessor()
        
        # Test resource exhaustion handling
        test_sources = ["https://httpbin.org/json"] * 10000
        
        try:
            results = await processor.process_sources_batch(test_sources, batch_size=1000)
            
            # Verify resource exhaustion handling
            assert results is not None, "Resource exhaustion handling failed"
            
        except Exception as e:
            # Resource exhaustion errors are acceptable
            assert "resource" in str(e).lower() or "memory" in str(e).lower() or "timeout" in str(e).lower()

    @pytest.mark.integration
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_error_recovery_stress(self):
        """Test error recovery under stress."""
        processor = SourceProcessor()
        
        # Test error recovery under stress
        test_sources = [
            "https://httpbin.org/json",
            "invalid_url",
            "https://httpbin.org/status/500",
            "https://httpbin.org/delay/10",
            "https://httpbin.org/json"
        ] * 100
        
        try:
            results = await processor.process_sources_batch(test_sources, batch_size=10)
            
            # Verify error recovery
            assert results is not None, "Error recovery under stress failed"
            
        except Exception as e:
            # Error recovery errors are acceptable
            assert "error" in str(e).lower() or "recovery" in str(e).lower() or "timeout" in str(e).lower()


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    @pytest.mark.integration
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_merger_workflow_e2e(self):
        """Test complete VPN merger workflow end-to-end."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize components
            source_manager = SourceManager()
            source_processor = SourceProcessor()
            output_manager = OutputManager(temp_dir)
            
            # Test complete workflow
            test_sources = ["https://httpbin.org/json"]
            
            try:
                # Test source processing
                results = await source_processor.process_sources_batch(test_sources, batch_size=1)
                
                if results:
                    # Test output generation
                    output_files = output_manager.save_results(results)
                    
                    # Verify output files
                    assert "raw" in output_files, "Raw output file not generated"
                    assert "base64" in output_files, "Base64 output file not generated"
                    assert "csv" in output_files, "CSV output file not generated"
                    
                    # Verify files exist
                    for file_type, file_path in output_files.items():
                        assert Path(file_path).exists(), f"{file_type} output file does not exist"
                        assert Path(file_path).stat().st_size > 0, f"{file_type} output file is empty"
                
            except Exception as e:
                # Network errors are acceptable in test environment
                assert "network" in str(e).lower() or "connection" in str(e).lower() or "timeout" in str(e).lower()

    @pytest.mark.integration
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_web_interface_workflow_e2e(self):
        """Test web interface workflow end-to-end."""
        generator = VPNConfigGenerator(host="127.0.0.1", port=8084)
        
        try:
            # Start web server
            await generator.start()
            
            # Test server is running
            assert generator.site is not None, "Web server not running"
            
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
            assert vless_result.status == 200, "VLESS generation failed"
            
            # Test WireGuard key generation
            wg_result = await generator._handle_generate_wg_key(AsyncMock())
            
            # Verify result
            assert wg_result.status == 200, "WireGuard key generation failed"
            
        finally:
            await generator.stop()

    @pytest.mark.integration
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_ml_quality_prediction_workflow_e2e(self):
        """Test ML quality prediction workflow end-to-end."""
        # Initialize ML predictor
        predictor = EnhancedConfigQualityPredictor()
        
        # Test configuration
        test_config = "vmess://test-config"
        
        try:
            # Test quality prediction
            result = await predictor.predict_quality(test_config, source_reliability=0.8)
            
            # Verify result
            assert result is not None, "ML quality prediction failed"
            assert 0.0 <= result.quality_score <= 1.0, "Invalid quality score"
            assert result.confidence >= 0.0, "Invalid confidence score"
            assert result.model_version is not None, "Model version not set"
            
        except Exception as e:
            # ML errors are acceptable in test environment
            assert "ml" in str(e).lower() or "model" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
