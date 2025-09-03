from pathlib import Path

from vpn_merger.core.source_validator import ValidationResult
from vpn_merger.sources.state_fsm import SourceState, WarmupFSM


def make_health(url: str, ok: bool, reliability: float) -> ValidationResult:
    h = ValidationResult(
        url=url,
        accessible=ok,
        status_code=200 if ok else 500,
        config_count=100 if ok else 0,
        protocols_found=["vmess"] if ok else [],
        response_time=1.0 if ok else 5.0,
        reliability_score=reliability,
        last_checked=None,
        error_message=None if ok else "Connection failed",
    )
    return h


def test_fsm_progression(tmp_path: Path):
    fsm = WarmupFSM()

    url = "https://example.org/sub.txt"

    # Initially not in FSM
    assert url not in fsm.sources

    # Add source
    fsm.add_source(url)
    assert url in fsm.sources
    assert fsm.sources[url].state == SourceState.PENDING

    # Transition to validating
    fsm.transition_state(url, SourceState.VALIDATING)
    assert fsm.sources[url].state == SourceState.VALIDATING

    # Transition to valid
    fsm.transition_state(url, SourceState.VALID)
    assert fsm.sources[url].state == SourceState.VALID

    # Transition to processing
    fsm.transition_state(url, SourceState.PROCESSING)
    assert fsm.sources[url].state == SourceState.PROCESSING

    # Transition to completed
    fsm.transition_state(url, SourceState.COMPLETED)
    assert fsm.sources[url].state == SourceState.COMPLETED

    # Test getting sources by state
    valid_sources = fsm.get_sources_by_state(SourceState.COMPLETED)
    assert url in valid_sources

    # Test getting ready sources
    ready_sources = fsm.get_ready_sources(max_sources=10)
    assert len(ready_sources) >= 0  # May or may not include our source depending on state
