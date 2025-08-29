from __future__ import annotations

"""Expose existing Strawberry schema if present."""

try:
    from ..graphql import schema  # type: ignore
except Exception:  # pragma: no cover
    schema = None  # type: ignore

