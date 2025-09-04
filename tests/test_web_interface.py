#!/usr/bin/env python3
"""
Test Suite for Web Interface Components
=======================================

Tests the web interface components including:
- Configuration Generator
- Integrated Server
- Free Nodes Aggregator
- Static File Server
"""

import asyncio
import json
from pathlib import Path

import aiofiles
import aiohttp
import pytest

# Import the components to test
pytest.importorskip("pytest_asyncio")

from vpn_merger.web.config_generator import VPNConfigGenerator
from vpn_merger.web.integrated_server import IntegratedWebServer
from vpn_merger.web.static_server import StaticFileServer


class TestWebInterface:
    """Test class for web interface components"""

    @pytest.fixture
    async def config_generator(self):
        """Create a test configuration generator instance"""
        generator = VPNConfigGenerator(host="127.0.0.1", port=8080)
        await generator.start()
        yield generator
        await generator.stop()

    @pytest.fixture
    async def integrated_server(self):
        """Create a test integrated server instance"""
        server = IntegratedWebServer(host="127.0.0.1", port=8000)
        await server.start()
        yield server
        await server.stop()

    @pytest.fixture
    async def static_server(self):
        """Create a test static file server instance"""
        return StaticFileServer()

    async def test_config_generator_initialization(self, config_generator):
        """Test configuration generator initialization"""
        assert config_generator.host == "127.0.0.1"
        assert config_generator.port == 8080
        assert config_generator.app is not None
        assert config_generator.site is not None

    async def test_config_generator_generator_page(self, config_generator):
        """Test the generator page endpoint"""
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8080/") as response:
                assert response.status == 200
                content = await response.text()
                assert "ProxyForge" in content or "Configuration Generator Error" in content

    async def test_config_generator_uuid_endpoint(self, config_generator):
        """Test UUID generation endpoint"""
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8080/api/v1/utils/uuid") as response:
                assert response.status == 200
                data = await response.json()
                assert "uuid" in data
                assert len(data["uuid"]) == 36  # UUID length

    async def test_config_generator_shortid_endpoint(self, config_generator):
        """Test short ID generation endpoint"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://127.0.0.1:8080/api/v1/utils/shortid?length=8"
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "short_id" in data
                assert len(data["short_id"]) == 8

    async def test_config_generator_vless_generation(self, config_generator):
        """Test VLESS configuration generation"""
        test_data = {
            "host": "example.com",
            "port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "sni": "www.microsoft.com",
            "pbk": "test_public_key_1234567890123456789012345678901234567890",
            "sid": "0123456789abcdef",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8080/api/v1/generate/vless", json=test_data
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data["success"] is True
                assert "config" in data
                assert "uri" in data["config"]
                assert data["config"]["uri"].startswith("vless://")

    async def test_config_generator_invalid_input(self, config_generator):
        """Test invalid input handling"""
        invalid_data = {
            "host": "",  # Empty host
            "port": 99999,  # Invalid port
            "uuid": "invalid-uuid",
            "sni": "",
            "pbk": "",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8080/api/v1/generate/vless", json=invalid_data
            ) as response:
                assert response.status == 400
                data = await response.json()
                assert data["success"] is False
                assert "error" in data

    async def test_integrated_server_initialization(self, integrated_server):
        """Test integrated server initialization"""
        assert integrated_server.host == "127.0.0.1"
        assert integrated_server.port == 8000
        assert integrated_server.app is not None
        assert integrated_server.config_generator is not None
        assert integrated_server.analytics_dashboard is not None
        assert integrated_server.static_server is not None

    async def test_integrated_server_landing_page(self, integrated_server):
        """Test the landing page endpoint"""
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8000/") as response:
                assert response.status == 200
                content = await response.text()
                assert "VPN Merger" in content
                assert "Configuration Generator" in content
                assert "Analytics Dashboard" in content

    async def test_integrated_server_health_check(self, integrated_server):
        """Test health check endpoint"""
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8000/health") as response:
                assert response.status == 200
                data = await response.json()
                assert "status" in data
                assert "services" in data

    async def test_integrated_server_merger_redirect(self, integrated_server):
        """Test merger redirect endpoint"""
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8000/merger") as response:
                # Should redirect or return a response
                assert response.status in [200, 302]

    async def test_integrated_server_generator_redirect(self, integrated_server):
        """Test generator redirect endpoint"""
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8000/generator") as response:
                # Should redirect or return a response
                assert response.status in [200, 302]

    async def test_integrated_server_analytics_redirect(self, integrated_server):
        """Test analytics redirect endpoint"""
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8000/analytics") as response:
                # Should redirect or return a response
                assert response.status in [200, 302]

    async def test_static_server_initialization(self, static_server):
        """Test static file server initialization"""
        assert static_server is not None
        info = static_server.get_server_info()
        assert "status" in info

    async def test_static_server_static_files(self, static_server):
        """Test static file serving"""
        # Check if static files exist (support src/ layout and flat layout)
        base = Path(__file__).parent.parent
        candidates = [
            base / "src" / "vpn_merger" / "web" / "static",
            base / "vpn_merger" / "web" / "static",
        ]
        static_dir = next((p for p in candidates if p.exists()), candidates[0])
        assert static_dir.exists()

        generator_html = static_dir / "generator.html"
        assert generator_html.exists()

        # Test reading the file
        async with aiofiles.open(generator_html, encoding="utf-8") as f:
            content = await f.read()
            assert len(content) > 0
            assert "<!DOCTYPE html>" in content

    async def test_config_generator_validation_methods(self, config_generator):
        """Test validation methods"""
        # Test hostname validation
        assert config_generator._is_valid_hostname("example.com") is True
        assert config_generator._is_valid_hostname("192.168.1.1") is True
        assert config_generator._is_valid_hostname("") is False
        assert config_generator._is_valid_hostname("invalid..hostname") is False

        # Test UUID validation
        valid_uuid = "12345678-1234-1234-1234-123456789abc"
        assert config_generator._is_valid_uuid(valid_uuid) is True
        assert config_generator._is_valid_uuid("invalid-uuid") is False

        # Test short ID validation
        assert config_generator._is_valid_shortid("0123456789abcdef") is True
        assert config_generator._is_valid_shortid("invalid") is False
        assert config_generator._is_valid_shortid("") is False

    async def test_config_generator_generation_methods(self, config_generator):
        """Test generation methods"""
        test_data = {
            "host": "example.com",
            "port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "sni": "www.microsoft.com",
            "pbk": "test_public_key_1234567890123456789012345678901234567890",
            "sid": "0123456789abcdef",
        }

        # Test VLESS URI generation
        vless_uri = config_generator._generate_vless_uri(test_data)
        assert vless_uri.startswith("vless://")
        assert "example.com:443" in vless_uri
        assert "encryption=none" in vless_uri
        assert "security=reality" in vless_uri

        # Test sing-box JSON generation
        singbox_json = config_generator._generate_singbox_json(test_data)
        config = json.loads(singbox_json)
        assert "outbounds" in config
        assert len(config["outbounds"]) == 1
        assert config["outbounds"][0]["type"] == "vless"
        assert config["outbounds"][0]["server"] == "example.com"

    async def test_integrated_server_aggregator_handlers(self, integrated_server):
        """Test aggregator API handlers"""
        # Set API token for authentication
        headers = {"X-API-Token": "testtoken"}
        
        # Test nodes.json handler
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8000/api/nodes.json", headers=headers) as response:
                assert response.status == 200
                data = await response.json()
                assert "nodes" in data
                assert "count" in data
                assert "timestamp" in data

        # Test ingest handler
        test_links = ["vless://test@example.com:443"]
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8000/api/ingest", json={"links": test_links}, headers=headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "ingested" in data
                assert "total" in data

        # Test sources handler
        test_sources = ["https://example.com/nodes.txt"]
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8000/api/sources", json={"urls": test_sources}, headers=headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "added" in data
                assert "total_sources" in data

    async def test_error_handling(self, config_generator):
        """Test error handling in web components"""
        # Test invalid JSON
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8080/api/v1/generate/vless", data="invalid json"
            ) as response:
                assert response.status == 500

        # Test missing required fields
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8080/api/v1/generate/vless", json={}
            ) as response:
                assert response.status == 400

    async def test_concurrent_requests(self, config_generator):
        """Test handling of concurrent requests"""

        async def make_request():
            async with aiohttp.ClientSession() as session:
                async with session.get("http://127.0.0.1:8080/api/v1/utils/uuid") as response:
                    return await response.json()

        # Make multiple concurrent requests
        tasks = [make_request() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # All requests should succeed
        for result in results:
            assert "uuid" in result
            assert len(result["uuid"]) == 36


@pytest.mark.asyncio
async def test_web_interface_integration():
    """Integration test for the complete web interface"""
    # This test would run the entire web interface and test end-to-end functionality
    # For now, we'll just verify that all components can be imported and initialized

    # Test that all components can be imported
    from vpn_merger.web.config_generator import VPNConfigGenerator
    from vpn_merger.web.free_nodes_api_sqla import app as aggregator_app
    from vpn_merger.web.integrated_server import IntegratedWebServer
    from vpn_merger.web.static_server import StaticFileServer

    # Test component initialization
    generator = VPNConfigGenerator(host="127.0.0.1", port=8081)
    assert generator is not None

    server = IntegratedWebServer(host="127.0.0.1", port=8001)
    assert server is not None

    static_server = StaticFileServer()
    assert static_server is not None

    # Test that aggregator app exists
    assert aggregator_app is not None

    # Clean up
    await generator.stop()


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
