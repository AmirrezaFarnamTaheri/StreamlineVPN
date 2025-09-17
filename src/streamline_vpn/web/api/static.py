"""
Static file serving setup.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path


def setup_static_files(app: FastAPI) -> None:
    """Setup static file serving for the FastAPI application."""

    # Serve static files
    static_path = Path(__file__).parent.parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    # Serve API documentation
    @app.get("/api", response_class=HTMLResponse)
    async def serve_api_base():
        """Serve API documentation page."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>StreamlineVPN API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
                .endpoint { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                .method { display: inline-block; padding: 5px 10px; border-radius: 3px; color: white; font-weight: bold; }
                .get { background: #28a745; }
                .post { background: #007bff; }
                .put { background: #ffc107; color: black; }
                .delete { background: #dc3545; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>StreamlineVPN API</h1>
                <p>Advanced VPN Configuration Manager API</p>
            </div>
            
            <h2>Available Endpoints</h2>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong>/health</strong> - Health check
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong>/sources</strong> - List all sources
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <strong>/sources</strong> - Add new source
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong>/configurations</strong> - List configurations
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <strong>/configurations/process</strong> - Process configurations
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong>/diagnostics/system</strong> - System diagnostics
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong>/diagnostics/performance</strong> - Performance diagnostics
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong>/diagnostics/network</strong> - Network diagnostics
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong>/diagnostics/cache</strong> - Cache diagnostics
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong>/ws</strong> - WebSocket endpoint
            </div>
            
            <h2>Interactive Documentation</h2>
            <p>Visit <a href="/docs">/docs</a> for interactive API documentation.</p>
        </body>
        </html>
        """

    # Root endpoint
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Serve root page."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>StreamlineVPN</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 10px; margin-bottom: 30px; }
                .content { max-width: 800px; margin: 0 auto; }
                .feature { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                .btn { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px; }
                .btn:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 StreamlineVPN</h1>
                <p>Advanced VPN Configuration Manager</p>
            </div>
            
            <div class="content">
                <h2>Welcome to StreamlineVPN</h2>
                <p>A comprehensive tool for managing, merging, and optimizing VPN configurations from multiple sources.</p>
                
                <div class="feature">
                    <h3>🔧 Configuration Management</h3>
                    <p>Efficiently manage VPN configurations from multiple sources with advanced filtering and deduplication.</p>
                </div>
                
                <div class="feature">
                    <h3>🌐 Web Interface</h3>
                    <p>User-friendly web interface for managing sources, viewing configurations, and monitoring system health.</p>
                </div>
                
                <div class="feature">
                    <h3>📊 Real-time Monitoring</h3>
                    <p>Monitor system performance, cache status, and processing statistics in real-time.</p>
                </div>
                
                <div class="feature">
                    <h3>🔒 Security & Validation</h3>
                    <p>Advanced security features with configuration validation and threat analysis.</p>
                </div>
                
                <h3>Quick Links</h3>
                <a href="/api" class="btn">API Documentation</a>
                <a href="/docs" class="btn">Interactive Docs</a>
                <a href="/health" class="btn">Health Check</a>
            </div>
        </body>
        </html>
        """
