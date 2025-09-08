"""Main entry point for StreamlineVPN with web interface."""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.utils.logging import get_logger
from streamline_vpn.web.static_server import EnhancedStaticServer
from streamline_vpn.web.settings import Settings

logger = get_logger(__name__)

def main() -> None:
    """Run the enhanced StreamlineVPN web interface."""
    settings = Settings()

    # Get dynamic configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", settings.PORT))
    api_port = int(os.getenv("API_PORT", "8080"))

    # Inject API configuration into static files
    server = EnhancedStaticServer(settings=settings)

    # Add API base configuration
    server.app.state.api_base = f"http://{host}:{api_port}"

    @server.app.middleware("http")
    async def add_security_headers(request, call_next):  # noqa: ANN001
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        api_host = f"{host}:{api_port}"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            f"connect-src 'self' http://{api_host} ws://{api_host} wss://{api_host};"
        )
        return response

    logger.info(
        f"""
    ╔══════════════════════════════════════════════════════════╗
    ║           StreamlineVPN Control Center v2.0              ║
    ╠══════════════════════════════════════════════════════════╣
    ║  🌐 Web Interface: http://localhost:{port}                   ║
    ║  📊 Control Panel: http://localhost:{port}/interactive.html       ║
    ║  🔄 Auto-Update: Every {settings.UPDATE_INTERVAL / 3600} hours                          ║
    ║  📡 API Server: http://localhost:{api_port}                      ║
    ╚══════════════════════════════════════════════════════════╝
    """
    )

    import uvicorn

    ssl_keyfile = os.environ.get("SSL_KEY_PATH")
    ssl_certfile = os.environ.get("SSL_CERT_PATH")

    uvicorn.run(
        server.app,
        host=host,
        port=port,
        log_level="info",
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down StreamlineVPN...")
    except Exception as exc:
        logger.error("Fatal error: %s", exc, exc_info=True)
        sys.exit(1)
