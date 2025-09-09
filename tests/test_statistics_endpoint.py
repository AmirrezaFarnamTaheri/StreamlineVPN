"""Tests for the `/api/v1/statistics` endpoint."""

from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from streamline_vpn.web.api import create_app, get_merger
from streamline_vpn.core.merger import StreamlineVPNMerger


def test_statistics_endpoint_with_mock_merger():
    """
    The statistics endpoint should correctly return data from the merger dependency.
    """
    app = create_app()

    # Create a mock for the StreamlineVPNMerger
    mock_merger_instance = AsyncMock(spec=StreamlineVPNMerger)
    mock_merger_instance.get_statistics.return_value = {
        "total_configs": 100,
        "successful_sources": 10,
        "success_rate": 0.9,
    }

    # Create a dependency override function
    async def override_get_merger():
        return mock_merger_instance

    # Apply the override to the app
    app.dependency_overrides[get_merger] = override_get_merger

    with TestClient(app) as client:
        response = client.get("/api/v1/statistics")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_configs"] == 100
        assert data["successful_sources"] == 10
        assert data["success_rate"] == 0.9

        # Ensure the mock was called
        mock_merger_instance.get_statistics.assert_awaited_once()
