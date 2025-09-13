#!/usr/bin/env python3
"""
Run the StreamlineVPN Unified API server.
"""

import os
import sys
from pathlib import Path

# Ensure local src is preferred over any installed package
sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.utils.logging import get_logger, setup_logging
from streamline_vpn.web.unified_api import create_unified_app


def main() -> None:
    """Start the unified API server via Uvicorn with robust logging."""
    # Configure logging early
    setup_logging(
        level=os.getenv("STREAMLINE_LOG_LEVEL", os.getenv("VPN_LOG_LEVEL", "INFO")).upper(),
        log_file=os.getenv("STREAMLINE_LOG_FILE", os.getenv("VPN_LOG_FILE")),
    )
    logger = get_logger(__name__)

    host = os.getenv("API_HOST", "0.0.0.0")
    try:
        port = int(os.getenv("API_PORT", "8080"))
        if not 1 <= port <= 65535:
            raise ValueError("API_PORT must be between 1 and 65535")
    except ValueError as e:
        logger.error("Invalid API_PORT: %s", e)
        sys.exit(2)

    try:
        workers = int(os.getenv("WORKERS", "1"))
        if workers < 1:
            raise ValueError("WORKERS must be >= 1")
    except ValueError as e:
        logger.error("Invalid WORKERS: %s", e)
        sys.exit(2)

    try:
        import uvicorn  # Local import so we can show clear error
    except Exception as exc:
        logger.error("Uvicorn is required to run the server: %s", exc)
        logger.info("Install it with: pip install uvicorn[standard]")
        sys.exit(3)

    app = create_unified_app()
    logger.info("Starting StreamlineVPN Unified API on %s:%s (workers=%s)", host, port, workers)

    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=workers,
        log_level=os.getenv("STREAMLINE_LOG_LEVEL", os.getenv("VPN_LOG_LEVEL", "info")).lower(),
    )


if __name__ == "__main__":
    logger = None
    try:
        main()
    except KeyboardInterrupt:
        # Setup a minimal fallback logger if initialization failed before setup
        try:
            logger = get_logger(__name__)
            logger.info("Shutting down Unified API server...")
        except Exception:
            print("\nShutting down Unified API server...")
    except Exception as exc:
        try:
            logger = logger or get_logger(__name__)
            logger.error("Fatal error: %s", exc, exc_info=True)
        except Exception:
            print(f"Fatal error: {exc}")
        sys.exit(1)
