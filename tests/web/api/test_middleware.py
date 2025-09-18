"""
Tests for API middleware.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from tests.web.api.test_app import app

@pytest.fixture
def client():
    """Returns a TestClient for the test app."""
    return TestClient(app)

class TestRequestIDMiddleware:
    """Tests for the Request ID middleware."""

    def test_request_id_header_is_added(self, client):
        """Test that the X-Request-ID header is added to the response."""
        response = client.get("/")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

class TestLoggingMiddleware:
    """Tests for the logging middleware."""

    def test_log_requests(self, client):
        """Test that requests and responses are logged."""
        with patch('streamline_vpn.web.api.middleware.logger') as mock_logger:
            response = client.get("/")
            assert response.status_code == 200

            assert mock_logger.info.call_count >= 2

            start_call = mock_logger.info.call_args_list[0]
            end_call = mock_logger.info.call_args_list[1]

            assert "Request started" in start_call.args
            assert "method" in start_call.kwargs

            assert "Request completed" in end_call.args
            assert "status_code" in end_call.kwargs
            assert end_call.kwargs["status_code"] == 200

class TestExceptionHandlers:
    """Tests for the exception handlers."""

    def test_value_error_handler(self, client):
        """Test the handler for ValueError."""
        response = client.get("/error/value")
        assert response.status_code == 400
        json_response = response.json()
        assert json_response["error"] == "Bad request"
        assert "Test value error" in json_response["message"]

    def test_file_not_found_handler(self, client):
        """Test the handler for FileNotFoundError."""
        response = client.get("/error/filenotfound")
        assert response.status_code == 404
        json_response = response.json()
        assert json_response["error"] == "Not found"
        assert "resource was not found" in json_response["message"]

    def test_general_exception_handler(self, client):
        """Test the handler for a generic Exception."""
        # The TestClient re-raises server-side exceptions.
        # So we assert that the correct exception is raised.
        with pytest.raises(Exception, match="Test generic error"):
            client.get("/error/generic")
