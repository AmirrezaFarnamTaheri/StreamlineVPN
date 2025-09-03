"""
Integrated Web Server for VPN Merger and Configuration Generator
==============================================================

Combines the VPN subscription merger with the configuration generator
in a unified web interface.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from aiohttp import web
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

from .config_generator import VPNConfigGenerator
from .middleware import (
    api_token_middleware,
    audit_middleware,
    create_rate_limit_middleware,
)
from .static_server import StaticFileServer

# Import the aggregator app directly (with fallback)
try:
    from .free_nodes_api_sqla import app as aggregator_app
except ImportError:
    # Fallback if SQLAlchemy is not available
    aggregator_app = None
import os

import uvicorn

from ..analytics.advanced_dashboard import AnalyticsDashboard
from ..monitoring.observability import init_observability
from .graphql.app import create_graphql_app

logger = logging.getLogger(__name__)


class IntegratedWebServer:
    """Integrated web server combining VPN merger, config generator, and analytics."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        config_generator_port: int = 8080,
        analytics_port: int = 8081,
    ):
        """Initialize the integrated web server.

        Args:
            host: Host address to bind to
            port: Main server port
            config_generator_port: Port for configuration generator
            analytics_port: Port for analytics dashboard
        """
        self.host = host
        self.port = port
        self.config_generator_port = config_generator_port
        self.analytics_port = analytics_port

        # Initialize components
        self.app = web.Application(
            middlewares=[
                api_token_middleware,
                create_rate_limit_middleware(int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))),
                audit_middleware,
            ]
        )
        # Prometheus registry and basic metrics
        self.metrics_registry = CollectorRegistry()
        self.req_counter = Counter(
            "web_requests_total",
            "Total HTTP requests",
            ["path", "method"],
            registry=self.metrics_registry,
        )
        self.req_latency = Histogram(
            "web_request_latency_seconds",
            "Request latency",
            ["path", "method"],
            registry=self.metrics_registry,
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2),
        )
        self.config_generator = VPNConfigGenerator(host, config_generator_port)
        self.analytics_dashboard = AnalyticsDashboard(host, analytics_port)
        self.static_server = StaticFileServer()

        # Setup routes
        self._setup_routes()

        logger.info(f"Integrated web server initialized on {host}:{port}")

    def _setup_routes(self):
        """Setup integrated web application routes."""
        # Main landing page
        self.app.router.add_get("/", self._handle_landing_page)

        # VPN merger endpoints
        self.app.router.add_get("/merger", self._handle_merger_redirect)
        self.app.router.add_get("/api/v1/merger/status", self._handle_merger_status)

        # Configuration generator endpoints
        self.app.router.add_get("/generator", self._handle_generator_redirect)
        self.app.router.add_get("/api/v1/generator/status", self._handle_generator_status)

        # Universal Client & QR endpoints
        self.app.router.add_get("/client", self._handle_client_redirect)

        # Analytics dashboard endpoints
        self.app.router.add_get("/analytics", self._handle_analytics_redirect)
        self.app.router.add_get("/api/v1/analytics/status", self._handle_analytics_status)

        # Nodes aggregator endpoints - mount the FastAPI app
        # Note: This is a simplified approach. For production, consider using aiohttp_fastapi
        self.app.router.add_get("/api/nodes.json", self._handle_nodes_json)
        self.app.router.add_post("/api/ingest", self._handle_ingest)
        self.app.router.add_post("/api/sources", self._handle_sources)
        self.app.router.add_get("/api/sources", self._handle_get_sources)
        self.app.router.add_get("/api/export/singbox", self._handle_export_singbox)
        self.app.router.add_get("/api/export/raw", self._handle_export_raw)
        self.app.router.add_get("/api/health", self._handle_health)

        # Health check
        self.app.router.add_get("/health", self._handle_health)
        # Prometheus metrics
        self.app.router.add_get("/metrics", self._handle_metrics)

        # Static files
        self.app.router.add_static("/static", Path(__file__).parent / "static")
        # Serve OpenAPI YAML and docs index link
        self.app.router.add_get("/docs/openapi.yaml", self._handle_openapi)
        self.app.router.add_get("/docs", self._handle_docs_index)
        self.app.router.add_get("/docs/redoc", self._handle_redoc)
        # Getting Started
        self.app.router.add_get("/getting-started", self._handle_getting_started)

    async def start(self):
        """Start all integrated services."""
        try:
            # Initialize observability if enabled
            init_observability("vpn-merger-web")

            # Start main server
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()

            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()

            # Start configuration generator
            await self.config_generator.start()

            # Start analytics dashboard
            await self.analytics_dashboard.start()

            # Start static file server
            await self.static_server.start(self.host, 8082)

            # Start GraphQL FastAPI server on 8083
            self._graphql_app = create_graphql_app()
            self._graphql_server = uvicorn.Server(
                config=uvicorn.Config(
                    self._graphql_app, host=self.host, port=8083, log_level="info"
                )
            )
            asyncio.create_task(self._graphql_server.serve())

            logger.info("🚀 Integrated web server started:")
            logger.info(f"   • Main server: http://{self.host}:{self.port}")
            logger.info(f"   • Config generator: http://{self.host}:{self.config_generator_port}")
            logger.info(f"   • Analytics dashboard: http://{self.host}:{self.analytics_port}")
            logger.info(f"   • Static files: http://{self.host}:8082")
            logger.info(f"   • GraphQL: http://{self.host}:8083/graphql")

        except Exception as e:
            logger.error(f"Failed to start integrated web server: {e}")
            raise

    async def stop(self):
        """Stop all integrated services."""
        try:
            # Stop all services
            if hasattr(self, "site") and self.site:
                await self.site.stop()
            if hasattr(self, "runner") and self.runner:
                await self.runner.cleanup()

            await self.config_generator.stop()
            await self.analytics_dashboard.stop()
            await self.static_server.stop()

            logger.info("Integrated web server stopped")

        except Exception as e:
            logger.error(f"Error stopping integrated web server: {e}")

    async def _handle_landing_page(self, request: web.Request) -> web.Response:
        """Handle the main landing page."""
        html_content = await self._generate_landing_page()
        return web.Response(text=html_content, content_type="text/html")

    async def _handle_merger_redirect(self, request: web.Request) -> web.Response:
        """Redirect to VPN merger interface."""
        return web.Response(
            text="<script>window.location.href='/api/v1/merger/status';</script>",
            content_type="text/html",
        )

    async def _handle_generator_redirect(self, request: web.Request) -> web.Response:
        """Redirect to configuration generator."""
        return web.Response(
            text=f"<script>window.location.href='http://{self.host}:{self.config_generator_port}';</script>",
            content_type="text/html",
        )

    async def _handle_client_redirect(self, request: web.Request) -> web.Response:
        """Redirect to Universal Client & QR."""
        return web.Response(
            text="<script>window.location.href='/static/universal-client.html';</script>",
            content_type="text/html",
        )

    async def _handle_analytics_redirect(self, request: web.Request) -> web.Response:
        """Redirect to analytics dashboard."""
        return web.Response(
            text=f"<script>window.location.href='http://{self.host}:{self.analytics_port}';</script>",
            content_type="text/html",
        )

    async def _handle_merger_status(self, request: web.Request) -> web.Response:
        """Handle VPN merger status request."""
        return web.json_response(
            {
                "service": "vpn_merger",
                "status": "running",
                "endpoints": {
                    "raw": "/api/v1/sub/raw",
                    "base64": "/api/v1/sub/base64",
                    "singbox": "/api/v1/sub/singbox",
                    "clash": "/api/v1/sub/clash",
                },
            }
        )

    async def _handle_openapi(self, request: web.Request) -> web.Response:
        """Serve OpenAPI YAML file from docs."""
        try:
            openapi_path = Path("docs/api/openapi.yaml")
            if not openapi_path.exists():
                return web.json_response({"error": "openapi not found"}, status=404)
            content = openapi_path.read_text(encoding="utf-8")
            return web.Response(text=content, content_type="application/yaml")
        except Exception as e:
            logger.error(f"Error serving openapi: {e}")
            return web.json_response({"error": "internal"}, status=500)

    async def _handle_docs_index(self, request: web.Request) -> web.Response:
        """Simple docs index page with links."""
        html = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head><meta charset=\"UTF-8\"><title>Docs</title></head>
