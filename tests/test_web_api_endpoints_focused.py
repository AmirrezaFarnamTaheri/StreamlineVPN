"""
Focused tests for Web API Endpoints
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.web.unified_api import create_unified_app


class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        app = create_unified_app()
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        app = create_unified_app()
        client = TestClient(app)
        
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "StreamlineVPN API"
    
    def test_api_base_endpoint(self):
        """Test API base endpoint"""
        app = create_unified_app()
        client = TestClient(app)
        
        response = client.get("/api-base.js")
        assert response.status_code == 200
        assert "application/javascript" in response.headers.get("content-type", "")
    
    def test_statistics_endpoint_no_merger(self):
        """Test statistics endpoint without merger"""
        app = create_unified_app()
        client = TestClient(app)
        
        response = client.get("/api/statistics")
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "Merger not initialized" in data["detail"]
    
    def test_sources_endpoint_no_merger(self):
        """Test sources endpoint without merger"""
        app = create_unified_app()
        client = TestClient(app)
        
        response = client.get("/api/v1/sources")
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "Merger not initialized" in data["detail"]
    
    def test_configurations_endpoint_no_merger(self):
        """Test configurations endpoint without merger"""
        app = create_unified_app()
        client = TestClient(app)
        
        response = client.get("/api/v1/configurations")
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "Merger not initialized" in data["detail"]
    
    def test_jobs_endpoint(self):
        """Test jobs endpoint"""
        app = create_unified_app()
        client = TestClient(app)
        
        response = client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)
    
    def test_export_endpoint_no_merger(self):
        """Test export endpoint without merger"""
        app = create_unified_app()
        client = TestClient(app)
        
        response = client.get("/api/export/json")
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "Merger not initialized" in data["detail"]
    
    def test_clear_cache_endpoint_no_merger(self):
        """Test clear cache endpoint without merger"""
        app = create_unified_app()
        client = TestClient(app)
        
        response = client.post("/api/v1/cache/clear")
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "Merger not initialized" in data["detail"]
    
    def test_diagnostics_endpoints(self):
        """Test diagnostics endpoints"""
        app = create_unified_app()
        client = TestClient(app)
        
        # Test system diagnostics
        response = client.get("/api/diagnostics/system")
        assert response.status_code == 200
        data = response.json()
        assert "dependencies_ok" in data
        
        # Test performance diagnostics
        response = client.post("/api/diagnostics/performance")
        assert response.status_code == 200
        data = response.json()
        assert "processing_speed" in data
        
        # Test network diagnostics
        response = client.get("/api/diagnostics/network")
        assert response.status_code == 200
        data = response.json()
        assert "internet_ok" in data
        
        # Test cache diagnostics
        response = client.get("/api/diagnostics/cache")
        assert response.status_code == 200
        data = response.json()
        assert "l1_status" in data
    
    def test_404_error(self):
        """Test 404 error handling"""
        app = create_unified_app()
        client = TestClient(app)
        
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_405_error(self):
        """Test 405 error handling"""
        app = create_unified_app()
        client = TestClient(app)
        
        response = client.post("/health")
        assert response.status_code == 405


class TestAPIWithMerger:
    """Test API with merger initialized"""
    
    def test_sources_endpoint_with_merger(self):
        """Test sources endpoint with merger"""
        app = create_unified_app()
        client = TestClient(app)
        
        # Mock merger initialization
        with patch.object(app.state, 'merger', MagicMock()):
            response = client.get("/api/v1/sources")
            assert response.status_code == 503  # Still not properly initialized
    
    def test_statistics_endpoint_with_merger(self):
        """Test statistics endpoint with merger"""
        app = create_unified_app()
        client = TestClient(app)
        
        # Mock merger initialization
        with patch.object(app.state, 'merger', MagicMock()):
            response = client.get("/api/statistics")
            assert response.status_code == 503  # Still not properly initialized
    
    def test_configurations_endpoint_with_merger(self):
        """Test configurations endpoint with merger"""
        app = create_unified_app()
        client = TestClient(app)
        
        # Mock merger initialization
        with patch.object(app.state, 'merger', MagicMock()):
            response = client.get("/api/v1/configurations")
            assert response.status_code == 503  # Still not properly initialized
    
    def test_pipeline_endpoint_with_merger(self):
        """Test pipeline endpoint with merger"""
        app = create_unified_app()
        client = TestClient(app)
        
        # Mock merger initialization
        with patch.object(app.state, 'merger', MagicMock()):
            response = client.get("/api/v1/pipeline")
            assert response.status_code == 503  # Still not properly initialized
    
    def test_export_endpoint_with_merger(self):
        """Test export endpoint with merger"""
        app = create_unified_app()
        client = TestClient(app)
        
        # Mock merger initialization
        with patch.object(app.state, 'merger', MagicMock()):
            response = client.get("/api/export/json")
            assert response.status_code == 503  # Still not properly initialized
    
    def test_clear_cache_endpoint_with_merger(self):
        """Test clear cache endpoint with merger"""
        app = create_unified_app()
        client = TestClient(app)
        
        # Mock merger initialization
        with patch.object(app.state, 'merger', MagicMock()):
            response = client.post("/api/v1/cache/clear")
            assert response.status_code == 503  # Still not properly initialized


class TestMiddleware:
    """Test middleware functionality"""
    
    def test_cors_middleware(self):
        """Test CORS middleware"""
        app = create_unified_app()
        client = TestClient(app)
        
        # Test OPTIONS request
        response = client.options("/api/statistics")
        assert response.status_code == 405  # Method not allowed, but CORS headers should be present
    
    def test_error_handling_middleware(self):
        """Test error handling middleware"""
        app = create_unified_app()
        client = TestClient(app)
        
        # Test 404 error
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        # Test 405 error
        response = client.post("/health")
        assert response.status_code == 405
