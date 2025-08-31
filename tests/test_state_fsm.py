from pathlib import Path
from vpn_merger.sources.state_fsm import WarmupFSM, SourceState
from vpn_merger.sources.source_validator import SourceHealth


def make_health(url: str, ok: bool, reliability: float) -> SourceHealth:
    h = SourceHealth(url=url)
    h.accessible = ok
    h.reliability_score = reliability
    return h


def test_fsm_progression(tmp_path: Path):
    state_file = tmp_path / "states.json"
    fsm = WarmupFSM(state_file=str(state_file), reliability_threshold=0.8, failure_threshold=3, recovery_successes=2)

    url = "https://example.org/sub.txt"

    # Initially new
    st = fsm.get(url)
    assert st.state == "new"

    # Two successes -> probation
    fsm.update_from_health(url, make_health(url, True, 0.6))
    st = fsm.update_from_health(url, make_health(url, True, 0.65))
    assert st.state in ("probation", "trusted")

    # Increase reliability and checks -> trusted
    fsm.update_from_health(url, make_health(url, True, 0.85))
    st = fsm.update_from_health(url, make_health(url, True, 0.9))
    st = fsm.update_from_health(url, make_health(url, True, 0.9))
    assert st.state == "trusted"

    # Drop reliability -> demote to probation
    st = fsm.update_from_health(url, make_health(url, True, 0.5))
    assert st.state == "probation"

    # Fail repeatedly -> suspended
    st = fsm.update_from_health(url, make_health(url, False, 0.1))
    st = fsm.update_from_health(url, make_health(url, False, 0.1))
    st = fsm.update_from_health(url, make_health(url, False, 0.1))
    assert st.state == "suspended"

    # Recovery -> probation
    st = fsm.update_from_health(url, make_health(url, True, 0.7))
    st = fsm.update_from_health(url, make_health(url, True, 0.7))
    assert st.state == "probation"

