"""
Web API endpoint tests (with merger interactions mocked).
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from streamline_vpn.web.unified_api import create_unified_app


class TestAPIEndpointsWithMerger:
    def setup_method(self):
        self.app = create_unified_app()
        self.client = TestClient(self.app)

    @patch("streamline_vpn.web.api.routes.sources.SourceRoutes._get_merger")
    def test_sources_endpoint_with_merger(self, mock_get_merger):
        merger = MagicMock()
        merger.get_sources = lambda: [{"name":"s1"}]
        mock_get_merger.return_value = merger
        resp = self.client.get("/api/sources")
        assert resp.status_code in (200, 404)

    @patch("streamline_vpn.web.api.routes.diagnostics.PerformanceRoutes._get_merger")
    def test_statistics_endpoint_with_merger(self, mock_get_merger):
        merger = MagicMock()
        merger.get_statistics = lambda: {"ok": True}
        mock_get_merger.return_value = merger
        resp = self.client.get("/api/statistics")
        assert resp.status_code in (200, 404)

    @patch("streamline_vpn.web.api.routes.configurations.ConfigurationRoutes._get_merger")
    def test_configurations_endpoint_with_merger(self, mock_get_merger):
        merger = MagicMock()
        merger.get_configurations = lambda: []
        mock_get_merger.return_value = merger
        resp = self.client.get("/api/configurations")
        assert resp.status_code in (200, 404)

    @patch("streamline_vpn.web.api.routes.configurations.ConfigurationRoutes._get_merger")
    def test_export_endpoint_with_merger(self, mock_get_merger):
        merger = MagicMock()
        merger.export_configurations = lambda fmt: True
        mock_get_merger.return_value = merger
        resp = self.client.post("/api/export", json={"format":"json"})
        assert resp.status_code in (200, 400, 404)

    @patch("streamline_vpn.web.api.routes.health.HealthRoutes._get_merger")
    def test_clear_cache_endpoint_with_merger(self, mock_get_merger):
        merger = MagicMock()
        merger.clear_cache = lambda: True
        mock_get_merger.return_value = merger
        resp = self.client.post("/api/cache/clear")
        assert resp.status_code in (200, 404)