<body style=\"font-family: sans-serif; margin: 2rem;\">
  <h1>Documentation</h1>
  <ul>
    <li><a href=\"/docs/openapi.yaml\">OpenAPI (REST)</a></li>
    <li><a href=\"/docs/redoc\">OpenAPI (Redoc)</a></li>
    <li><a href=\"http://{self.host}:8083/graphql\">GraphQL Playground</a></li>
  </ul>
  <p>For full site docs, see the published MkDocs site.</p>
 </body>
</html>
"""
        return web.Response(text=html, content_type="text/html")

    async def _handle_redoc(self, request: web.Request) -> web.Response:
        """Serve a minimal Redoc UI pointing to our OpenAPI YAML."""
        redoc_html = """
<!DOCTYPE html>
<html>
  <head>
    <title>API Docs</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style> body { margin: 0; padding: 0; } </style>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
  </head>
  <body>
    <redoc spec-url="/docs/openapi.yaml"></redoc>
  </body>
</html>
"""
        return web.Response(text=redoc_html, content_type="text/html")

    async def _handle_getting_started(self, request: web.Request) -> web.Response:
        html = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Getting Started</title>
  <script src=\"https://cdn.tailwindcss.com\"></script>
  <style> .step {{ border-left: 4px solid #e5e7eb; padding-left: 1rem; }} .step-active {{ border-color: #6366f1; }} </style>
  </head>
<body class=\"bg-gray-50\">
  <div class=\"max-w-3xl mx-auto p-6\">
    <h1 class=\"text-3xl font-bold mb-6\">Getting Started</h1>
    <ol class=\"space-y-4\">
      <li class=\"step step-active\"><strong>Run the server:</strong> <code>python -m vpn_merger --web</code></li>
      <li class=\"step\"><strong>Check health:</strong> <a class=\"text-indigo-600\" href=\"/health\">/health</a></li>
      <li class=\"step\"><strong>REST API:</strong> <a class=\"text-indigo-600\" href=\"/docs/openapi.yaml\">OpenAPI</a> or <a class=\"text-indigo-600\" href=\"/docs/redoc\">Redoc</a></li>
      <li class=\"step\"><strong>GraphQL:</strong> <a class=\"text-indigo-600\" href=\"http://{self.host}:8083/graphql\">Playground</a></li>
      <li class=\"step\"><strong>Metrics:</strong> <a class=\"text-indigo-600\" href=\"/metrics\">/metrics</a></li>
    </ol>
    <div class=\"mt-8 p-4 bg-white rounded shadow\">
      <h2 class=\"font-semibold mb-2\">Security</h2>
      <p>Set <code>API_TOKEN</code> for auth; <code>RATE_LIMIT_PER_MINUTE</code> to throttle; <code>OTEL_ENABLED</code> for tracing.</p>
    </div>
  </div>
</body>
</html>
"""
        return web.Response(text=html, content_type="text/html")

    async def _handle_generator_status(self, request: web.Request) -> web.Response:
        """Handle configuration generator status request."""
        return web.json_response(self.config_generator.get_generator_info())

    async def _handle_analytics_status(self, request: web.Request) -> web.Response:
        """Handle analytics dashboard status request."""
        return web.json_response(self.analytics_dashboard.get_dashboard_info())

    async def _handle_health(self, request: web.Request) -> web.Response:
        """Handle health check request."""
        self.req_counter.labels(path="/health", method=request.method).inc()
        with self.req_latency.labels(path="/health", method=request.method).time():
            return web.json_response(
                {
                    "status": "healthy",
                    "services": {
                        "main_server": "running",
                        "config_generator": self.config_generator.get_generator_info()["status"],
                        "analytics_dashboard": self.analytics_dashboard.get_dashboard_info()[
                            "status"
                        ],
                        "static_server": self.static_server.get_server_info()["status"],
                    },
                    "endpoints": {
                        "main": f"http://{self.host}:{self.port}",
                        "generator": f"http://{self.host}:{self.config_generator_port}",
                        "analytics": f"http://{self.host}:{self.analytics_port}",
                        "static": f"http://{self.host}:8082",
                    },
                }
            )

    async def _handle_metrics(self, request: web.Request) -> web.Response:
        """Expose Prometheus metrics."""
        output = generate_latest(self.metrics_registry)
        return web.Response(body=output, content_type=CONTENT_TYPE_LATEST)

    async def _generate_landing_page(self) -> str:
        """Generate the main landing page HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VPN Merger & Configuration Generator</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card-hover { transition: transform 0.2s, box-shadow 0.2s; }
        .card-hover:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
    </style>
</head>
<body class="min-h-screen bg-gray-50">
    <header class="gradient-bg text-white py-8">
        <div class="max-w-6xl mx-auto px-4 text-center">
            <h1 class="text-4xl font-bold mb-4">VPN Merger & Configuration Generator</h1>
            <p class="text-xl opacity-90">High-performance VPN subscription merger with advanced configuration generation</p>
        </div>

        <!-- Docs Section -->
        <div class="mt-16 bg-white rounded-xl shadow-lg p-8">
            <h2 class="text-3xl font-bold text-gray-800 mb-6 text-center">Documentation</h2>
            <div class="grid md:grid-cols-2 gap-8">
                <div class="space-y-2 text-sm">
                    <div class="flex justify-between">
                        <code class="bg-gray-100 px-2 py-1 rounded">/docs/openapi.yaml</code>
                        <span class="text-gray-600">OpenAPI (REST)</span>
                    </div>
                </div>
                <div class="space-y-2 text-sm">
                    <div class="flex justify-between">
                        <code class="bg-gray-100 px-2 py-1 rounded">/graphql</code>
                        <span class="text-gray-600">GraphQL Playground</span>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <main class="max-w-6xl mx-auto px-4 py-12">
        <div class="grid md:grid-cols-2 lg:grid-cols-5 gap-8">
            <!-- VPN Merger Card -->
            <div class="bg-white rounded-xl shadow-lg p-6 card-hover">
                <div class="text-center mb-6">
                    <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                        </svg>
                    </div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-2">VPN Merger</h2>
                    <p class="text-gray-600">Aggregate and process VPN configurations from multiple sources</p>
                </div>
                <div class="space-y-3">
                    <div class="flex items-center text-sm text-gray-600">
                        <svg class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        500+ VPN sources
                    </div>
                    <div class="flex items-center text-sm text-gray-600">
                        <svg class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        Multiple output formats
                    </div>
                    <div class="flex items-center text-sm text-gray-600">
                        <svg class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        Real-time validation
                    </div>
                </div>
                <div class="mt-6">
                    <a href="/api/v1/merger/status" class="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition duration-200 block text-center">
                        Access VPN Merger
                    </a>
                </div>
            </div>

            <!-- Configuration Generator Card -->
            <div class="bg-white rounded-xl shadow-lg p-6 card-hover">
                <div class="text-center mb-6">
                    <div class="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                        </svg>
                    </div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-2">Config Generator</h2>
                    <p class="text-gray-600">Generate VPN client configurations for multiple protocols</p>
                </div>
                <div class="space-y-3">
                    <div class="flex items-center text-sm text-gray-600">
                        <svg class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        VLESS REALITY
                    </div>
                    <div class="flex items-center text-sm text-gray-600">
                        <svg class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        WireGuard
                    </div>
                    <div class="flex items-center text-sm text-gray-600">
                        <svg class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        Shadowsocks
                    </div>
                </div>
                <div class="mt-6">
                    <a href="/generator" class="w-full bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 transition duration-200 block text-center">
                        Open Generator
                    </a>
                </div>
            </div>

            <!-- Analytics Dashboard Card -->
            <div class="bg-white rounded-xl shadow-lg p-6 card-hover">
                <div class="text-center mb-6">
                    <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                        </svg>
                    </div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-2">Analytics Dashboard</h2>
                    <p class="text-gray-600">Real-time metrics and performance monitoring</p>
                </div>
                <div class="space-y-3">
                    <div class="flex items-center text-sm text-gray-600">
                        <svg class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        Real-time metrics
                    </div>
                    <div class="flex items-center text-sm text-gray-600">
                        <svg class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        Performance trends
                    </div>
                    <div class="flex items-center text-sm text-gray-600">
                        <svg class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        Interactive charts
                    </div>
                </div>
                <div class="mt-6">
                    <a href="/analytics" class="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition duration-200 block text-center">
                        View Dashboard
                    </a>
                </div>
            </div>

            <!-- Universal Client & QR Card -->
            <div class="bg-white rounded-xl shadow-lg p-6 card-hover">
                <div class="text-center mb-6">
                    <div class="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
                        </svg>
                    </div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-2">Universal Client</h2>
                    <p class="text-gray-600">Parse, manage, and export VPN configurations with QR codes</p>
                </div>
                <div class="space-y-3">
                    <div class="flex items-center text-sm text-gray-600">
                        <svg class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        Multi-protocol support
                    </div>
                    <div class="flex items-center text-sm text-gray-600">
                        <svg class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        QR code generation
                    </div>
                    <div class="flex items-center text-sm text-gray-600">
                        <svg class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        Export to sing-box
                    </div>
                </div>
                <div class="mt-6">
                    <a href="/client" class="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition duration-200 block text-center">
                        Open Client
                    </a>
                </div>
            </div>

            <!-- Free Nodes Aggregator Card -->
            <div class="bg-white rounded-xl shadow-lg p-6 card-hover">
                <div class="text-center mb-6">
                    <div class="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9m0-9v9"></path>
                        </svg>
                    </div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-2">Free Nodes</h2>
                    <p class="text-gray-600">Aggregate and verify free VPN nodes from public sources</p>
                </div>
                <div class="space-y-3">
                    <div class="flex items-center text-sm text-gray-600">
                        <svg class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        Auto-validation
                    </div>
                    <div class="flex items-center text-sm text-gray-600">
                        <svg class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        Quality scoring
                    </div>
                    <div class="flex items-center text-sm text-gray-600">
                        <svg class="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        Real-time updates
                    </div>
                </div>
                <div class="mt-6">
                    <a href="/aggregator/health" class="w-full bg-orange-600 text-white py-2 px-4 rounded-lg hover:bg-orange-700 transition duration-200 block text-center">
                        View Free Nodes
                    </a>
                </div>
            </div>
        </div>

        <!-- API Documentation Section -->
        <div class="mt-16 bg-white rounded-xl shadow-lg p-8">
            <h2 class="text-3xl font-bold text-gray-800 mb-6 text-center">API Endpoints</h2>
            <div class="grid md:grid-cols-4 gap-8">
                <div>
                    <h3 class="text-xl font-semibold text-gray-700 mb-4">VPN Merger API</h3>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">GET /api/v1/sub/raw</code>
                            <span class="text-gray-600">Raw subscription</span>
                        </div>
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">GET /api/v1/sub/base64</code>
                            <span class="text-gray-600">Base64 encoded</span>
                        </div>
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">GET /api/v1/sub/singbox</code>
                            <span class="text-gray-600">Sing-box format</span>
                        </div>
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">GET /api/v1/sub/clash</code>
                            <span class="text-gray-600">Clash format</span>
                        </div>
                    </div>
                </div>
                <div>
                    <h3 class="text-xl font-semibold text-gray-700 mb-4">Config Generator API</h3>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">POST /api/v1/generate/vless</code>
                            <span class="text-gray-600">VLESS config</span>
                        </div>
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">POST /api/v1/generate/wireguard</code>
                            <span class="text-gray-600">WireGuard config</span>
                        </div>
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">POST /api/v1/generate/shadowsocks</code>
                            <span class="text-gray-600">Shadowsocks config</span>
                        </div>
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">GET /api/v1/utils/uuid</code>
                            <span class="text-gray-600">Generate UUID</span>
                        </div>
                    </div>
                </div>
                <div>
                    <h3 class="text-xl font-semibold text-gray-700 mb-4">Universal Client API</h3>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">GET /client</code>
                            <span class="text-gray-600">Client interface</span>
                        </div>
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">GET /static/universal-client.html</code>
                            <span class="text-gray-600">Static client</span>
                        </div>
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">POST /api/v1/parse</code>
                            <span class="text-gray-600">Parse links</span>
                        </div>
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">GET /api/v1/export</code>
                            <span class="text-gray-600">Export configs</span>
                        </div>
                    </div>
                </div>
                <div>
                    <h3 class="text-xl font-semibold text-gray-700 mb-4">Free Nodes API</h3>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">GET /aggregator/health</code>
                            <span class="text-gray-600">Health check</span>
                        </div>
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">GET /aggregator/nodes</code>
                            <span class="text-gray-600">Get nodes</span>
                        </div>
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">GET /aggregator/singbox</code>
                            <span class="text-gray-600">Sing-box config</span>
                        </div>
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">GET /aggregator/raw</code>
                            <span class="text-gray-600">Raw links</span>
                        </div>
                        <div class="flex justify-between">
                            <code class="bg-gray-100 px-2 py-1 rounded">GET /aggregator/stats</code>
                            <span class="text-gray-600">Node statistics</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <footer class="bg-gray-800 text-white py-8 mt-16">
        <div class="max-w-6xl mx-auto px-4 text-center">
            <p class="text-gray-400">VPN Merger & Configuration Generator v2.0.0</p>
            <p class="text-sm text-gray-500 mt-2">High-performance VPN subscription processing with advanced configuration generation</p>
        </div>
    </footer>
</body>
</html>
        """

    def get_server_info(self) -> dict[str, Any]:
        """Get comprehensive server information."""
        return {
            "main_server": {
                "host": self.host,
                "port": self.port,
                "url": f"http://{self.host}:{self.port}",
                "status": "running" if hasattr(self, "site") and self.site else "stopped",
            },
            "config_generator": self.config_generator.get_generator_info(),
            "analytics_dashboard": self.analytics_dashboard.get_dashboard_info(),
            "static_server": self.static_server.get_server_info(),
        }

    # Aggregator API handlers
    async def _handle_nodes_json(self, request):
        """Handle GET /api/nodes.json"""
        try:
            # For now, return a simple response. In production, this would call the aggregator
            return web.json_response(
                {"nodes": [], "count": 0, "timestamp": asyncio.get_event_loop().time()}
            )
        except Exception as e:
            logger.error(f"Error handling nodes.json: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)

    async def _handle_ingest(self, request):
        """Handle POST /api/ingest"""
        try:
            data = await request.json()
            return web.json_response({"ingested": 0, "total": 0})
        except Exception as e:
            logger.error(f"Error handling ingest: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)

    async def _handle_sources(self, request):
        """Handle POST /api/sources"""
        try:
            data = await request.json()
            return web.json_response({"added": 0, "total_sources": 0})
        except Exception as e:
            logger.error(f"Error handling sources: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)

    async def _handle_get_sources(self, request):
        """Handle GET /api/sources"""
        try:
            return web.json_response({"sources": []})
        except Exception as e:
            logger.error(f"Error handling get_sources: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)

    async def _handle_export_singbox(self, request):
        """Handle GET /api/export/singbox"""
        try:
            return web.json_response({"outbounds": [], "count": 0})
        except Exception as e:
            logger.error(f"Error handling export_singbox: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)

    async def _handle_export_raw(self, request):
        """Handle GET /api/export/raw"""
        try:
            return web.json_response({"links": [], "count": 0, "subscription": ""})
        except Exception as e:
            logger.error(f"Error handling export_raw: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
