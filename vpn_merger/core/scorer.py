from __future__ import annotations

"""Expose scoring functions from existing module."""

try:
    from .quality_scorer import QualityScorer  # type: ignore
except Exception:  # pragma: no cover
    QualityScorer = object  # type: ignore

