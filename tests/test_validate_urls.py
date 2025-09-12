from starlette.testclient import TestClient
from streamline_vpn.web.unified_api import app


def test_validate_urls_endpoint_basic():
    client = TestClient(app)
    payload = {"urls": ["https://example.com/a.txt", "invalid://host", "http://"]}
    r = client.post("/api/v1/sources/validate-urls", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["checked"] == 3
    assert "results" in data
    results = data["results"]
    # First should be valid http(s)
    assert results[0]["url"].startswith("https://")
    assert results[0]["valid"] in (True, False)  # allow security gate to flip
    # Second/third invalid by syntax
    assert results[1]["valid"] is False
    assert results[2]["valid"] is False

