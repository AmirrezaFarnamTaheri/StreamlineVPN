#!/usr/bin/env python3
"""
Run the StreamlineVPN Unified API server.
"""

import os
import sys
from pathlib import Path

# Ensure local src is preferred over any installed package
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn

from streamline_vpn.web.unified_api import create_unified_app


def main() -> None:
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8080"))
    workers = int(os.getenv("WORKERS", "1"))

    app = create_unified_app()

    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=workers,
        log_level=os.getenv("VPN_LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down Unified API server...")
    except Exception as exc:
        print(f"Fatal error: {exc}")
        sys.exit(1)

