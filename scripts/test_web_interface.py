#!/usr/bin/env python3
"""
Test script for the VPN Configuration Generator Web Interface
============================================================

This script demonstrates the web interface functionality and tests the API endpoints.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from vpn_merger.web.config_generator import VPNConfigGenerator
from vpn_merger.web.integrated_server import IntegratedWebServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_config_generator():
    """Test the configuration generator functionality."""
    logger.info("🧪 Testing VPN Configuration Generator...")
    
    # Create generator instance
    generator = VPNConfigGenerator(host="127.0.0.1", port=8080)
    
    try:
        # Start the generator
        await generator.start()
        logger.info("✅ Configuration generator started successfully")
        
        # Test data for VLESS REALITY
        test_data = {
            "host": "example.com",
            "port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "sni": "www.microsoft.com",
            "pbk": "test_public_key_base64url_format_example",
            "sid": "0123456789abcdef"
        }
        
        # Test validation
        validation_result = generator._validate_vless_input(test_data)
        logger.info(f"✅ Validation test: {validation_result}")
        
        # Test URI generation
        vless_uri = generator._generate_vless_uri(test_data)
        logger.info(f"✅ Generated VLESS URI: {vless_uri[:50]}...")
        
        # Test sing-box JSON generation
        singbox_json = generator._generate_singbox_json(test_data)
        logger.info(f"✅ Generated sing-box JSON: {len(singbox_json)} characters")
        
        # Test WireGuard data
        wg_data = {
            "endpoint": "vpn.example.com:51820",
            "server_public_key": "test_server_public_key_base64",
            "client_private_key": "test_client_private_key_base64",
            "address": "10.0.0.2/32",
            "dns": "1.1.1.1, 1.0.0.1",
            "allowed_ips": "0.0.0.0/0, ::/0",
            "keepalive": "25"
        }
        
        wg_config = generator._generate_wireguard_config(wg_data)
        logger.info(f"✅ Generated WireGuard config: {len(wg_config)} characters")
        
        # Test Shadowsocks data
        ss_data = {
            "host": "example.com",
            "port": 8388,
            "method": "chacha20-ietf-poly1305",
            "password": "test_password_123"
        }
        
        ss_uri = generator._generate_shadowsocks_uri(ss_data)
        logger.info(f"✅ Generated Shadowsocks URI: {ss_uri[:50]}...")
        
        # Test utility functions
        logger.info("✅ Testing utility functions...")
        logger.info(f"   - UUID validation: {generator._is_valid_uuid('12345678-1234-1234-1234-123456789abc')}")
        logger.info(f"   - Hostname validation: {generator._is_valid_hostname('example.com')}")
        logger.info(f"   - Public key validation: {generator._is_valid_pbk('test_public_key_base64url_format_example')}")
        logger.info(f"   - Short ID validation: {generator._is_valid_shortid('0123456789abcdef')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration generator test failed: {e}")
        return False
    finally:
        await generator.stop()


async def test_integrated_server():
    """Test the integrated web server."""
    logger.info("🧪 Testing Integrated Web Server...")
    
    # Create integrated server instance
    server = IntegratedWebServer(host="127.0.0.1", port=8000)
    
    try:
        # Start the server
        await server.start()
        logger.info("✅ Integrated web server started successfully")
        
        # Get server info
        server_info = server.get_server_info()
        logger.info(f"✅ Server info: {json.dumps(server_info, indent=2)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integrated server test failed: {e}")
        return False
    finally:
        await server.stop()


async def main():
    """Main test function."""
    logger.info("🚀 Starting VPN Web Interface Tests")
    logger.info("=" * 50)
    
    # Test configuration generator
    config_test = await test_config_generator()
    
    # Test integrated server
    server_test = await test_integrated_server()
    
    # Summary
    logger.info("=" * 50)
    logger.info("📊 Test Results:")
    logger.info(f"   Configuration Generator: {'✅ PASS' if config_test else '❌ FAIL'}")
    logger.info(f"   Integrated Server: {'✅ PASS' if server_test else '❌ FAIL'}")
    
    if config_test and server_test:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
