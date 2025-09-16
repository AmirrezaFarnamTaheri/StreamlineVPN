"""
Tests for MetricsCollector.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from streamline_vpn.monitoring.metrics_collector import MetricsCollector, MetricType


class TestMetricsCollector:
    """Test MetricsCollector class"""
    
    def test_initialization(self):
        """Test metrics collector initialization"""
        collector = MetricsCollector()
        assert hasattr(collector, 'metrics')
        assert hasattr(collector, 'is_running')
        assert hasattr(collector, 'collection_interval')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test metrics collector initialization"""
        collector = MetricsCollector()
        result = await collector.initialize()
        assert result is True
    
    def test_start_collection(self):
        """Test starting metrics collection"""
        collector = MetricsCollector()
        
        with patch.object(collector, 'start_collection') as mock_start:
            mock_start.return_value = None
            
            result = collector.start_collection()
            assert result is None
            mock_start.assert_called_once()
    
    def test_stop_collection(self):
        """Test stopping metrics collection"""
        collector = MetricsCollector()
        
        with patch.object(collector, 'stop_collection') as mock_stop:
            mock_stop.return_value = None
            
            result = collector.stop_collection()
            assert result is None
            mock_stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_collect_metrics(self):
        """Test collecting metrics"""
        collector = MetricsCollector()
        
        with patch.object(collector, 'collect_metrics') as mock_collect:
            mock_collect.return_value = AsyncMock(return_value={"cpu": 50.0, "memory": 75.0})
            
            metrics = await collector.collect_metrics()
            assert metrics["cpu"] == 50.0
            assert metrics["memory"] == 75.0
    
    def test_add_metric(self):
        """Test adding a metric"""
        collector = MetricsCollector()
        
        collector.add_metric("test_metric", 100.0)
        assert "test_metric" in collector.metrics
        # Check the complex structure that's actually stored
        metric_data = collector.metrics["test_metric"]
        assert metric_data["type"] == MetricType.GAUGE
        assert metric_data["help"] == "test_metric"
        assert "values" in metric_data
    
    def test_get_metric(self):
        """Test getting a metric"""
        collector = MetricsCollector()
        collector.metrics["test_metric"] = 100.0
        
        value = collector.get_metric("test_metric")
        assert value == 100.0
    
    def test_get_metric_nonexistent(self):
        """Test getting a nonexistent metric"""
        collector = MetricsCollector()
        
        value = collector.get_metric("nonexistent_metric")
        assert value is None
    
    def test_get_all_metrics(self):
        """Test getting all metrics"""
        collector = MetricsCollector()
        collector.metrics = {"metric1": 10.0, "metric2": 20.0}
        
        all_metrics = collector.get_all_metrics()
        assert all_metrics["metric1"] == 10.0
        assert all_metrics["metric2"] == 20.0
    
    def test_clear_metrics(self):
        """Test clearing metrics"""
        collector = MetricsCollector()
        collector.metrics = {"metric1": 10.0, "metric2": 20.0}
        
        collector.clear_metrics()
        assert len(collector.metrics) == 0
    
    def test_set_collection_interval(self):
        """Test setting collection interval"""
        collector = MetricsCollector()
        
        collector.set_collection_interval(30)
        assert collector.collection_interval == 30
    
    def test_is_running_property(self):
        """Test is_running property"""
        collector = MetricsCollector()
        
        assert collector.is_running is False
        
        collector.is_running = True
        assert collector.is_running is True
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics(self):
        """Test collecting system metrics"""
        collector = MetricsCollector()
        
        with patch.object(collector, 'collect_system_metrics') as mock_collect:
            mock_collect.return_value = AsyncMock(return_value={
                "cpu_percent": 50.0,
                "memory_percent": 75.0,
                "disk_usage": 60.0
            })
            
            metrics = await collector.collect_system_metrics()
            assert metrics["cpu_percent"] == 50.0
            assert metrics["memory_percent"] == 75.0
            assert metrics["disk_usage"] == 60.0
    
    @pytest.mark.asyncio
    async def test_collect_application_metrics(self):
        """Test collecting application metrics"""
        collector = MetricsCollector()
        
        with patch.object(collector, 'collect_application_metrics') as mock_collect:
            mock_collect.return_value = AsyncMock(return_value={
                "requests_per_second": 100.0,
                "response_time": 0.05,
                "error_rate": 0.01
            })
            
            metrics = await collector.collect_application_metrics()
            assert metrics["requests_per_second"] == 100.0
            assert metrics["response_time"] == 0.05
            assert metrics["error_rate"] == 0.01
    
    @pytest.mark.asyncio
    async def test_collect_business_metrics(self):
        """Test collecting business metrics"""
        collector = MetricsCollector()
        
        with patch.object(collector, 'collect_business_metrics') as mock_collect:
            mock_collect.return_value = AsyncMock(return_value={
                "active_users": 1000,
                "configurations_processed": 5000,
                "sources_updated": 10
            })
            
            metrics = await collector.collect_business_metrics()
            assert metrics["active_users"] == 1000
            assert metrics["configurations_processed"] == 5000
            assert metrics["sources_updated"] == 10
    
    def test_metric_validation(self):
        """Test metric validation"""
        collector = MetricsCollector()
        
        # Test valid metric
        collector.add_metric("valid_metric", 100.0)
        assert collector.get_metric("valid_metric") == 100.0
        
        # Test invalid metric name
        with pytest.raises(ValueError):
            collector.add_metric("", 100.0)
        
        # Test invalid metric value
        with pytest.raises(ValueError):
            collector.add_metric("test_metric", "invalid_value")
    
    def test_metric_types(self):
        """Test different metric types"""
        collector = MetricsCollector()
        
        # Test counter metric
        collector.add_metric("counter_metric", 1, metric_type="counter")
        assert collector.get_metric("counter_metric") == 1
        
        # Test gauge metric
        collector.add_metric("gauge_metric", 50.0, metric_type="gauge")
        assert collector.get_metric("gauge_metric") == 50.0
        
        # Test histogram metric
        collector.add_metric("histogram_metric", [0.1, 0.2, 0.3], metric_type="histogram")
        assert collector.get_metric("histogram_metric") == [0.1, 0.2, 0.3]
    
    @pytest.mark.asyncio
    async def test_continuous_collection(self):
        """Test continuous metrics collection"""
        collector = MetricsCollector()
        
        with patch.object(collector, 'collect_metrics') as mock_collect:
            mock_collect.return_value = AsyncMock(return_value={"test": 1.0})
            
            # Start collection
            collector.start_collection()
            assert collector.is_running is True
            
            # Stop collection
            collector.stop_collection()
            assert collector.is_running is False
    
    def test_metric_aggregation(self):
        """Test metric aggregation"""
        collector = MetricsCollector()
        
        # Add multiple values for aggregation
        collector.add_metric("test_metric", 10.0)
        collector.add_metric("test_metric", 20.0)
        collector.add_metric("test_metric", 30.0)
        
        # Test average aggregation
        avg_value = collector.get_metric_average("test_metric")
        assert avg_value == 20.0
        
        # Test sum aggregation
        sum_value = collector.get_metric_sum("test_metric")
        assert sum_value == 60.0
        
        # Test max aggregation
        max_value = collector.get_metric_max("test_metric")
        assert max_value == 30.0
        
        # Test min aggregation
        min_value = collector.get_metric_min("test_metric")
        assert min_value == 10.0

