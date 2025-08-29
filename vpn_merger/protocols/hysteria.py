from __future__ import annotations

"""Compatibility shim mapping hysteria to hysteria2 handler when appropriate."""

try:
    from .hysteria2 import Hysteria2Handler as HysteriaHandler  # type: ignore
except Exception:  # pragma: no cover
    class HysteriaHandler:  # type: ignore
        pass

