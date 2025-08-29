from __future__ import annotations

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from vpn_merger.core.container import ServiceContainer
from vpn_merger.processing.pipeline import AsyncPipeline, PipelineStage

# Optional imports with fallbacks
try:
    from vpn_merger.storage.cache import MultiTierCache, CacheEntry, CacheStats
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

try:
    from vpn_merger.monitoring.metrics_collector import MetricsCollector
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

try:
    from vpn_merger.monitoring.tracing_enhanced import TracingService
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False


class TestServiceContainer:
    """Test dependency injection container."""
    
    def test_register_instance(self):
        container = ServiceContainer()
        mock_service = Mock()
        container.register(Mock, instance=mock_service)
        assert container.get(Mock) is mock_service
    
    def test_register_factory(self):
        container = ServiceContainer()
        mock_factory = Mock(return_value="created")
        container.register(str, factory=mock_factory)
        result = container.get(str)
        assert result == "created"
        mock_factory.assert_called_once()
    
    def test_register_both_raises_error(self):
        container = ServiceContainer()
        with pytest.raises(ValueError, match="Provide either instance or factory"):
            container.register(Mock, instance=Mock(), factory=Mock())
    
    def test_register_none_raises_error(self):
        container = ServiceContainer()
        with pytest.raises(ValueError, match="Must provide either instance or factory"):
            container.register(Mock)
    
    def test_get_unregistered_raises_error(self):
        container = ServiceContainer()
        with pytest.raises(KeyError, match="Service <class 'str'> not registered"):
            container.get(str)
    
    def test_create_scope(self):
        container = ServiceContainer()
        container.register(str, factory=lambda: "parent")
        scope = container.create_scope()
        assert scope.get(str) == "parent"
        # Scope should have its own instance
        assert scope._services != container._services


