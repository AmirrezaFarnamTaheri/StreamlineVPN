"""
Basic tests for web API
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.web.app import create_app


class TestWebAPIBasic:
    """Test basic web API functionality"""

    def test_create_app(self):
        """Test create_app function"""
        app = create_app()
        assert app is not None
        assert app.title == "StreamlineVPN API"

    def test_endpoints_with_uninitialized_merger(self):
        """
        Test API endpoints when the merger fails to initialize.
        The lifespan event handler should catch the exception, and the get_merger
        dependency should raise a 503 error.
        """
        # Create a mock class for StreamlineVPNMerger
        mock_merger_class = MagicMock()
        # Mock the instance that will be created from the class
        mock_merger_instance = mock_merger_class.return_value
        # Mock the initialize method to be an async function that raises an exception
        mock_merger_instance.initialize = AsyncMock(
            side_effect=Exception("Merger initialization failed")
        )

        # Pass the mocked class to the app factory
        app = create_app(merger_class=mock_merger_class)
        with TestClient(app) as client:
            # Test sources endpoint
            response = client.get("/api/v1/sources")
            assert response.status_code == 503
            data = response.json()
            assert "detail" in data
            assert "Merger not initialized" in data["detail"]

            # Test configurations endpoint
            response = client.get("/api/v1/configurations")
            assert response.status_code == 503
            data = response.json()
            assert "detail" in data
            assert "Merger not initialized" in data["detail"]

            # Test clear cache endpoint
            response = client.post("/api/v1/cache/clear")
            assert response.status_code == 503
            data = response.json()
            assert "detail" in data
            assert "Merger not initialized" in data["detail"]

    def test_404_error(self):
        """Test 404 error handling"""
        app = create_app()
        with TestClient(app) as client:
            response = client.get("/nonexistent")
            assert response.status_code == 404