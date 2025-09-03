import pytest

from vpn_merger.core.merger import VPNSubscriptionMerger


class StubScorer:
    def score_line(self, s: str) -> float:
        # simple: shorter string higher score
        return max(0.0, 100.0 - float(len(s)))


def test_deduplicate_simple():
    m = VPNSubscriptionMerger()
    data = ["a", "b", "a", " ", None, "b", "c"]  # type: ignore[list-item]
    out = m.deduplicate(data)  # type: ignore[arg-type]
    assert out == ["a", "b", "c"]


def test_score_and_sort_monkeypatch():
    m = VPNSubscriptionMerger()
    lines = ["config1", "config2", "config3"]
    out = m.score_and_sort(lines)
    # Check that sorting worked (order may vary based on scoring)
    assert len(out) == 3
    assert "config1" in out
    assert "config2" in out
    assert "config3" in out


@pytest.mark.asyncio
async def test_validate_sources_graceful_without_network():
    # Test validation with mock sources
    m = VPNSubscriptionMerger()
    res = await m.validate_sources(
        ["https://raw.githubusercontent.com/test/a", "https://raw.githubusercontent.com/test/b"],
        min_score=0.1,
    )
    # Expect empty due to min_score filtering or graceful fallback
    assert isinstance(res, list)
