"""Main entry point for StreamlineVPN with web interface."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.utils.logging import get_logger
from streamline_vpn.web.static_server import EnhancedStaticServer
from streamline_vpn.web.settings import Settings

logger = get_logger(__name__)


def main() -> None:
    """Run the enhanced StreamlineVPN web interface."""
    settings = Settings()
    server = EnhancedStaticServer(settings=settings)

    logger.info(
        f"""
    ╔══════════════════════════════════════════════════════════╗
    ║           StreamlineVPN Control Center v2.0              ║
    ╠══════════════════════════════════════════════════════════╣
    ║  🌐 Web Interface: http://localhost:{settings.PORT}                   ║
    ║  📊 Control Panel: http://localhost:{settings.PORT}/interactive.html       ║
    ║  🔄 Auto-Update: Every {settings.UPDATE_INTERVAL / 3600} hours                          ║
    ║  📡 API Base: {settings.API_BASE}                      ║
    ╚══════════════════════════════════════════════════════════╝
    """
    )

    import uvicorn

    uvicorn.run(server.app, host=settings.HOST, port=settings.PORT, log_level="info")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down StreamlineVPN...")
    except Exception as exc:  # noqa: BLE001
        logger.error("Fatal error: %s", exc, exc_info=True)
        sys.exit(1)
