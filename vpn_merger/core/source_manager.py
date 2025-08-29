from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Set

from .source_discovery import discover_sources
try:
    from vpn_merger.sources.validator import SourceValidator as _SourceValidator
except Exception:  # pragma: no cover - optional import
    _SourceValidator = None  # type: ignore
try:
    # Prefer the intelligent GitHub API-backed discovery when available
    from vpn_merger.discovery.intelligent_discovery import (
        IntelligentSourceDiscovery as _IntelligentSourceDiscovery,
    )
except Exception:  # pragma: no cover - optional import
    _IntelligentSourceDiscovery = None  # type: ignore


class IntelligentSourceManager:
    """Dynamic source discovery, quarantine and simple health scoring."""

    def __init__(self, db_connection=None):
        self.db = db_connection
        self._manual: Set[str] = set()
        self._quarantined: Set[str] = set()
        # success_rate, ema_latency_score (0..1000), last_good_ts
        self._health: Dict[str, Dict[str, float]] = {}

    async def discover_new_sources(self, use_intelligent: bool = True, validate: bool = True, min_score: float = 0.5, timeout: int = 12) -> List[str]:
        """Discover sources using both heuristic and intelligent methods.

        - Always uses the HTML/regex-based fallback discovery (fast, offline-friendly)
        - Optionally augments with GitHub API-based intelligent discovery when available
        - Deduplicates and filters quarantined URLs
        """
        results: Set[str] = set()

        # Baseline heuristic discovery
        try:
            baseline = await discover_sources()
            results.update(baseline)
        except Exception:
            pass

        # Optional intelligent discovery
        if use_intelligent and _IntelligentSourceDiscovery is not None:
            try:
                disc = _IntelligentSourceDiscovery()
                gh_urls = await disc.discover_github_sources()
                results.update(gh_urls)
            except Exception:
                # Ignore API/rate-limit/network errors and proceed with baseline
                pass

        # Filter quarantined and return a stable order
        filtered = [u for u in results if u not in self._quarantined]
        # Optionally validate and gate by reliability score (aggressive pruning)
        if validate and filtered:
            try:
                filtered = await self.validate_sources(filtered, min_score=min_score, timeout=timeout)
            except Exception:
                pass
        filtered.sort()
        return filtered

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

    async def validate_sources(self, urls: List[str], min_score: float = 0.0, timeout: int = 15) -> List[str]:
        """Optionally validate sources using SourceValidator and filter by score.

        Returns URLs with reliability_score >= min_score, preserving input order.
        """
        if _SourceValidator is None:
            return urls
        sv = _SourceValidator()
        ordered: List[str] = []

        async def _run(u: str):
            try:
                res = await sv.validate_source(u, timeout=timeout)
                if float(res.get("reliability_score") or 0.0) >= float(min_score):
                    ordered.append(u)
            except Exception:
                pass

        await asyncio.gather(*[_run(u) for u in urls])
        # Preserve original order
        idx = {u: i for i, u in enumerate(urls)}
        ordered.sort(key=lambda u: idx.get(u, 0))
        return ordered


