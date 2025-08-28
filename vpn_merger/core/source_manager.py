from __future__ import annotations

from typing import Dict, List, Optional, Set

from .source_discovery import discover_sources


class IntelligentSourceManager:
    """Dynamic source discovery, quarantine and simple health scoring."""

    def __init__(self, db_connection=None):
        self.db = db_connection
        self._manual: Set[str] = set()
        self._quarantined: Set[str] = set()
        # success_rate, ema_latency_score (0..1000), last_good_ts
        self._health: Dict[str, Dict[str, float]] = {}

    async def discover_new_sources(self) -> List[str]:
        found = await discover_sources()
        return [u for u in found if u not in self._quarantined]

    def add_manual_sources(self, urls: List[str]) -> None:
        self._manual.update(urls)

    def get_known_sources(self) -> Set[str]:
        return set(self._manual)

    def disable_source(self, url: str) -> None:
        self._quarantined.add(url)

    def record_health(self, url: str, ok: bool, rtt_ms: Optional[float]) -> None:
        h = self._health.setdefault(
            url, {"success_rate": 0.0, "ema": 0.0, "last_good_ts": 0.0}
        )
        alpha = 0.3
        ema_contrib = 0.0 if not ok else max(0.0, 1000.0 - float(rtt_ms or 1000.0))
        h["ema"] = (1 - alpha) * h["ema"] + alpha * ema_contrib
        if ok:
            try:
                import time

                h["last_good_ts"] = time.time()
            except Exception:
                pass

    def score(self, url: str) -> float:
        return self._health.get(url, {}).get("ema", 0.0)

    async def update_source_priorities(self) -> List[str]:
        base = list(self._manual)
        base.sort(key=self.score, reverse=True)
        return base


