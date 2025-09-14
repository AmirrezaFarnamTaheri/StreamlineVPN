#!/usr/bin/env python3
"""
API Server Runner
=================

Runs the FastAPI backend server.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add src to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from streamline_vpn.web.unified_api import create_unified_app

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8080"))

    app = create_unified_app()

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
