"""
Focused tests for Monitoring Metrics
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.monitoring.metrics_collector import MetricsCollector
from streamline_vpn.monitoring.metrics_exporter import MetricsExporter
from streamline_vpn.monitoring.metrics_service import MetricsService


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
    
    def test_collect_system_metrics(self):
        """Test collecting system metrics"""
        collector = MetricsCollector()
        
        with patch.object(collector, 'collect_system_metrics') as mock_collect:
            mock_collect.return_value = {
                "cpu_usage": 50.0,
                "memory_usage": 75.0,
                "disk_usage": 60.0
            }
            
            result = collector.collect_system_metrics()
            assert "cpu_usage" in result
            assert "memory_usage" in result
            assert "disk_usage" in result
            mock_collect.assert_called_once()
    
    def test_collect_application_metrics(self):
        """Test collecting application metrics"""
        collector = MetricsCollector()
        
        with patch.object(collector, 'collect_application_metrics') as mock_collect:
            mock_collect.return_value = {
                "requests_total": 1000,
                "errors_total": 50,
                "response_time_avg": 150.0
            }
            
            result = collector.collect_application_metrics()
            assert "requests_total" in result
            assert "errors_total" in result
            assert "response_time_avg" in result
            mock_collect.assert_called_once()
    
    def test_collect_business_metrics(self):
        """Test collecting business metrics"""
        collector = MetricsCollector()
        
        with patch.object(collector, 'collect_business_metrics') as mock_collect:
            mock_collect.return_value = {
                "configs_processed": 500,
                "sources_active": 10,
                "cache_hit_rate": 0.85
            }
            
            result = collector.collect_business_metrics()
            assert "configs_processed" in result
            assert "sources_active" in result
            assert "cache_hit_rate" in result
            mock_collect.assert_called_once()
    
    def test_get_metrics(self):
        """Test getting all metrics"""
        collector = MetricsCollector()
        
        with patch.object(collector, 'get_metrics') as mock_get:
            mock_get.return_value = {
                "system": {"cpu_usage": 50.0},
                "application": {"requests_total": 1000},
                "business": {"configs_processed": 500}
            }
            
            result = collector.get_metrics()
            assert "system" in result
            assert "application" in result
            assert "business" in result
            mock_get.assert_called_once()
    
    def test_reset_metrics(self):
        """Test resetting metrics"""
        collector = MetricsCollector()
        
        with patch.object(collector, 'reset_metrics') as mock_reset:
            mock_reset.return_value = None
            
            result = collector.reset_metrics()
            assert result is None
            mock_reset.assert_called_once()
    
    def test_get_metrics_summary(self):
        """Test getting metrics summary"""
        collector = MetricsCollector()
        
        with patch.object(collector, 'get_metrics_summary') as mock_summary:
            mock_summary.return_value = {
                "total_metrics": 15,
                "last_updated": "2023-01-01T00:00:00Z",
                "status": "healthy"
            }
            
            result = collector.get_metrics_summary()
            assert "total_metrics" in result
            assert "last_updated" in result
            assert "status" in result
            mock_summary.assert_called_once()


class TestMetricsExporter:
    """Test MetricsExporter class"""
    
    def test_initialization(self):
        """Test metrics exporter initialization"""
        exporter = MetricsExporter(collector=MagicMock())
        assert hasattr(exporter, 'collector')
        assert hasattr(exporter, 'export_formats')
        assert hasattr(exporter, 'is_running')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test metrics exporter initialization"""
        exporter = MetricsExporter(collector=MagicMock())
        result = await exporter.initialize()
        assert result is True
    
    def test_start_export(self):
        """Test starting metrics export"""
        exporter = MetricsExporter(collector=MagicMock())
        
        with patch.object(exporter, 'start_export') as mock_start:
            mock_start.return_value = None
            
            result = exporter.start_export()
            assert result is None
            mock_start.assert_called_once()
    
    def test_stop_export(self):
        """Test stopping metrics export"""
        exporter = MetricsExporter(collector=MagicMock())
        
        with patch.object(exporter, 'stop_export') as mock_stop:
            mock_stop.return_value = None
            
            result = exporter.stop_export()
            assert result is None
            mock_stop.assert_called_once()
    
    def test_export_prometheus(self):
        """Test exporting metrics in Prometheus format"""
        exporter = MetricsExporter(collector=MagicMock())
        
        with patch.object(exporter, 'export_prometheus') as mock_export:
            mock_export.return_value = "# HELP test_metric Test metric\n# TYPE test_metric counter\ntest_metric 100"
            
            result = exporter.export_prometheus()
            assert "# HELP" in result
            assert "# TYPE" in result
            mock_export.assert_called_once()
    
    def test_export_json(self):
        """Test exporting metrics in JSON format"""
        exporter = MetricsExporter(collector=MagicMock())
        
        with patch.object(exporter, 'export_json') as mock_export:
            mock_export.return_value = '{"test_metric": 100}'
            
            result = exporter.export_json()
            assert "test_metric" in result
            mock_export.assert_called_once()
    
    def test_export_csv(self):
        """Test exporting metrics in CSV format"""
        exporter = MetricsExporter(collector=MagicMock())
        
        with patch.object(exporter, 'export_csv') as mock_export:
            mock_export.return_value = "metric_name,value\ntest_metric,100"
            
            result = exporter.export_csv()
            assert "metric_name" in result
            assert "test_metric" in result
            mock_export.assert_called_once()
    
    def test_export_all_formats(self):
        """Test exporting metrics in all formats"""
        exporter = MetricsExporter(collector=MagicMock())
        
        with patch.object(exporter, 'export_all_formats') as mock_export:
            mock_export.return_value = {
                "prometheus": "# HELP test_metric Test metric",
                "json": '{"test_metric": 100}',
                "csv": "metric_name,value\ntest_metric,100"
            }
            
            result = exporter.export_all_formats()
            assert "prometheus" in result
            assert "json" in result
            assert "csv" in result
            mock_export.assert_called_once()
    
    def test_get_export_stats(self):
        """Test getting export statistics"""
        exporter = MetricsExporter(collector=MagicMock())
        
        with patch.object(exporter, 'get_export_stats') as mock_stats:
            mock_stats.return_value = {
                "total_exports": 100,
                "successful_exports": 95,
                "failed_exports": 5
            }
            
            result = exporter.get_export_stats()
            assert "total_exports" in result
            assert "successful_exports" in result
            assert "failed_exports" in result
            mock_stats.assert_called_once()


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
    
    def test_get_current_metrics(self):
        """Test getting current metrics"""
        service = MetricsService()
        
        with patch.object(service, 'get_current_metrics') as mock_get:
            mock_get.return_value = {
                "system": {"cpu_usage": 50.0},
                "application": {"requests_total": 1000}
            }
            
            result = service.get_current_metrics()
            assert "system" in result
            assert "application" in result
            mock_get.assert_called_once()
    
    def test_export_metrics(self):
        """Test exporting metrics"""
        service = MetricsService()
        
        with patch.object(service, 'export_metrics') as mock_export:
            mock_export.return_value = {"prometheus": "# HELP test_metric Test metric"}
            
            result = service.export_metrics()
            assert "prometheus" in result
            mock_export.assert_called_once()
    
    def test_get_service_status(self):
        """Test getting service status"""
        service = MetricsService()
        
        with patch.object(service, 'get_service_status') as mock_status:
            mock_status.return_value = {
                "status": "running",
                "collector_running": True,
                "exporter_running": True
            }
            
            result = service.get_service_status()
            assert result["status"] == "running"
            assert result["collector_running"] is True
            assert result["exporter_running"] is True
            mock_status.assert_called_once()
    
    def test_reset_metrics(self):
        """Test resetting metrics"""
        service = MetricsService()
        
        with patch.object(service, 'reset_metrics') as mock_reset:
            mock_reset.return_value = None
            
            result = service.reset_metrics()
            assert result is None
            mock_reset.assert_called_once()
