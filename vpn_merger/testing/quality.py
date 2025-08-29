from __future__ import annotations

"""Quality scoring facade using existing scorer where available."""

try:
    from vpn_merger.core.quality_scorer import QualityScorer  # type: ignore
except Exception:  # pragma: no cover
    QualityScorer = None  # type: ignore


def score_config(config: str) -> float:
    if QualityScorer is None:
        return 0.0
    try:
        return float(QualityScorer().score_line(config))  # type: ignore[attr-defined]
    except Exception:
        return 0.0

