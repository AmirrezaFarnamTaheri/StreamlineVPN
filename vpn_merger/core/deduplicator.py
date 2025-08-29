from __future__ import annotations

from typing import Iterable, List, Optional, Tuple


class Deduplicator:
    """Simple deduplicator with optional Bloom filter acceleration."""

    def __init__(self, capacity: int = 1_000_000, error_rate: float = 0.01):
        self._bloom = None
        try:
            from vpn_merger.services.bloom import BloomFilter  # type: ignore

            self._bloom = BloomFilter(capacity=capacity, error_rate=error_rate)
        except Exception:
            self._bloom = None

    def unique(self, items: Iterable[str]) -> List[str]:
        if self._bloom is None:
            seen = set()
            out: List[str] = []
            for x in items:
                if x not in seen:
                    seen.add(x)
                    out.append(x)
            return out
        out = []
        for x in items:
            if x not in self._bloom:  # type: ignore[operator]
                self._bloom.add(x)  # type: ignore[operator]
                out.append(x)
        return out

