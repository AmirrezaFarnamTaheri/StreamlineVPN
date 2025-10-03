#!/usr/bin/env python3
"""Unified Server Runner for StreamlineVPN"""

import os
import sys
from pathlib import Path
import uvicorn

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def main():
    """Main entry point for unified server"""
    try:
        from streamline_vpn.web.unified_api import create_unified_app
        app = create_unified_app()

        host = os.getenv("API_HOST", "0.0.0.0")
        port = int(os.getenv("API_PORT", "8080"))

        uvicorn.run(app, host=host, port=port, reload=True)
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()