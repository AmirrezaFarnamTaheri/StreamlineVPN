import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from streamline_vpn.web.unified_api import create_unified_app

@pytest.fixture
def client_for_webhook_test():
    from streamline_vpn.web.api.routes.webhooks import webhooks
    from unittest.mock import MagicMock, AsyncMock
    webhooks.clear()
    mock_merger = MagicMock()
    mock_merger.process_all = AsyncMock(return_value={"success": True})
    app = create_unified_app(merger=mock_merger, initialize_merger=False)
    yield TestClient(app)

@pytest.fixture
def client(client_for_webhook_test):
    with patch("streamline_vpn.web.unified_api.UnifiedAPIServer._process_pipeline_async", new_callable=AsyncMock):
        yield client_for_webhook_test

def test_create_webhook(client):
    response = client.post("/api/v1/webhooks", json={"url": "http://example.com/webhook", "event": "pipeline_finished"})
    assert response.status_code == 200
    assert response.json() == {"message": "Webhook created successfully"}

def test_get_webhooks(client):
    client.post("/api/v1/webhooks", json={"url": "http://example.com/webhook", "event": "pipeline_finished"})
    response = client.get("/api/v1/webhooks")
    assert response.status_code == 200
    assert sorted(response.json(), key=lambda x: x['url']) == sorted([{"url": "http://example.com/webhook", "event": "pipeline_finished"}], key=lambda x: x['url'])

def test_delete_webhook(client):
    client.post("/api/v1/webhooks", json={"url": "http://example.com/webhook", "event": "pipeline_finished"})
    response = client.delete("/api/v1/webhooks?url=http://example.com/webhook&event=pipeline_finished")
    assert response.status_code == 200
    assert response.json() == {"message": "Webhook deleted successfully"}
    response = client.get("/api/v1/webhooks")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
@patch("streamline_vpn.web.unified_api.httpx.AsyncClient")
async def test_pipeline_finished_webhook(mock_httpx_client, client_for_webhook_test):
    client_for_webhook_test.post("/api/v1/webhooks", json={"url": "http://example.com/webhook", "event": "pipeline_finished"})

    mock_async_client = AsyncMock()
    mock_httpx_client.return_value.__aenter__.return_value = mock_async_client

    response = client_for_webhook_test.post("/api/v1/pipeline/run", json={})
    assert response.status_code == 202

    await asyncio.sleep(0.5)
    mock_async_client.post.assert_called_once()