@pytest.mark.skipif(not CACHE_AVAILABLE, reason="Cache not available")
class TestMultiTierCache:
    """Test multi-tier caching system."""
    
    @pytest.mark.asyncio
    async def test_l1_cache_basic_operations(self):
        cache = MultiTierCache()
        
        # Test set/get
        await cache.set("key1", "value1", ttl=3600, tier="l1")
        result = await cache.get("key1", tier="l1")
        assert result == "value1"
        
        # Test expiration - use negative TTL to ensure immediate expiration
        await cache.set("key2", "value2", ttl=-1, tier="l1")  # Immediate expiration
        result = await cache.get("key2", tier="l1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_stats(self):
        cache = MultiTierCache()
        
        # Initial stats
        assert cache.stats.hit_rate == 0.0
        
        # Add and retrieve
        await cache.set("key1", "value1", tier="l1")
        await cache.get("key1", tier="l1")
        
        assert cache.stats.l1_hits == 1
        assert cache.stats.misses == 0
        assert cache.stats.hit_rate == 1.0
        
        # Test miss
        await cache.get("nonexistent", tier="l1")
        assert cache.stats.misses == 1
        assert cache.stats.hit_rate == 0.5


class TestAsyncPipeline:
    """Test async processing pipeline."""
    
    @pytest.mark.asyncio
    async def test_pipeline_stages(self):
        pipeline = AsyncPipeline()
        
        # Add stages with async processors
        async def double_processor(item):
            return item * 2
        
        async def add_one_processor(item):
            return item + 1
        
        pipeline.add_stage("double", double_processor, concurrency=2)
        pipeline.add_stage("add_one", add_one_processor, concurrency=1)
        
        # Process items
        items = [1, 2, 3]
        results = await pipeline.process(items)
        
        # Should be: (1*2)+1=3, (2*2)+1=5, (3*2)+1=7
        assert results == [3, 5, 7]
    
    @pytest.mark.asyncio
    async def test_pipeline_concurrency_control(self):
        import asyncio
        
        pipeline = AsyncPipeline()
        
        # Create a stage that takes time
        async def slow_processor(item):
            await asyncio.sleep(0.1)
            return item * 2
        
        pipeline.add_stage("slow", slow_processor, concurrency=2)
        
        # Process 4 items with concurrency=2
        start_time = asyncio.get_event_loop().time()
        results = await pipeline.process([1, 2, 3, 4])
        end_time = asyncio.get_event_loop().time()
        
        # Should take ~0.2s (2 batches of 2 items)
        assert end_time - start_time >= 0.15
        assert results == [2, 4, 6, 8]
    
    @pytest.mark.asyncio
    async def test_pipeline_exception_handling(self):
        pipeline = AsyncPipeline()
        
        # Add stage that raises exception
        async def failing_processor(item):
            if item == 2:
                raise ValueError("Test exception")
            return item
        
        pipeline.add_stage("test", failing_processor, concurrency=1)
        
        # Process items, should filter out exceptions
        items = [1, 2, 3]
        results = await pipeline.process(items)
        
        # Only successful items should remain
        assert results == [1, 3]


@pytest.mark.skipif(not METRICS_AVAILABLE, reason="Metrics collector not available")
class TestMetricsCollector:
    """Test metrics collection."""
    
    def test_record_config(self):
        # Clear default registry to avoid duplicate metric errors
        from prometheus_client import REGISTRY
        original_collectors = list(REGISTRY._collector_to_names.keys())
        
        try:
            # Remove any existing metrics collectors
            for collector in original_collectors:
                REGISTRY.unregister(collector)
            
            metrics = MetricsCollector()
            
            # Record some configs
            metrics.record_config("vmess", "success")
            metrics.record_config("vless", "success")
            metrics.record_config("vmess", "failed")
            
            # Check that metrics were created and can be accessed
            assert metrics.configs_processed is not None
            assert metrics.configs_processed.labels(protocol="vmess", status="success") is not None
            assert metrics.configs_processed.labels(protocol="vmess", status="failed") is not None
            assert metrics.configs_processed.labels(protocol="vless", status="success") is not None
        finally:
            # Restore original collectors
            for collector in original_collectors:
                try:
                    REGISTRY.register(collector)
                except Exception:
                    pass
    
    def test_record_latency(self):
        # Clear default registry to avoid duplicate metric errors
        from prometheus_client import REGISTRY
        original_collectors = list(REGISTRY._collector_to_names.keys())
        
        try:
            # Remove any existing metrics collectors
            for collector in original_collectors:
                REGISTRY.unregister(collector)
            
            metrics = MetricsCollector()
            
            # Record latencies
            metrics.record_latency("vmess", 100.0)
            metrics.record_latency("vmess", 200.0)
            metrics.record_latency("vless", 150.0)
            
            # Check that histograms were created and can be accessed
            assert metrics.config_latency is not None
            assert metrics.config_latency.labels(protocol="vmess") is not None
            assert metrics.config_latency.labels(protocol="vless") is not None
        finally:
            # Restore original collectors
            for collector in original_collectors:
                try:
                    REGISTRY.register(collector)
                except Exception:
                    pass
    
    def test_time_stage_context_manager(self):
        # Clear default registry to avoid duplicate metric errors
        from prometheus_client import REGISTRY
        original_collectors = list(REGISTRY._collector_to_names.keys())
        
        try:
            # Remove any existing metrics collectors
            for collector in original_collectors:
                REGISTRY.unregister(collector)
            
            metrics = MetricsCollector()
            
            with metrics.time_stage("test_stage"):
                # Simulate some work
                import time
                time.sleep(0.01)
            
            # Check that timing metric was created
            assert metrics.processing_duration is not None
            assert metrics.processing_duration.labels(stage="test_stage") is not None
        finally:
            # Restore original collectors
            for collector in original_collectors:
                try:
                    REGISTRY.register(collector)
                except Exception:
                    pass


@pytest.mark.skipif(not TRACING_AVAILABLE, reason="Tracing service not available")
class TestTracingService:
    """Test tracing service."""
    
    @pytest.mark.asyncio
    async def test_trace_context_manager(self):
        tracing = TracingService()
        
        async with tracing.trace("test_operation", {"key": "value"}) as span:
            # Verify span was created
            assert span is not None
            # Simulate some work
            import asyncio
            await asyncio.sleep(0.01)
        
        # Span should be marked as OK
        assert span.get_status().status_code.value == 1  # OK
    
    @pytest.mark.asyncio
    async def test_trace_method_decorator(self):
        tracing = TracingService()
        
        @tracing.trace_method
        async def test_function():
            return "success"
        
        result = await test_function()
        assert result == "success"
    
    def test_trace_method_sync(self):
        tracing = TracingService()
        
        @tracing.trace_method
        def sync_function():
            return "sync_success"
        
        # Should work for sync functions too
        result = sync_function()
        assert result == "sync_success"


if __name__ == "__main__":
    pytest.main([__file__])
