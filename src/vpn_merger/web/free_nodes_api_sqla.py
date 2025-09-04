"""
Backward-compatible entry that re-exports the modular FastAPI app.

Original implementation has been refactored into vpn_merger.web.free_nodes.*
This file is kept so existing run commands keep working:
  uvicorn vpn_merger.web.free_nodes_api_sqla:app
"""

from __future__ import annotations

from .free_nodes.app import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


