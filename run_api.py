#!/usr/bin/env python3
"""API Server Runner for StreamlineVPN"""

import os
import sys
from pathlib import Path
import uvicorn

project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def main():
    try:
        host = os.getenv("API_HOST", "0.0.0.0")
        port = int(os.getenv("API_PORT", "8080"))

        # Use factory pattern for uvicorn to enable reload
        uvicorn.run(
            "streamline_vpn.web.api:create_app",
            host=host,
            port=port,
            reload=True,
            factory=True,
        )
    except ImportError as e:
        print(f"Import error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()