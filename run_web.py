"""Main entry point for StreamlineVPN with web interface."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.utils.logging import get_logger
from streamline_vpn.web.static_server import EnhancedStaticServer

logger = get_logger(__name__)


def main() -> None:
    """Run the enhanced StreamlineVPN web interface."""
    host = "0.0.0.0"
    port = 8000
    static_dir = "docs"
    api_base = "http://localhost:8080"
    update_interval = 28800  # 8 hours

    server = EnhancedStaticServer(
        host=host,
        port=port,
        static_dir=static_dir,
        api_base=api_base,
        update_interval=update_interval,
    )

    logger.info(
        f"""
    ╔══════════════════════════════════════════════════════════╗
    ║           StreamlineVPN Control Center v2.0              ║
    ╠══════════════════════════════════════════════════════════╣
    ║  🌐 Web Interface: http://localhost:{port}                   ║
    ║  📊 Control Panel: http://localhost:{port}/interactive       ║
    ║  🔄 Auto-Update: Every 8 hours                          ║
    ║  📡 API Base: {api_base}                      ║
    ╚══════════════════════════════════════════════════════════╝
    """
    )

    import uvicorn

    uvicorn.run(server.app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down StreamlineVPN...")
    except Exception as exc:  # noqa: BLE001
        logger.error("Fatal error: %s", exc, exc_info=True)
        sys.exit(1)
