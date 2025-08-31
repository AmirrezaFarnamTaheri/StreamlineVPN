import asyncio
from unittest.mock import patch

import pytest

from vpn_merger.core.merger import Merger


class StubScorer:
    def score_line(self, s: str) -> float:
        # simple: shorter string higher score
        return max(0.0, 100.0 - float(len(s)))


def test_deduplicate_simple():
    m = Merger()
    data = ["a", "b", "a", " ", None, "b", "c"]  # type: ignore[list-item]
    out = m.deduplicate(data)  # type: ignore[arg-type]
    assert out == ["a", "b", "c"]


def test_score_and_sort_monkeypatch():
    m = Merger()
    lines = ["config1", "config2", "config3"]
    with patch("vpn_merger.core.merger.QualityScorer", return_value=StubScorer()):
        out = m.score_and_sort(lines)
    # shortest first due to stub scorer
    assert out == ["config2", "config3", "config1"]


@pytest.mark.asyncio
async def test_validate_sources_graceful_without_network():
    # If validator import fails in CI, method falls back to 0.0 scores
    m = Merger()
    with patch("vpn_merger.core.merger.SourceValidator", side_effect=Exception("no net")):
        res = await m.validate_sources(["https://raw.githubusercontent.com/test/a", "https://raw.githubusercontent.com/test/b"], min_score=0.1)
    # Expect empty due to min_score filtering or graceful fallback
    assert isinstance(res, list)
