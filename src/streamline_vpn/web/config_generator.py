"""
VPN Configuration Generator
===========================

Web-based VPN configuration generator.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from ..core.merger import StreamlineVPNMerger
from ..utils.logging import get_logger

logger = get_logger(__name__)


class VPNConfigGenerator:
    """VPN configuration generator with web interface."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        """Initialize configuration generator.

        Args:
            host: Host to bind to
            port: Port to bind to
        """
        self.host = host
        self.port = port
        self.app = FastAPI(title="StreamlineVPN Config Generator")
        self.merger = StreamlineVPNMerger()
        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            """Serve main page."""
            return self._get_index_html()

        @self.app.get("/api/configs")
        async def get_configs():
            """Get configurations."""
            try:
                configs = await self.merger.get_configurations()
                return {
                    "count": len(configs),
                    "configurations": [config.to_dict() for config in configs],
                }
            except Exception as e:
                logger.error(f"Error getting configs: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/generate")
        async def generate_configs(format_type: str = "json"):
            """Generate configurations in specified format."""
            try:
                results = await self.merger.process_all()
                if results.get("success"):
                    return {"message": "Configurations generated successfully"}
                else:
                    raise HTTPException(
                        status_code=500, detail=results.get("error")
                    )
            except Exception as e:
                logger.error(f"Error generating configs: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/download/{format_type}")
        async def download_configs(format_type: str):
            """Download configurations in specified format."""
            try:
                # Generate configurations
                await self.merger.process_all()

                # Get output file path
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)

                # Find the generated file
                pattern = f"*{format_type}*"
                files = list(output_dir.glob(pattern))

                if not files:
                    raise HTTPException(
                        status_code=404, detail="File not found"
                    )

                return FileResponse(
                    path=files[0],
                    filename=files[0].name,
                    media_type="application/octet-stream",
                )
            except Exception as e:
                logger.error(f"Error downloading configs: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def _get_index_html(self) -> str:
        """Get main HTML page."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>StreamlineVPN Config Generator</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .button { 
                    background: #007bff; color: white; padding: 10px 20px; 
                    border: none; border-radius: 5px; cursor: pointer; margin: 5px;
                }
                .button:hover { background: #0056b3; }
                .config-list { margin: 20px 0; }
                .config-item { 
                    background: #f8f9fa; padding: 10px; margin: 5px 0; 
                    border-radius: 5px; border-left: 4px solid #007bff;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 StreamlineVPN Config Generator</h1>
                <p>Generate and download VPN configurations in multiple formats.</p>
                
                <div>
                    <button class="button" onclick="loadConfigs()">Load Configurations</button>
                    <button class="button" onclick="generateConfigs()">Generate New</button>
                </div>
                
                <div class="config-list" id="configList">
                    <p>Click "Load Configurations" to see available configurations.</p>
                </div>
                
                <div>
                    <h3>Download Formats:</h3>
                    <button class="button" onclick="downloadConfigs('json')">JSON</button>
                    <button class="button" onclick="downloadConfigs('clash')">Clash</button>
                    <button class="button" onclick="downloadConfigs('singbox')">SingBox</button>
                    <button class="button" onclick="downloadConfigs('raw')">Raw</button>
                </div>
            </div>
            
            <script>
                async function loadConfigs() {
                    try {
                        const response = await fetch('/api/configs');
                        const data = await response.json();
                        
                        const configList = document.getElementById('configList');
                        configList.innerHTML = `
                            <h3>Available Configurations (${data.count})</h3>
                            ${data.configurations.map(config => `
                                <div class="config-item">
                                    <strong>${config.protocol}</strong> -
                                    ${config.server}:${config.port}
                                    <br><small>Quality: ${config.quality_score.toFixed(2)}</small>
                                    <br><small>Network: ${config.network}</small>
                                </div>
                            `).join('')}
                        `;
                    } catch (error) {
                        alert(
                            'Error loading configurations: ' + error.message
                        );
                    }
                }

                async function generateConfigs() {
                    try {
                        const response = await fetch('/api/generate', { method: 'POST' });
                        const data = await response.json();
                        alert(data.message);
                        loadConfigs();
                    } catch (error) {
                        alert(
                            'Error generating configurations: ' +
                                error.message
                        );
                    }
                }

                function downloadConfigs(format) {
                    window.open(
                        `/api/download/${format}`, '_blank'
                    );
                }
            </script>
        </body>
        </html>
        """

    async def start(self):
        """Start the configuration generator."""
        logger.info(
            f"Starting VPN Config Generator on {self.host}:{self.port}"
        )
        # Note: In a real implementation, you would use uvicorn to run the app
        # uvicorn.run(self.app, host=self.host, port=self.port)

    async def stop(self):
        """Stop the configuration generator."""
        logger.info("Stopping VPN Config Generator")
