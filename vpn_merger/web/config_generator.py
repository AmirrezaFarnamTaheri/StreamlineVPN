"""
VPN Configuration Generator Web Interface
========================================

Web-based interface for generating VPN client configurations including
VLESS REALITY, sing-box JSON, WireGuard, and Shadowsocks.
"""

import base64
import json
import logging
import secrets
import uuid
from pathlib import Path
from typing import Any

import aiofiles
from aiohttp import web

logger = logging.getLogger(__name__)


class VPNConfigGenerator:
    """Web-based VPN configuration generator with multiple protocol support.

    Features:
    - VLESS REALITY client link generation
    - sing-box JSON configuration generation
    - WireGuard client configuration
    - Shadowsocks link generation
    - QR code generation for mobile clients
    - Real-time validation and error handling
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        """Initialize the VPN configuration generator.

        Args:
            host: Host address to bind to
            port: Port number to bind to
        """
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None

        # Setup routes
        self._setup_routes()

        logger.info(f"VPN Config Generator initialized on {host}:{port}")

    def _setup_routes(self):
        """Setup web application routes."""
        # Main generator interface
        self.app.router.add_get("/", self._handle_generator_page)
        self.app.router.add_get("/generator", self._handle_generator_page)

        # API endpoints for configuration generation
        self.app.router.add_post("/api/v1/generate/vless", self._handle_generate_vless)
        self.app.router.add_post("/api/v1/generate/singbox", self._handle_generate_singbox)
        self.app.router.add_post("/api/v1/generate/wireguard", self._handle_generate_wireguard)
        self.app.router.add_post("/api/v1/generate/shadowsocks", self._handle_generate_shadowsocks)

        # Utility endpoints
        self.app.router.add_get("/api/v1/utils/uuid", self._handle_generate_uuid)
        self.app.router.add_get("/api/v1/utils/shortid", self._handle_generate_shortid)
        self.app.router.add_get("/api/v1/utils/password", self._handle_generate_password)
        self.app.router.add_get("/api/v1/utils/wg-key", self._handle_generate_wg_key)

        # Static files
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            self.app.router.add_static("/static", static_dir)

    async def start(self):
        """Start the configuration generator web server."""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()

            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()

            logger.info(f"VPN Config Generator started at http://{self.host}:{self.port}")

        except Exception as e:
            logger.error(f"Failed to start config generator: {e}")
            raise

    async def stop(self):
        """Stop the configuration generator web server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("VPN Config Generator stopped")

    async def _handle_generator_page(self, request: web.Request) -> web.Response:
        """Handle the main generator page request."""
        try:
            html_content = await self._generate_generator_html()
            return web.Response(text=html_content, content_type="text/html")
        except Exception as e:
            logger.error(f"Error handling generator page request: {e}")
            return web.Response(text="Generator Error", status=500)

    async def _handle_generate_vless(self, request: web.Request) -> web.Response:
        """Handle VLESS REALITY configuration generation."""
        try:
            data = await request.json()

            # Validate input
            validation_result = self._validate_vless_input(data)
            if not validation_result["valid"]:
                return web.json_response(
                    {"success": False, "error": validation_result["error"]}, status=400
                )

            # Generate VLESS URI
            vless_uri = self._generate_vless_uri(data)

            return web.json_response(
                {
                    "success": True,
                    "config": {"uri": vless_uri, "type": "vless", "protocol": "reality"},
                }
            )

        except Exception as e:
            logger.error(f"Error generating VLESS config: {e}")
            return web.json_response({"success": False, "error": str(e)}, status=500)

    async def _handle_generate_singbox(self, request: web.Request) -> web.Response:
        """Handle sing-box JSON configuration generation."""
        try:
            data = await request.json()

            # Validate input
            validation_result = self._validate_singbox_input(data)
            if not validation_result["valid"]:
                return web.json_response(
                    {"success": False, "error": validation_result["error"]}, status=400
                )

            # Generate sing-box JSON
            singbox_config = self._generate_singbox_json(data)

            return web.json_response(
                {
                    "success": True,
                    "config": {
                        "json": singbox_config,
                        "type": "singbox",
                        "protocol": "vless-reality",
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error generating sing-box config: {e}")
            return web.json_response({"success": False, "error": str(e)}, status=500)

    async def _handle_generate_wireguard(self, request: web.Request) -> web.Response:
        """Handle WireGuard configuration generation."""
        try:
            data = await request.json()

            # Validate input
            validation_result = self._validate_wireguard_input(data)
            if not validation_result["valid"]:
                return web.json_response(
                    {"success": False, "error": validation_result["error"]}, status=400
                )

            # Generate WireGuard config
            wg_config = self._generate_wireguard_config(data)

            return web.json_response(
                {"success": True, "config": {"config": wg_config, "type": "wireguard"}}
            )

        except Exception as e:
            logger.error(f"Error generating WireGuard config: {e}")
            return web.json_response({"success": False, "error": str(e)}, status=500)

    async def _handle_generate_shadowsocks(self, request: web.Request) -> web.Response:
        """Handle Shadowsocks configuration generation."""
        try:
            data = await request.json()

            # Validate input
            validation_result = self._validate_shadowsocks_input(data)
            if not validation_result["valid"]:
                return web.json_response(
                    {"success": False, "error": validation_result["error"]}, status=400
                )

            # Generate Shadowsocks URI
            ss_uri = self._generate_shadowsocks_uri(data)

            return web.json_response(
                {"success": True, "config": {"uri": ss_uri, "type": "shadowsocks"}}
            )

        except Exception as e:
            logger.error(f"Error generating Shadowsocks config: {e}")
            return web.json_response({"success": False, "error": str(e)}, status=500)

    async def _handle_generate_uuid(self, request: web.Request) -> web.Response:
        """Generate a new UUID."""
        return web.json_response({"uuid": str(uuid.uuid4())})

    async def _handle_generate_shortid(self, request: web.Request) -> web.Response:
        """Generate a new short ID for REALITY."""
        length = int(request.query.get("length", 8))
        length = max(2, min(16, length))  # Clamp between 2 and 16
        short_id = "".join(secrets.choice("0123456789abcdef") for _ in range(length))
        return web.json_response({"short_id": short_id})

    async def _handle_generate_password(self, request: web.Request) -> web.Response:
        """Generate a secure password."""
        length = int(request.query.get("length", 20))
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*"
        password = "".join(secrets.choice(chars) for _ in range(length))
        return web.json_response({"password": password})

    async def _handle_generate_wg_key(self, request: web.Request) -> web.Response:
        """Generate a WireGuard key (placeholder - use wg genkey for production)."""
        # This is a placeholder - in production, use actual wg genkey
        key_bytes = secrets.token_bytes(32)
        key_b64 = base64.b64encode(key_bytes).decode("ascii")
        return web.json_response({"key": key_b64})

    def _validate_vless_input(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate VLESS REALITY input parameters."""
        required_fields = ["host", "port", "uuid", "sni", "pbk"]

        for field in required_fields:
            if field not in data or not data[field]:
                return {"valid": False, "error": f"Missing required field: {field}"}

        # Validate hostname/IP
        if not self._is_valid_hostname(data["host"]):
            return {"valid": False, "error": "Invalid hostname or IP address"}

        # Validate port
        try:
            port = int(data["port"])
            if not (1 <= port <= 65535):
                return {"valid": False, "error": "Port must be between 1 and 65535"}
        except (ValueError, TypeError):
            return {"valid": False, "error": "Invalid port number"}

        # Validate UUID
        if not self._is_valid_uuid(data["uuid"]):
            return {"valid": False, "error": "Invalid UUID format"}

        # Validate public key
        if not self._is_valid_pbk(data["pbk"]):
            return {"valid": False, "error": "Invalid public key format"}

        # Validate short ID if provided
        if data.get("sid"):
            if not self._is_valid_shortid(data["sid"]):
                return {
                    "valid": False,
                    "error": "Invalid short ID format (must be hex, 2-16 chars)",
                }

        return {"valid": True}

    def _validate_singbox_input(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate sing-box input parameters."""
        return self._validate_vless_input(data)  # Same validation for now

    def _validate_wireguard_input(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate WireGuard input parameters."""
        required_fields = ["endpoint", "server_public_key", "client_private_key"]

        for field in required_fields:
            if field not in data or not data[field]:
                return {"valid": False, "error": f"Missing required field: {field}"}

        # Validate endpoint format
        if ":" not in data["endpoint"]:
            return {"valid": False, "error": "Endpoint must be in format host:port"}

        return {"valid": True}

    def _validate_shadowsocks_input(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate Shadowsocks input parameters."""
        required_fields = ["host", "port", "method", "password"]

        for field in required_fields:
            if field not in data or not data[field]:
                return {"valid": False, "error": f"Missing required field: {field}"}

        # Validate hostname/IP
        if not self._is_valid_hostname(data["host"]):
            return {"valid": False, "error": "Invalid hostname or IP address"}

        # Validate port
        try:
            port = int(data["port"])
            if not (1 <= port <= 65535):
                return {"valid": False, "error": "Port must be between 1 and 65535"}
        except (ValueError, TypeError):
            return {"valid": False, "error": "Invalid port number"}

        return {"valid": True}

    def _generate_vless_uri(self, data: dict[str, Any]) -> str:
        """Generate VLESS REALITY URI."""
        params = {
            "encryption": "none",
            "security": "reality",
            "pbk": data["pbk"],
            "sni": data["sni"],
            "type": "tcp",
        }

        if data.get("sid"):
            params["sid"] = data["sid"]

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"vless://{data['uuid']}@{data['host']}:{data['port']}?{query_string}#ProxyForge"

    def _generate_singbox_json(self, data: dict[str, Any]) -> str:
        """Generate sing-box JSON configuration."""
        config = {
            "log": {"level": "info"},
            "outbounds": [
                {
                    "type": "vless",
                    "server": data["host"],
                    "server_port": int(data["port"]),
                    "uuid": data["uuid"],
                    "tls": {
                        "enabled": True,
                        "server_name": data["sni"],
                        "reality": {
                            "enabled": True,
                            "public_key": data["pbk"],
                            "short_id": data.get("sid", ""),
                        },
                    },
                    "transport": {"type": "tcp"},
                }
            ],
        }

        return json.dumps(config, indent=2)

    def _generate_wireguard_config(self, data: dict[str, Any]) -> str:
        """Generate WireGuard configuration."""
        config_lines = [
            "[Interface]",
            f"PrivateKey = {data['client_private_key']}",
            f"Address = {data.get('address', '10.0.0.2/32')}",
            f"DNS = {data.get('dns', '1.1.1.1, 1.0.0.1')}",
            "",
            "[Peer]",
            f"PublicKey = {data['server_public_key']}",
            f"Endpoint = {data['endpoint']}",
            f"AllowedIPs = {data.get('allowed_ips', '0.0.0.0/0, ::/0')}",
            f"PersistentKeepalive = {data.get('keepalive', '25')}",
        ]

        return "\n".join(config_lines)

    def _generate_shadowsocks_uri(self, data: dict[str, Any]) -> str:
        """Generate Shadowsocks URI."""
        method_password = f"{data['method']}:{data['password']}"
        encoded = base64.b64encode(method_password.encode()).decode()
        return f"ss://{encoded}@{data['host']}:{data['port']}#ProxyForge"

    def _is_valid_hostname(self, hostname: str) -> bool:
        """Validate hostname or IP address."""
        import re

        # Simple hostname/IP validation
        hostname_pattern = (
            r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$"
        )
        ip_pattern = r"^\b\d{1,3}(\.\d{1,3}){3}\b$"
        return bool(re.match(hostname_pattern, hostname) or re.match(ip_pattern, hostname))

    def _is_valid_uuid(self, uuid_str: str) -> bool:
        """Validate UUID format."""
        import re

        # Accept general UUID v4 or similar patterns per tests
        uuid_pattern = (
            r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
        )
        return bool(re.match(uuid_pattern, uuid_str))

    def _is_valid_pbk(self, pbk: str) -> bool:
        """Validate public key format (base64url)."""
        import re

        # Rough check for base64url length
        return bool(re.match(r"^[A-Za-z0-9_-]{40,60}$", pbk))

    def _is_valid_shortid(self, sid: str) -> bool:
        """Validate short ID format."""
        import re

        return bool(re.match(r"^[0-9a-f]{2,16}$", sid, re.IGNORECASE))

    async def _generate_generator_html(self) -> str:
        """Generate the main generator HTML page."""
        # This will be the ProxyForge HTML content
        html_file = Path(__file__).parent / "static" / "generator.html"

        if html_file.exists():
            async with aiofiles.open(html_file, encoding="utf-8") as f:
                return await f.read()
        else:
            # Fallback to embedded HTML
            return self._get_embedded_html()

    def _get_embedded_html(self) -> str:
        """Get the embedded ProxyForge HTML content as fallback."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>ProxyForge — VPN Configuration Generator</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .error { color: red; background: #ffe6e6; padding: 20px; border-radius: 8px; }
        .info { color: blue; background: #e6f3ff; padding: 20px; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="error">
        <h1>Configuration Generator Error</h1>
        <p>The main HTML template file is missing. Please ensure that <code>vpn_merger/web/static/generator.html</code> exists.</p>
        <p>This is a fallback page. The full ProxyForge interface should be available at the correct path.</p>
    </div>
</body>
</html>
        """

    def get_generator_info(self) -> dict[str, Any]:
        """Get generator information."""
        return {
            "host": self.host,
            "port": self.port,
            "url": f"http://{self.host}:{self.port}",
            "status": "running" if self.site else "stopped",
            "supported_protocols": ["vless-reality", "singbox", "wireguard", "shadowsocks"],
        }
