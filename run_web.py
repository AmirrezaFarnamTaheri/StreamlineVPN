"""Run the StreamlineVPN Web Interface."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.utils.logging import get_logger, setup_logging
from streamline_vpn.web.settings import Settings
from streamline_vpn.web.static_server import StaticControlServer

logger = get_logger(__name__)


def validate_environment():
    """Validate environment variables."""
    errors = []
    
    # Validate ports
    web_port = os.getenv("WEB_PORT", "8000")
    api_port = os.getenv("API_PORT", "8080")
    
    try:
        web_port_int = int(web_port)
        if not 1 <= web_port_int <= 65535:
            errors.append(f"Invalid WEB_PORT: {web_port} (must be 1-65535)")
    except ValueError:
        errors.append(f"Invalid WEB_PORT: {web_port} (must be integer)")
    
    try:
        api_port_int = int(api_port)
        if not 1 <= api_port_int <= 65535:
            errors.append(f"Invalid API_PORT: {api_port} (must be 1-65535)")
    except ValueError:
        errors.append(f"Invalid API_PORT: {api_port} (must be integer)")
    
    # Check if docs directory exists
    docs_path = Path(__file__).parent / "docs"
    if not docs_path.exists():
        errors.append(f"Docs directory not found: {docs_path}")
    
    return errors


def main() -> None:
    """Run the web interface with proper API integration."""
    # Initialize logging (before validation and server instantiation)
    setup_logging(
        level=os.getenv("STREAMLINE_LOG_LEVEL", os.getenv("VPN_LOG_LEVEL", "INFO")).upper(),
        log_file=os.getenv("STREAMLINE_LOG_FILE", os.getenv("VPN_LOG_FILE")),
    )
    # Validate environment
    errors = validate_environment()
    if errors:
        for error in errors:
            logger.error(error)
        sys.exit(1)
    
    settings = Settings()
    
    # Configuration
    host = os.getenv("WEB_HOST", "0.0.0.0")
    web_port = int(os.getenv("WEB_PORT", "8000"))
    api_host = os.getenv("API_HOST", "localhost")
    api_port = int(os.getenv("API_PORT", "8080"))
    
    # Set API base URL for frontend
    api_base_url = os.getenv("API_BASE_URL", f"http://{api_host}:{api_port}")
    
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Create server
    try:
        server = StaticControlServer(settings=settings)
        server.app.state.api_base = api_base_url
    except Exception as e:
        logger.error(f"Failed to create server: {e}")
        sys.exit(1)

    # Optional: preflight API health check for operator visibility
    try:
        import urllib.request  # stdlib
        with urllib.request.urlopen(f"{api_base_url}/health", timeout=5) as resp:
            status = getattr(resp, "status", 200)
            if status == 200:
                logger.info("API health check OK at %s", api_base_url)
            else:
                logger.warning("API health check returned HTTP %s at %s", status, api_base_url)
    except Exception:
        # Non-fatal: UI still serves static pages, but certain actions may fail
        logger.warning("API server not responding at %s; continuing to serve UI", api_base_url)

    # Add middleware to inject API base
    @server.app.middleware("http")
    async def inject_api_base(request, call_next):
        response = await call_next(request)
        # Add API base as header for debugging
        response.headers["X-API-Base"] = api_base_url
        return response

    # Simple health endpoint for container/ops checks
    @server.app.get("/health")
    async def health():  # type: ignore[func-returns-value]
        return {"status": "healthy", "timestamp": __import__("datetime").datetime.now().isoformat()}
    
    logger.info(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║           StreamlineVPN Web Interface v2.0               ║
    ╠══════════════════════════════════════════════════════════╣
    ║  🌐 Web Interface: http://localhost:{web_port:<5}              ║
    ║  📊 Control Panel: http://localhost:{web_port}/interactive.html  ║
    ║  📡 API Server: {api_base_url:<25}    ║
    ╚══════════════════════════════════════════════════════════╝
    
    Make sure the API server is running on {api_base_url}
    """)
    
    # Concise startup log for better readability
    logger.info(
        "Web UI starting on http://%s:%d (API %s)", host, web_port, api_base_url
    )

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
