"""Main entry point for StreamlineVPN with web interface."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.utils.logging import get_logger
from streamline_vpn.web.settings import Settings
from streamline_vpn.web.static_server import StaticControlServer

logger = get_logger(__name__)


def main() -> None:
    """Run the enhanced StreamlineVPN web interface."""
    settings = Settings()

    # Get dynamic configuration
    host = os.getenv("HOST", "0.0.0.0")
    web_port = int(os.getenv("WEB_PORT", settings.PORT))
    api_port = int(os.getenv("API_PORT", "8080"))

    # Inject API configuration into static files
    server = StaticControlServer(settings=settings)

    # Prefer explicit env override, otherwise use settings-derived base
    server.app.state.api_base = os.getenv("API_BASE_URL", settings.API_BASE)

    @server.app.middleware("http")
    async def add_security_headers(request, call_next):  # noqa: ANN001
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        # Build connect-src targets from configured API base
        from urllib.parse import urlparse
        import os as _os
        api_base = getattr(server.app.state, "api_base", f"http://{host}:{api_port}")
        parsed = urlparse(api_base)
        netloc = parsed.netloc or (parsed.hostname or host)
        if parsed.port and ":" not in netloc:
            netloc = f"{netloc}:{parsed.port}"
        # Derive ws scheme counterpart
        http_scheme = "https" if parsed.scheme == "https" else "http"
        ws_scheme = "wss" if http_scheme == "https" else "ws"
        localhost_api_host = f"localhost:{api_port}"

        # Optional extra connect-src entries via env (space/comma separated)
        extras_raw = _os.getenv("WEB_CONNECT_SRC_EXTRA", "")
        extra_tokens = []
        if extras_raw:
            for tok in [t.strip() for t in extras_raw.replace(",", " ").split() if t.strip()]:
                if "://" in tok:
                    extra_tokens.append(tok)
                else:
                    extra_tokens.append(f"{http_scheme}://{tok}")
                    extra_tokens.append(f"{ws_scheme}://{tok}")
        extra_part = (" " + " ".join(extra_tokens)) if extra_tokens else ""

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; "
            "font-src 'self' data: fonts.gstatic.com; "
            f"connect-src 'self' {http_scheme}://{netloc} {ws_scheme}://{netloc} "
            f"http://{localhost_api_host} ws://{localhost_api_host} wss://{localhost_api_host}{extra_part}; "
            "img-src 'self' data:; "
            "object-src 'none'; frame-ancestors 'none';"
        )
        return response

    logger.info(
        f"""
    ╔══════════════════════════════════════════════════════════╗
    ║           StreamlineVPN Control Center v2.0              ║
    ╠══════════════════════════════════════════════════════════╣
    ║  🌐 Web Interface: http://localhost:{web_port}                   ║
    ║  📊 Control Panel: http://localhost:{web_port}/interactive.html       ║
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
        port=web_port,
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
