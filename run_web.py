# run_web.py - Main entry point for StreamlineVPN with web interface

"""
StreamlineVPN Web Runner
========================

Main script to run StreamlineVPN with enhanced web interface and auto-update.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from streamline_vpn.web.static_server import EnhancedStaticServer
from streamline_vpn.utils.logging import get_logger

logger = get_logger(__name__)


async def main():
    """Run the enhanced StreamlineVPN web interface."""

    # Configuration
    host = "0.0.0.0"
    port = 8000
    static_dir = "docs"  # Where HTML files are stored
    api_base = "http://localhost:8080"  # Backend API
    update_interval = 28800  # 8 hours

    # Create server
    server = EnhancedStaticServer(
        host=host,
        port=port,
        static_dir=static_dir,
        api_base=api_base,
        update_interval=update_interval
    )

    logger.info(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║           StreamlineVPN Control Center v2.0              ║
    ╠══════════════════════════════════════════════════════════╣
    ║  🌐 Web Interface: http://localhost:{port}                   ║
    ║  📊 Control Panel: http://localhost:{port}/interactive       ║
    ║  🔄 Auto-Update: Every 8 hours                          ║
    ║  📡 API Base: {api_base}                      ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    # Run server with uvicorn
    import uvicorn
    await uvicorn.run(
        server.app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down StreamlineVPN...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
