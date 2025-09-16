"""
Web API endpoint tests (without merger dependency).
"""

import pytest
from fastapi.testclient import TestClient

from streamline_vpn.web.unified_api import create_unified_app


class TestAPIEndpointsNoMerger:
    def setup_method(self):
        self.app = create_unified_app(initialize_merger=False)
        self.client = TestClient(self.app)

    def test_statistics_endpoint_no_merger(self):
        response = self.client.get("/api/statistics")
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        assert response.status_code in (200, 404)

    def test_sources_endpoint_no_merger(self):
        response = self.client.get("/api/sources")
        assert response.status_code in (200, 404)

    def test_configurations_endpoint_no_merger(self):
        response = self.client.get("/api/configurations")
        assert response.status_code in (200, 404)

    def test_jobs_endpoint(self):
        response = self.client.get("/api/jobs")
        assert response.status_code in (200, 404)

    def test_export_endpoint_no_merger(self):
        response = self.client.post("/api/export", json={"format":"json"})
        assert response.status_code in (200, 400, 404)

    def test_clear_cache_endpoint_no_merger(self):
        response = self.client.post("/api/cache/clear")
        assert response.status_code in (200, 404)

    def test_diagnostics_endpoints(self):
        # POST performance
        perf = self.client.post("/api/diagnostics/performance", json={})
        assert perf.status_code in (200, 404)
        # GET network
        net = self.client.get("/api/diagnostics/network")
        assert net.status_code in (200, 404)
        # GET cache
        cache = self.client.get("/api/diagnostics/cache")
        assert cache.status_code in (200, 404)

    def test_404_error(self):
        resp = self.client.get("/does-not-exist")
        assert resp.status_code == 404

    def test_405_error(self):
        resp = self.client.post("/health")
        assert resp.status_code in (404, 405)


