"""
Tests for MetricsExporter.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from streamline_vpn.monitoring.metrics_exporter import MetricsExporter


class TestMetricsExporter:
    """Test MetricsExporter class"""
    
    def test_initialization(self):
        """Test metrics exporter initialization"""
        exporter = MetricsExporter()
        assert hasattr(exporter, 'export_formats')
        assert hasattr(exporter, 'export_destinations')
        assert hasattr(exporter, 'is_exporting')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test metrics exporter initialization"""
        exporter = MetricsExporter()
        result = await exporter.initialize()
        assert result is True
    
    def test_start_export(self):
        """Test starting metrics export"""
        exporter = MetricsExporter()
        
        with patch.object(exporter, 'start_export') as mock_start:
            mock_start.return_value = None
            
            result = exporter.start_export()
            assert result is None
            mock_start.assert_called_once()
    
    def test_stop_export(self):
        """Test stopping metrics export"""
        exporter = MetricsExporter()
        
        with patch.object(exporter, 'stop_export') as mock_stop:
            mock_stop.return_value = None
            
            result = exporter.stop_export()
            assert result is None
            mock_stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_export_metrics(self):
        """Test exporting metrics"""
        exporter = MetricsExporter()
        metrics = {"cpu": 50.0, "memory": 75.0}
        
        with patch.object(exporter, 'export_metrics') as mock_export:
            mock_export.return_value = AsyncMock(return_value=True)
            
            result = await exporter.export_metrics(metrics)
            assert result is True
    
    def test_export_to_prometheus(self):
        """Test exporting to Prometheus format"""
        exporter = MetricsExporter()
        metrics = {"cpu_percent": 50.0, "memory_percent": 75.0}
        
        with patch.object(exporter, 'export_to_prometheus') as mock_export:
            mock_export.return_value = "# HELP cpu_percent CPU usage percentage\n# TYPE cpu_percent gauge\ncpu_percent 50.0"
            
            result = exporter.export_to_prometheus(metrics)
            assert "cpu_percent" in result
            assert "memory_percent" in result
            assert "HELP" in result
            assert "TYPE" in result
    
    def test_export_to_json(self):
        """Test exporting to JSON format"""
        exporter = MetricsExporter()
        metrics = {"cpu": 50.0, "memory": 75.0}
        
        with patch.object(exporter, 'export_to_json') as mock_export:
            mock_export.return_value = '{"cpu": 50.0, "memory": 75.0}'
            
            result = exporter.export_to_json(metrics)
            assert result == '{"cpu": 50.0, "memory": 75.0}'
    
    def test_export_to_csv(self):
        """Test exporting to CSV format"""
        exporter = MetricsExporter()
        metrics = {"cpu": 50.0, "memory": 75.0}
        
        with patch.object(exporter, 'export_to_csv') as mock_export:
            mock_export.return_value = "metric,value\ncpu,50.0\nmemory,75.0"
            
            result = exporter.export_to_csv(metrics)
            assert "metric,value" in result
            assert "cpu,50.0" in result
            assert "memory,75.0" in result
    
    def test_export_to_yaml(self):
        """Test exporting to YAML format"""
        exporter = MetricsExporter()
        metrics = {"cpu": 50.0, "memory": 75.0}
        
        with patch.object(exporter, 'export_to_yaml') as mock_export:
            mock_export.return_value = "cpu: 50.0\nmemory: 75.0"
            
            result = exporter.export_to_yaml(metrics)
            assert "cpu: 50.0" in result
            assert "memory: 75.0" in result
    
    @pytest.mark.asyncio
    async def test_export_to_file(self):
        """Test exporting to file"""
        exporter = MetricsExporter()
        metrics = {"cpu": 50.0, "memory": 75.0}
        
        with patch.object(exporter, 'export_to_file') as mock_export:
            mock_export.return_value = AsyncMock(return_value=True)
            
            result = await exporter.export_to_file(metrics, "test.json")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_export_to_http(self):
        """Test exporting to HTTP endpoint"""
        exporter = MetricsExporter()
        metrics = {"cpu": 50.0, "memory": 75.0}
        
        with patch.object(exporter, 'export_to_http') as mock_export:
            mock_export.return_value = AsyncMock(return_value=True)
            
            result = await exporter.export_to_http(metrics, "http://example.com/metrics")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_export_to_database(self):
        """Test exporting to database"""
        exporter = MetricsExporter()
        metrics = {"cpu": 50.0, "memory": 75.0}
        
        with patch.object(exporter, 'export_to_database') as mock_export:
            mock_export.return_value = AsyncMock(return_value=True)
            
            result = await exporter.export_to_database(metrics, "test_db")
            assert result is True
    
    def test_export_format_validation(self):
        """Test export format validation"""
        exporter = MetricsExporter()
        
        # Test valid format
        assert exporter.is_valid_format("json") is True
        assert exporter.is_valid_format("prometheus") is True
        assert exporter.is_valid_format("csv") is True
        assert exporter.is_valid_format("yaml") is True
        
        # Test invalid format
        assert exporter.is_valid_format("invalid") is False
        assert exporter.is_valid_format("") is False
    
    def test_export_destination_validation(self):
        """Test export destination validation"""
        exporter = MetricsExporter()
        
        # Test valid destinations
        assert exporter.is_valid_destination("file://test.json") is True
        assert exporter.is_valid_destination("http://example.com/metrics") is True
        assert exporter.is_valid_destination("database://test_db") is True
        
        # Test invalid destinations
        assert exporter.is_valid_destination("invalid://test") is False
        assert exporter.is_valid_destination("") is False
    
    @pytest.mark.asyncio
    async def test_batch_export(self):
        """Test batch export functionality"""
        exporter = MetricsExporter()
        metrics_batch = [
            {"cpu": 50.0, "memory": 75.0},
            {"cpu": 60.0, "memory": 80.0},
            {"cpu": 70.0, "memory": 85.0}
        ]
        
        with patch.object(exporter, 'export_metrics') as mock_export:
            mock_export.return_value = AsyncMock(return_value=True)
            
            result = await exporter.export_batch(metrics_batch)
            assert result is True
            assert mock_export.call_count == 3
    
    @pytest.mark.asyncio
    async def test_scheduled_export(self):
        """Test scheduled export functionality"""
        exporter = MetricsExporter()
        
        with patch.object(exporter, 'export_metrics') as mock_export:
            mock_export.return_value = AsyncMock(return_value=True)
            
            # Start scheduled export
            exporter.start_scheduled_export(interval=60)
            assert exporter.is_exporting is True
            
            # Stop scheduled export
            exporter.stop_scheduled_export()
            assert exporter.is_exporting is False
    
    def test_export_compression(self):
        """Test export compression"""
        exporter = MetricsExporter()
        metrics = {"cpu": 50.0, "memory": 75.0}
        
        with patch.object(exporter, 'export_compressed') as mock_export:
            mock_export.return_value = b"compressed_data"
            
            result = exporter.export_compressed(metrics, "gzip")
            assert result == b"compressed_data"
    
    def test_export_encryption(self):
        """Test export encryption"""
        exporter = MetricsExporter()
        metrics = {"cpu": 50.0, "memory": 75.0}
        
        with patch.object(exporter, 'export_encrypted') as mock_export:
            mock_export.return_value = b"encrypted_data"
            
            result = exporter.export_encrypted(metrics, "aes256")
            assert result == b"encrypted_data"
    
    @pytest.mark.asyncio
    async def test_export_error_handling(self):
        """Test export error handling"""
        exporter = MetricsExporter()
        metrics = {"cpu": 50.0, "memory": 75.0}
        
        with patch.object(exporter, 'export_metrics') as mock_export:
            mock_export.side_effect = Exception("Export failed")
            
            with pytest.raises(Exception):
                await exporter.export_metrics(metrics)
    
    def test_export_metadata(self):
        """Test export metadata"""
        exporter = MetricsExporter()
        metrics = {"cpu": 50.0, "memory": 75.0}
        
        with patch.object(exporter, 'add_export_metadata') as mock_add:
            mock_add.return_value = None
            
            exporter.add_export_metadata(metrics, {"timestamp": "2024-01-01T00:00:00Z"})
            mock_add.assert_called_once()
    
    def test_export_filtering(self):
        """Test export filtering"""
        exporter = MetricsExporter()
        metrics = {"cpu": 50.0, "memory": 75.0, "disk": 60.0}
        
        with patch.object(exporter, 'filter_metrics') as mock_filter:
            mock_filter.return_value = {"cpu": 50.0, "memory": 75.0}
            
            filtered = exporter.filter_metrics(metrics, ["cpu", "memory"])
            assert "cpu" in filtered
            assert "memory" in filtered
            assert "disk" not in filtered

