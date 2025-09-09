"""
API package public surface.

This module re-exports the production FastAPI app factory from
`streamline_vpn.web.api:create_app` to avoid duplicate placeholder endpoints
and inconsistencies. Tests and other modules should import `create_app` from
here and receive the real, fully implemented app.
"""

from ..api import create_app  # type: ignore[F401]  # Re-export the real app

__all__ = [
    "create_app",
]
