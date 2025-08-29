from __future__ import annotations

"""REST routes that delegate to existing API module if present."""

try:
    from ..rest_endpoints import api as app  # type: ignore
except Exception:  # pragma: no cover
    app = None  # type: ignore

