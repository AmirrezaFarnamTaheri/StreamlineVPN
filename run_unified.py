#!/usr/bin/env python3
"""
run_unified.py
==============

Unified run script for StreamlineVPN with all fixes applied.
"""

import os
import sys
import asyncio
import signal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.web.unified_api import create_unified_app
from streamline_vpn.utils.logging import get_logger

logger = get_logger(__name__)


def handle_shutdown(signum, frame):
    """Handle shutdown gracefully."""
    logger.info("Received shutdown signal, cleaning up...")
    sys.exit(0)


def main():
    """Main entry point for unified server."""
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8080"))
    workers = int(os.getenv("WORKERS", "4"))
    
    # Load environment file if exists
    env_file = Path(".env")
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Loaded environment from .env file")
    
    # Create application
    app = create_unified_app()
    
    # Print startup banner
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║         StreamlineVPN Unified API Server v3.0               ║
    ║                                                              ║
    ╠══════════════════════════════════════════════════════════════╣
    ║                                                              ║
    ║  Starting server...                                          ║
    ║  Host: {host:<50} ║
    ║  Port: {port:<50} ║
    ║  Workers: {workers:<47} ║
    ║                                                              ║
    ║  API Documentation: http://{host}:{port}/docs              {padding1}║
    ║  Health Check: http://{host}:{port}/health                 {padding2}║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """.format(
        host=host,
        port=port,
        workers=workers,
        padding1=" " * (34 - len(f"{host}:{port}")),
        padding2=" " * (30 - len(f"{host}:{port}"))
    ))
    
    # Run with uvicorn
    import uvicorn
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=workers if os.getenv("VPN_ENVIRONMENT") == "production" else 1,
        log_level=os.getenv("VPN_LOG_LEVEL", "info").lower(),
        access_log=True,
        use_colors=True,
        server_header=False,
        date_header=True,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {e}", exc_info=True)
        sys.exit(1)
