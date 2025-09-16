"""
Tests for MetricsService.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from streamline_vpn.monitoring.metrics_service import MetricsService


class TestMetricsService:
    """Test MetricsService class"""
    
    def test_initialization(self):
        """Test metrics service initialization"""
        service = MetricsService()
        assert hasattr(service, 'collector')
        assert hasattr(service, 'exporter')
        assert hasattr(service, 'is_running')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test metrics service initialization"""
        service = MetricsService()
        result = await service.initialize()
        assert result is True
    
    def test_start_service(self):
        """Test starting metrics service"""
        service = MetricsService()
        
        with patch.object(service, 'start_service') as mock_start:
            mock_start.return_value = None
            
            result = service.start_service()
            assert result is None
            mock_start.assert_called_once()
    
    def test_stop_service(self):
        """Test stopping metrics service"""
        service = MetricsService()
        
        with patch.object(service, 'stop_service') as mock_stop:
            mock_stop.return_value = None
            
            result = service.stop_service()
            assert result is None
            mock_stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_collect_and_export(self):
        """Test collecting and exporting metrics"""
        service = MetricsService()
        
        with patch.object(service, 'collect_and_export') as mock_collect_export:
            mock_collect_export.return_value = AsyncMock(return_value=True)
            
            result = await service.collect_and_export()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_current_metrics(self):
        """Test getting current metrics"""
        service = MetricsService()
        
        with patch.object(service, 'get_current_metrics') as mock_get:
            mock_get.return_value = AsyncMock(return_value={"cpu": 50.0, "memory": 75.0})
            
            metrics = await service.get_current_metrics()
            assert metrics["cpu"] == 50.0
            assert metrics["memory"] == 75.0
    
    @pytest.mark.asyncio
    async def test_get_historical_metrics(self):
        """Test getting historical metrics"""
        service = MetricsService()
        
        with patch.object(service, 'get_historical_metrics') as mock_get:
            mock_get.return_value = AsyncMock(return_value=[
                {"timestamp": "2024-01-01T00:00:00Z", "cpu": 50.0, "memory": 75.0},
                {"timestamp": "2024-01-01T00:01:00Z", "cpu": 60.0, "memory": 80.0}
            ])
            
            metrics = await service.get_historical_metrics()
            assert len(metrics) == 2
            assert metrics[0]["cpu"] == 50.0
            assert metrics[1]["cpu"] == 60.0
    
    @pytest.mark.asyncio
    async def test_export_metrics(self):
        """Test exporting metrics"""
        service = MetricsService()
        metrics = {"cpu": 50.0, "memory": 75.0}
        
        with patch.object(service, 'export_metrics') as mock_export:
            mock_export.return_value = AsyncMock(return_value=True)
            
            result = await service.export_metrics(metrics)
            assert result is True
    
    def test_set_collection_interval(self):
        """Test setting collection interval"""
        service = MetricsService()
        
        service.set_collection_interval(30)
        assert service.collection_interval == 30
    
    def test_set_export_interval(self):
        """Test setting export interval"""
        service = MetricsService()
        
        service.set_export_interval(60)
        assert service.export_interval == 60
    
    def test_add_custom_metric(self):
        """Test adding custom metric"""
        service = MetricsService()
        
        service.add_custom_metric("custom_metric", 100.0)
        assert "custom_metric" in service.custom_metrics
        assert service.custom_metrics["custom_metric"] == 100.0
    
    def test_remove_custom_metric(self):
        """Test removing custom metric"""
        service = MetricsService()
        service.custom_metrics["custom_metric"] = 100.0
        
        service.remove_custom_metric("custom_metric")
        assert "custom_metric" not in service.custom_metrics
    
    @pytest.mark.asyncio
    async def test_get_metrics_summary(self):
        """Test getting metrics summary"""
        service = MetricsService()
        
        with patch.object(service, 'get_metrics_summary') as mock_get:
            mock_get.return_value = AsyncMock(return_value={
                "total_metrics": 10,
                "system_metrics": 5,
                "application_metrics": 3,
                "custom_metrics": 2,
                "last_updated": "2024-01-01T00:00:00Z"
            })
            
            summary = await service.get_metrics_summary()
            assert summary["total_metrics"] == 10
            assert summary["system_metrics"] == 5
            assert summary["application_metrics"] == 3
            assert summary["custom_metrics"] == 2
    
    @pytest.mark.asyncio
    async def test_export_to_multiple_destinations(self):
        """Test exporting to multiple destinations"""
        service = MetricsService()
        metrics = {"cpu": 50.0, "memory": 75.0}
        destinations = ["file://test.json", "http://example.com/metrics"]
        
        with patch.object(service, 'export_to_multiple_destinations') as mock_export:
            mock_export.return_value = AsyncMock(return_value=True)
            
            result = await service.export_to_multiple_destinations(metrics, destinations)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_schedule_export(self):
        """Test scheduling export"""
        service = MetricsService()
        
        with patch.object(service, 'schedule_export') as mock_schedule:
            mock_schedule.return_value = AsyncMock(return_value=True)
            
            result = await service.schedule_export(interval=60)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_cancel_scheduled_export(self):
        """Test canceling scheduled export"""
        service = MetricsService()
        
        with patch.object(service, 'cancel_scheduled_export') as mock_cancel:
            mock_cancel.return_value = AsyncMock(return_value=True)
            
            result = await service.cancel_scheduled_export()
            assert result is True
    
    def test_configure_export_format(self):
        """Test configuring export format"""
        service = MetricsService()
        
        service.configure_export_format("json")
        assert service.export_format == "json"
        
        service.configure_export_format("prometheus")
        assert service.export_format == "prometheus"
    
    def test_configure_export_destination(self):
        """Test configuring export destination"""
        service = MetricsService()
        
        service.configure_export_destination("file://test.json")
        assert service.export_destination == "file://test.json"
        
        service.configure_export_destination("http://example.com/metrics")
        assert service.export_destination == "http://example.com/metrics"
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test metrics service health check"""
        service = MetricsService()
        
        with patch.object(service, 'health_check') as mock_health:
            mock_health.return_value = AsyncMock(return_value={
                "status": "healthy",
                "collector_running": True,
                "exporter_running": True,
                "last_collection": "2024-01-01T00:00:00Z",
                "last_export": "2024-01-01T00:00:00Z"
            })
            
            health = await service.health_check()
            assert health["status"] == "healthy"
            assert health["collector_running"] is True
            assert health["exporter_running"] is True
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics(self):
        """Test getting performance metrics"""
        service = MetricsService()
        
        with patch.object(service, 'get_performance_metrics') as mock_perf:
            mock_perf.return_value = AsyncMock(return_value={
                "collection_time": 0.05,
                "export_time": 0.1,
                "total_metrics_collected": 1000,
                "total_exports": 100,
                "failed_exports": 5
            })
            
            perf = await service.get_performance_metrics()
            assert perf["collection_time"] == 0.05
            assert perf["export_time"] == 0.1
            assert perf["total_metrics_collected"] == 1000
            assert perf["total_exports"] == 100
            assert perf["failed_exports"] == 5
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in metrics service"""
        service = MetricsService()
        
        with patch.object(service, 'collect_and_export') as mock_collect_export:
            mock_collect_export.side_effect = Exception("Collection failed")
            
            with pytest.raises(Exception):
                await service.collect_and_export()
    
    def test_metrics_validation(self):
        """Test metrics validation"""
        service = MetricsService()
        
        # Test valid metrics
        valid_metrics = {"cpu": 50.0, "memory": 75.0}
        assert service.validate_metrics(valid_metrics) is True
        
        # Test invalid metrics
        invalid_metrics = {"cpu": "invalid", "memory": None}
        assert service.validate_metrics(invalid_metrics) is False
    
    @pytest.mark.asyncio
    async def test_metrics_aggregation(self):
        """Test metrics aggregation"""
        service = MetricsService()
        
        with patch.object(service, 'aggregate_metrics') as mock_aggregate:
            mock_aggregate.return_value = AsyncMock(return_value={
                "cpu_avg": 55.0,
                "cpu_max": 70.0,
                "cpu_min": 40.0,
                "memory_avg": 77.5,
                "memory_max": 85.0,
                "memory_min": 70.0
            })
            
            aggregated = await service.aggregate_metrics("1h")
            assert aggregated["cpu_avg"] == 55.0
            assert aggregated["cpu_max"] == 70.0
            assert aggregated["cpu_min"] == 40.0

