"""Run the StreamlineVPN Web Interface."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.utils.logging import get_logger
from streamline_vpn.web.settings import Settings
from streamline_vpn.web.static_server import StaticControlServer

logger = get_logger(__name__)


def main() -> None:
    """Run the web interface with proper API integration."""
    settings = Settings()
    
    # Configuration
    host = os.getenv("WEB_HOST", "0.0.0.0")
    web_port = int(os.getenv("WEB_PORT", "8000"))
    api_host = os.getenv("API_HOST", "localhost")
    api_port = int(os.getenv("API_PORT", "8080"))
    
    # Set API base URL for frontend
    api_base_url = os.getenv("API_BASE_URL", f"http://{api_host}:{api_port}")
    
    # Create server
    server = StaticControlServer(settings=settings)
    server.app.state.api_base = api_base_url
    
    # Add middleware to inject API base
    @server.app.middleware("http")
    async def inject_api_base(request, call_next):
        response = await call_next(request)
        # Add API base as header for debugging
        response.headers["X-API-Base"] = api_base_url
        return response
    
    logger.info(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║           StreamlineVPN Web Interface v2.0               ║
    ╠══════════════════════════════════════════════════════════╣
    ║  🌐 Web Interface: http://localhost:{web_port}                   ║
    ║  📊 Control Panel: http://localhost:{web_port}/interactive.html       ║
    ║  📡 API Server: {api_base_url}                           ║
    ╚══════════════════════════════════════════════════════════╝
    
    Make sure the API server is running on {api_base_url}
    """)
    
    import uvicorn
    uvicorn.run(
        server.app,
        host=host,
        port=web_port,
        log_level="info"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down web interface...")
    except Exception as exc:
        logger.error(f"Fatal error: {exc}", exc_info=True)
        sys.exit(1)

