"""
API App
=======

Stable `create_app()` factory and `app` object for running the API server with Uvicorn/Gunicorn.
"""

from __future__ import annotations

from fastapi import FastAPI

from .api import create_app as _create_app


def create_app() -> FastAPI:
    """Return the FastAPI application instance."""
    return _create_app()


# Uvicorn entrypoint (e.g., `uvicorn streamline_vpn.web.api_app:app`)
app = create_app()

