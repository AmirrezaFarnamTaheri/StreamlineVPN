"""Run the StreamlineVPN API server."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.utils.logging import get_logger, setup_logging
from streamline_vpn.web.unified_api import create_unified_app  # back-compat

logger = get_logger(__name__)


def main() -> None:
    """Run the API server via Uvicorn."""
    # Initialize logging early for better error reporting
    setup_logging(
        level=os.getenv("STREAMLINE_LOG_LEVEL", os.getenv("VPN_LOG_LEVEL", "INFO")).upper(),
        log_file=os.getenv("STREAMLINE_LOG_FILE", os.getenv("VPN_LOG_FILE")),
    )
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8080"))

    # Prefer the canonical create_app factory if present
    try:
        from streamline_vpn.web.api_app import create_app  # type: ignore

        app = create_app()
        logger.info("Using api_app.create_app() entrypoint")
    except Exception as exc:
        # Fallback to unified wrapper for compatibility
        logger.warning(
            "Falling back to unified_api.create_unified_app() due to import/init error: %s",
            exc,
        )
        app = create_unified_app()

    logger.info("Starting StreamlineVPN API server on %s:%s", host, port)
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down API server...")
    except Exception as exc:
        logger.error("Fatal error: %s", exc, exc_info=True)
        sys.exit(1)
