import pytest
import asyncio
import httpx
from httpx import ASGITransport

from streamline_vpn.web.unified_api import create_unified_app


@pytest.mark.asyncio
async def test_diagnostics_system():
    app = create_unified_app()
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/diagnostics/system")
        assert r.status_code == 200
        data = r.json()
        assert "python_version" in data
        assert "platform" in data


@pytest.mark.asyncio
async def test_diagnostics_performance():
    app = create_unified_app()
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/diagnostics/performance")
        assert r.status_code == 200
        data = r.json()
        assert "baseline_op_ms" in data


@pytest.mark.asyncio
async def test_diagnostics_network():
    app = create_unified_app()
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/diagnostics/network")
        assert r.status_code == 200
        data = r.json()
        assert "internet_ok" in data
        assert "dns_ok" in data


@pytest.mark.asyncio
async def test_diagnostics_cache():
    app = create_unified_app()
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/diagnostics/cache")
        assert r.status_code == 200
        data = r.json()
        assert "l1_status" in data
