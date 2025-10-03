#!/usr/bin/env python3
"""Unified Server Runner for StreamlineVPN using Hypercorn"""

import os
import sys
import asyncio
from pathlib import Path
from hypercorn.config import Config
from hypercorn.asyncio import serve

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

async def main():
    """Main entry point for unified server using Hypercorn."""
    try:
        from streamline_vpn.web.unified_api import create_unified_app

        host = os.getenv("API_HOST", "0.0.0.0")
        port = int(os.getenv("API_PORT", "8080"))

        config = Config()
        config.bind = [f"{host}:{port}"]
        config.use_reloader = True

        app = create_unified_app()
        await serve(app, config)

    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped gracefully.")