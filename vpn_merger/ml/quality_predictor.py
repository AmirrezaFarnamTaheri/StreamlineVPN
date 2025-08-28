from __future__ import annotations

from typing import Dict


class QualityPredictor:
    """Heuristic quality predictor placeholder (ML-ready)."""

    def __init__(self):
        self.model = None  # attach trained model if available

    def predict_quality(self, protocol: str, port: int | None, context: Dict) -> float:
        # Heuristic baseline: prefer modern protocols
        score = 50.0
        if protocol in {"Reality", "VLESS"}:
            score += 15
        elif protocol in {"VMess", "Trojan"}:
            score += 10
        if port in {80, 443, 8080, 8443}:
            score -= 5
        score += float(context.get('source_reputation', 0)) * 20
        return max(0.0, min(100.0, score))

