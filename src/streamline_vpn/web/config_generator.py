"""Web-based VPN configuration generator."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse
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
        try:
            self.app.mount(
                "/assets",
                StaticFiles(packages=["streamline_vpn.web.static"]),
                name="assets",
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("Static assets not found: %s", exc)

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
                logger.error("Error getting configs: %s", e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error",
                )

        @self.app.post("/api/generate")
        async def generate_configs(format_type: str = "json"):
            """Generate configurations in specified format."""
            try:
                results = await self.merger.process_all()
                if results.get("success"):
                    return {"message": "Configurations generated successfully"}
                error_msg = results.get("error")
                logger.error("Error generating configs: %s", error_msg)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error",
                )
            except Exception as e:
                logger.error("Error generating configs: %s", e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error",
                )

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
                logger.error("Error downloading configs: %s", e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error",
                )

    def _get_index_html(self) -> str:
        """Get main HTML page."""
        html_path = Path(__file__).parent / "config_generator.html"
        try:
            with open(html_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"HTML file not found at {html_path}")
            return "<h1>Error: HTML file not found</h1>"

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
