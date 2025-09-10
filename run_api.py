"""Run the StreamlineVPN API server."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.utils.logging import get_logger
from streamline_vpn.web.unified_api import create_unified_app  # back-compat

logger = get_logger(__name__)


def main() -> None:
    """Run the API server via Uvicorn."""
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8080"))

    # Prefer the canonical create_app factory if present
    try:
        from streamline_vpn.web.api_app import create_app  # type: ignore

        app = create_app()
    except Exception:
        # Fallback to unified wrapper for compatibility
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

