"""
Unified API Wrapper
===================

Thin wrapper to expose a stable `create_unified_app()` factory and an `app`
object for Uvicorn/Gunicorn entrypoints, delegating to the main FastAPI app
factory in `web.api`.
"""

from __future__ import annotations

from fastapi import FastAPI

# Reuse the consolidated implementation from web.api
from .api import create_app as _create_app


def create_unified_app() -> FastAPI:
    """Return the unified FastAPI application."""
    return _create_app()


# Uvicorn entrypoint (e.g., `uvicorn streamline_vpn.web.unified_api:app`)
app = create_unified_app()

