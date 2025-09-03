"""
State Finite State Machine
=========================

State management for VPN source processing.
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SourceState(Enum):
    """Source processing states."""

    PENDING = "pending"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"


@dataclass
class SourceHealth:
    """Source health information."""

    url: str
    state: SourceState
    reliability_score: float
    last_check: float
    error_count: int
    success_count: int
    estimated_configs: int
    protocols_found: list[str]
    last_error: str | None = None


class WarmupFSM:
    """Finite State Machine for source warmup and processing."""

    def __init__(self):
        """Initialize the FSM."""
        self.sources: dict[str, SourceHealth] = {}

    def add_source(self, url: str) -> None:
        """Add a new source to the FSM."""
        if url not in self.sources:
            self.sources[url] = SourceHealth(
                url=url,
                state=SourceState.PENDING,
                reliability_score=0.0,
                last_check=0.0,
                error_count=0,
                success_count=0,
                estimated_configs=0,
                protocols_found=[],
            )

    def transition_state(self, url: str, new_state: SourceState, **kwargs) -> bool:
        """Transition a source to a new state."""
        if url not in self.sources:
            return False

        self.sources[url].state = new_state
        return True

    def get_sources_by_state(self, state: SourceState) -> list[str]:
        """Get all sources in a specific state."""
        return [url for url, health in self.sources.items() if health.state == state]

    def get_ready_sources(self, max_sources: int = 50) -> list[str]:
        """Get sources ready for processing."""
        valid_sources = self.get_sources_by_state(SourceState.VALID)
        pending_sources = self.get_sources_by_state(SourceState.PENDING)
        return (valid_sources + pending_sources)[:max_sources]
