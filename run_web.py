"""Main entry point for StreamlineVPN with web interface."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi.middleware.cors import CORSMiddleware
from streamline_vpn.utils.logging import get_logger
from streamline_vpn.web.static_server import EnhancedStaticServer
from streamline_vpn.web.settings import Settings

logger = get_logger(__name__)


def main() -> None:
    """Run the enhanced StreamlineVPN web interface with security enhancements."""
    settings = Settings()

    # Basic production validation
    if settings.ENV == "production":
        if not os.environ.get("SSL_CERT_PATH"):
            logger.warning("SSL certificate not configured for production!")
        if len(settings.SECRET_KEY) < 32:
            raise ValueError("Secret key must be at least 32 characters in production")

    server = EnhancedStaticServer(settings=settings)

    server.app.add_middleware(
        CORSMiddleware,
        allow_origins=[f"http://localhost:{settings.PORT}"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @server.app.middleware("http")
    async def add_security_headers(request, call_next):  # noqa: ANN001
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers[
            "Strict-Transport-Security"
        ] = "max-age=31536000; includeSubDomains"
        api_host = settings.API_BASE.replace("http://", "").replace("https://", "")
        response.headers[
            "Content-Security-Policy"
        ] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            f"connect-src 'self' {settings.API_BASE} ws://{api_host} wss://{api_host};"
        )
        return response

    logger.info(
        f"""
    ╔══════════════════════════════════════════════════════════╗
    ║           StreamlineVPN Control Center v2.0              ║
    ╠══════════════════════════════════════════════════════════╣
    ║  🌐 Web Interface: http://localhost:{settings.PORT}                   ║
    ║  📊 Control Panel: http://localhost:{settings.PORT}/interactive.html  ║
    ║  🔄 Auto-Update: Every {settings.UPDATE_INTERVAL / 3600:.1f} hours                     ║
    ║  📡 API Base: {settings.API_BASE}                        ║
    ║  🔒 Environment: {settings.ENV}                                    ║
    ╚══════════════════════════════════════════════════════════╝
    """
    )

    import uvicorn

    ssl_keyfile = os.environ.get("SSL_KEY_PATH")
    ssl_certfile = os.environ.get("SSL_CERT_PATH")

    uvicorn.run(
        server.app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down StreamlineVPN...")
    except Exception as exc:  # noqa: BLE001
        logger.error("Fatal error: %s", exc, exc_info=True)
        sys.exit(1)
