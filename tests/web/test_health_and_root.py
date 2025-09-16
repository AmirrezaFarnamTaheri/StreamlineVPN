"""
Web API tests: health, root, and static assets.
"""

import pytest
from fastapi.testclient import TestClient

from streamline_vpn.web.unified_api import create_unified_app


class TestAPIBase:
    def setup_method(self):
        self.app = create_unified_app()
        self.client = TestClient(self.app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

    def test_root_endpoint(self):
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data.get("service") == "StreamlineVPN API"

    def test_api_base_js(self):
        response = self.client.get("/api-base.js")
        assert response.status_code == 200
        assert "application/javascript" in response.headers.get("content-type", "")


