"""
HTML Templates for the web interface.

These helpers keep `integrated_server.py` compact and focused on routing
and orchestration, while page markup lives here.
"""

from __future__ import annotations


def render_docs_index(*, host: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Docs</title></head>
<body style="font-family: sans-serif; margin: 2rem;">
  <h1>Documentation</h1>
  <ul>
    <li><a href="/docs/openapi.yaml">OpenAPI (REST)</a></li>
    <li><a href="/docs/redoc">OpenAPI (Redoc)</a></li>
    <li><a href="http://{host}:8083/graphql">GraphQL Playground</a></li>
  </ul>
  <p>For full site docs, see the published MkDocs site.</p>
 </body>
 </html>
"""


def render_redoc() -> str:
    return """
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


def render_getting_started(*, host: str) -> str:
    return f"""
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
      <li class=\"step\"><strong>GraphQL:</strong> <a class=\"text-indigo-600\" href=\"http://{host}:8083/graphql\">Playground</a></li>
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


def render_landing_page(*, host: str, port: int, config_generator_port: int, analytics_port: int) -> str:
    return f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>VPN Merger & Configuration Generator</title>
    <script src=\"https://cdn.tailwindcss.com\"></script>
    <style>
        .gradient-bg {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .card-hover {{ transition: transform 0.2s, box-shadow 0.2s; }}
        .card-hover:hover {{ transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }}
    </style>
</head>
<body class=\"min-h-screen bg-gray-50\">
    <header class=\"gradient-bg text-white py-8\">
        <div class=\"max-w-6xl mx-auto px-4 text-center\">
            <h1 class=\"text-4xl font-bold mb-4\">VPN Merger & Configuration Generator</h1>
            <p class=\"text-xl opacity-90\">High-performance VPN subscription merger with advanced configuration generation</p>
        </div>

        <div class=\"mt-16 bg-white rounded-xl shadow-lg p-8\">
            <h2 class=\"text-3xl font-bold text-gray-800 mb-6 text-center\">Documentation</h2>
            <div class=\"grid md:grid-cols-2 gap-8\">
                <div class=\"space-y-2 text-sm\">
                    <div class=\"flex justify-between\">
                        <code class=\"bg-gray-100 px-2 py-1 rounded\">/docs/openapi.yaml</code>
                        <span class=\"text-gray-600\">OpenAPI (REST)</span>
                    </div>
                </div>
                <div class=\"space-y-2 text-sm\">
                    <div class=\"flex justify-between\">
                        <a class=\"bg-gray-100 px-2 py-1 rounded text-blue-700\" href=\"http://{host}:8083/graphql\">/graphql</a>
                        <span class=\"text-gray-600\">GraphQL Playground</span>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <main class=\"max-w-6xl mx-auto px-4 py-12\">
        <div class=\"grid md:grid-cols-2 lg:grid-cols-4 gap-8\">
            <div class=\"bg-white rounded-xl shadow-lg p-6 card-hover\">
                <h2 class=\"text-2xl font-bold text-gray-800 mb-2\">VPN Merger</h2>
                <p class=\"text-gray-600 mb-4\">Aggregate and process VPN configurations</p>
                <a href=\"/api/v1/merger/status\" class=\"w-full bg-blue-600 text-white py-2 px-4 rounded-lg block text-center\">Access VPN Merger</a>
            </div>
            <div class=\"bg-white rounded-xl shadow-lg p-6 card-hover\">
                <h2 class=\"text-2xl font-bold text-gray-800 mb-2\">Config Generator</h2>
                <p class=\"text-gray-600 mb-4\">Generate client configs for multiple protocols</p>
                <a href=\"http://{host}:{config_generator_port}\" class=\"w-full bg-purple-600 text-white py-2 px-4 rounded-lg block text-center\">Open Generator</a>
            </div>
            <div class=\"bg-white rounded-xl shadow-lg p-6 card-hover\">
                <h2 class=\"text-2xl font-bold text-gray-800 mb-2\">Analytics Dashboard</h2>
                <p class=\"text-gray-600 mb-4\">Monitor system performance and health</p>
                <a href=\"http://{host}:{analytics_port}\" class=\"w-full bg-green-600 text-white py-2 px-4 rounded-lg block text-center\">Open Dashboard</a>
            </div>
            <div class=\"bg-white rounded-xl shadow-lg p-6 card-hover\">
                <h2 class=\"text-2xl font-bold text-gray-800 mb-2\">Universal Client</h2>
                <p class=\"text-gray-600 mb-4\">Parse, manage, and export VPN configs</p>
                <a href=\"/client\" class=\"w-full bg-indigo-600 text-white py-2 px-4 rounded-lg block text-center\">Open Client</a>
            </div>
        </div>

        <div class=\"mt-16 bg-white rounded-xl shadow-lg p-8\">
            <h2 class=\"text-3xl font-bold text-gray-800 mb-6 text-center\">API Endpoints</h2>
            <div class=\"grid md:grid-cols-4 gap-8\">
                <div>
                    <h3 class=\"text-xl font-semibold text-gray-700 mb-4\">VPN Merger API</h3>
                    <div class=\"space-y-2 text-sm\">
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">GET /api/v1/sub/raw</code><span class=\"text-gray-600\">Raw subscription</span></div>
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">GET /api/v1/sub/base64</code><span class=\"text-gray-600\">Base64 encoded</span></div>
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">GET /api/v1/sub/singbox</code><span class=\"text-gray-600\">Sing-box</span></div>
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">GET /api/v1/sub/clash</code><span class=\"text-gray-600\">Clash</span></div>
                    </div>
                </div>
                <div>
                    <h3 class=\"text-xl font-semibold text-gray-700 mb-4\">Config Generator API</h3>
                    <div class=\"space-y-2 text-sm\">
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">POST /api/v1/generate/vless</code><span class=\"text-gray-600\">VLESS</span></div>
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">POST /api/v1/generate/wireguard</code><span class=\"text-gray-600\">WireGuard</span></div>
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">POST /api/v1/generate/shadowsocks</code><span class=\"text-gray-600\">Shadowsocks</span></div>
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">GET /api/v1/utils/uuid</code><span class=\"text-gray-600\">UUID</span></div>
                    </div>
                </div>
                <div>
                    <h3 class=\"text-xl font-semibold text-gray-700 mb-4\">Universal Client API</h3>
                    <div class=\"space-y-2 text-sm\">
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">GET /client</code><span class=\"text-gray-600\">Client</span></div>
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">GET /static/universal-client.html</code><span class=\"text-gray-600\">Static</span></div>
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">POST /api/v1/parse</code><span class=\"text-gray-600\">Parse</span></div>
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">GET /api/v1/export</code><span class=\"text-gray-600\">Export</span></div>
                    </div>
                </div>
                <div>
                    <h3 class=\"text-xl font-semibold text-gray-700 mb-4\">Free Nodes API</h3>
                    <div class=\"space-y-2 text-sm\">
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">GET /aggregator/health</code><span class=\"text-gray-600\">Health</span></div>
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">GET /aggregator/nodes</code><span class=\"text-gray-600\">Nodes</span></div>
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">GET /aggregator/singbox</code><span class=\"text-gray-600\">Sing-box</span></div>
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">GET /aggregator/raw</code><span class=\"text-gray-600\">Raw</span></div>
                        <div class=\"flex justify-between\"><code class=\"bg-gray-100 px-2 py-1 rounded\">GET /aggregator/stats</code><span class=\"text-gray-600\">Stats</span></div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <footer class=\"bg-gray-800 text-white py-8 mt-16\">
        <div class=\"max-w-6xl mx-auto px-4 text-center\">
            <p class=\"text-gray-400\">VPN Merger & Configuration Generator v2.0.0</p>
            <p class=\"text-sm text-gray-500 mt-2\">High-performance VPN subscription processing with advanced configuration generation</p>
        </div>
    </footer>
</body>
</html>
"""

