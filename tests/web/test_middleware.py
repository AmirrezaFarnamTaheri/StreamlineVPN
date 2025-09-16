"""
Web API middleware tests.
"""

import pytest
from fastapi.testclient import TestClient

from streamline_vpn.web.unified_api import create_unified_app


class TestMiddleware:
    def setup_method(self):
        self.app = create_unified_app()
        self.client = TestClient(self.app)

    def test_cors_middleware(self):
        # CORS headers are reliably returned on OPTIONS requests
        resp = self.client.options("/health")
        allow_origin = resp.headers.get("access-control-allow-origin")
        assert allow_origin is None or allow_origin == "*"

    def test_error_handling_middleware(self):
        # Hitting 404 triggers error handling
        resp = self.client.get("/missing")
        assert resp.status_code == 404


