import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from streamline_vpn.web.unified_api import create_unified_app

@pytest.fixture
def client():
    from streamline_vpn.web.api.routes.webhooks import webhooks
    webhooks.clear()
    app = create_unified_app()
    return TestClient(app)

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
    response = client.delete("/api/v1/webhooks", content='{"url": "http://example.com/webhook", "event": "pipeline_finished"}')
    assert response.status_code == 200
    assert response.json() == {"message": "Webhook deleted successfully"}
    response = client.get("/api/v1/webhooks")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
async def test_pipeline_finished_webhook(mock_post, client):
    client.post("/api/v1/webhooks", json={"url": "http://example.com/webhook", "event": "pipeline_finished"})

    with patch("streamline_vpn.web.unified_api.StreamlineVPNMerger") as mock_merger:
        client.app.state.merger = mock_merger
        mock_merger.process_all.return_value = {"success": True}
        client.app.merger = mock_merger
        response = client.post("/api/v1/pipeline/run", json={})
        assert response.status_code == 202

    await asyncio.sleep(0.1)
    mock_post.assert_called_once()
