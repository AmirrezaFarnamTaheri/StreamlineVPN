"""
Finite State Machine
====================

Finite state machine for source state management.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ..utils.logging import get_logger

logger = get_logger(__name__)


class SourceState(Enum):
    """Source states."""

    UNKNOWN = "unknown"
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILING = "failing"
    BLACKLISTED = "blacklisted"
    MAINTENANCE = "maintenance"
    DISABLED = "disabled"


class SourceEvent(Enum):
    """Source events."""

    ENABLE = "enable"
    DISABLE = "disable"
    SUCCESS = "success"
    FAILURE = "failure"
    BLACKLIST = "blacklist"
    WHITELIST = "whitelist"
    MAINTENANCE_START = "maintenance_start"
    MAINTENANCE_END = "maintenance_end"
    RESET = "reset"


class SourceStateMachine:
    """Finite state machine for source states."""

    def __init__(self, initial_state: SourceState = SourceState.UNKNOWN):
        """Initialize state machine.

        Args:
            initial_state: Initial state
        """
        self.current_state = initial_state
        self.transition_history: List[Dict[str, Any]] = []
        self.state_entry_time = datetime.now()

        # Define state transitions
        self.transitions = {
            SourceState.UNKNOWN: {
                SourceEvent.ENABLE: SourceState.ACTIVE,
                SourceEvent.DISABLE: SourceState.DISABLED,
                SourceEvent.BLACKLIST: SourceState.BLACKLISTED,
                SourceEvent.MAINTENANCE_START: SourceState.MAINTENANCE,
            },
            SourceState.ACTIVE: {
                SourceEvent.DISABLE: SourceState.DISABLED,
                SourceEvent.FAILURE: SourceState.FAILING,
                SourceEvent.BLACKLIST: SourceState.BLACKLISTED,
                SourceEvent.MAINTENANCE_START: SourceState.MAINTENANCE,
            },
            SourceState.INACTIVE: {
                SourceEvent.ENABLE: SourceState.ACTIVE,
                SourceEvent.DISABLE: SourceState.DISABLED,
                SourceEvent.SUCCESS: SourceState.ACTIVE,
                SourceEvent.BLACKLIST: SourceState.BLACKLISTED,
                SourceEvent.MAINTENANCE_START: SourceState.MAINTENANCE,
            },
            SourceState.FAILING: {
                SourceEvent.SUCCESS: SourceState.ACTIVE,
                SourceEvent.FAILURE: SourceState.FAILING,
                SourceEvent.DISABLE: SourceState.DISABLED,
                SourceEvent.BLACKLIST: SourceState.BLACKLISTED,
                SourceEvent.MAINTENANCE_START: SourceState.MAINTENANCE,
            },
            SourceState.BLACKLISTED: {
                SourceEvent.WHITELIST: SourceState.UNKNOWN,
                SourceEvent.RESET: SourceState.UNKNOWN,
            },
            SourceState.MAINTENANCE: {
                SourceEvent.MAINTENANCE_END: SourceState.ACTIVE,
                SourceEvent.DISABLE: SourceState.DISABLED,
                SourceEvent.BLACKLIST: SourceState.BLACKLISTED,
            },
            SourceState.DISABLED: {
                SourceEvent.ENABLE: SourceState.ACTIVE,
                SourceEvent.RESET: SourceState.UNKNOWN,
            },
        }

        # State entry actions
        self.entry_actions: Dict[SourceState, Callable] = {
            SourceState.ACTIVE: self._on_enter_active,
            SourceState.INACTIVE: self._on_enter_inactive,
            SourceState.FAILING: self._on_enter_failing,
            SourceState.BLACKLISTED: self._on_enter_blacklisted,
            SourceState.MAINTENANCE: self._on_enter_maintenance,
            SourceState.DISABLED: self._on_enter_disabled,
        }

        # State exit actions
        self.exit_actions: Dict[SourceState, Callable] = {
            SourceState.ACTIVE: self._on_exit_active,
            SourceState.INACTIVE: self._on_exit_inactive,
            SourceState.FAILING: self._on_exit_failing,
            SourceState.BLACKLISTED: self._on_exit_blacklisted,
            SourceState.MAINTENANCE: self._on_exit_maintenance,
            SourceState.DISABLED: self._on_exit_disabled,
        }

    def transition(
        self, event: SourceEvent, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Transition to new state based on event.

        Args:
            event: Event that triggered transition
            data: Additional data for the transition

        Returns:
            True if transition was successful, False otherwise
        """
        if data is None:
            data = {}

        # Check if transition is valid
        if event not in self.transitions.get(self.current_state, {}):
            logger.warning(
                f"Invalid transition from {self.current_state.value} "
                f"on {event.value}"
            )
            return False

        # Get new state
        new_state = self.transitions[self.current_state][event]

        # Record transition
        transition_record = {
            "from_state": self.current_state.value,
            "to_state": new_state.value,
            "event": event.value,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        self.transition_history.append(transition_record)

        # Execute exit action
        if self.current_state in self.exit_actions:
            self.exit_actions[self.current_state](data)

        # Update state
        old_state = self.current_state
        self.current_state = new_state
        self.state_entry_time = datetime.now()

        # Execute entry action
        if self.current_state in self.entry_actions:
            self.entry_actions[self.current_state](data)

        logger.info(
            f"State transition: {old_state.value} -> "
            f"{self.current_state.value} (event: {event.value})"
        )
        return True

    def can_transition(self, event: SourceEvent) -> bool:
        """Check if transition is possible.

        Args:
            event: Event to check

        Returns:
            True if transition is possible, False otherwise
        """
        return event in self.transitions.get(self.current_state, {})

    def get_valid_events(self) -> List[SourceEvent]:
        """Get list of valid events for current state.

        Returns:
            List of valid events
        """
        return list(self.transitions.get(self.current_state, {}).keys())

    def get_state_duration(self) -> float:
        """Get duration in current state.

        Returns:
            Duration in seconds
        """
        return (datetime.now() - self.state_entry_time).total_seconds()

    def get_transition_history(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get transition history.

        Args:
            limit: Maximum number of transitions to return

        Returns:
            List of transition records
        """
        if limit is None:
            return self.transition_history.copy()
        return self.transition_history[-limit:]

    def reset(self) -> None:
        """Reset state machine to initial state."""
        self.current_state = SourceState.UNKNOWN
        self.transition_history.clear()
        self.state_entry_time = datetime.now()
        logger.info("State machine reset to UNKNOWN")

    # State entry actions
    def _on_enter_active(self, data: Dict[str, Any]) -> None:
        """Action when entering ACTIVE state."""
        logger.debug("Entered ACTIVE state")

    def _on_enter_inactive(self, data: Dict[str, Any]) -> None:
        """Action when entering INACTIVE state."""
        logger.debug("Entered INACTIVE state")

    def _on_enter_failing(self, data: Dict[str, Any]) -> None:
        """Action when entering FAILING state."""
        logger.debug("Entered FAILING state")

    def _on_enter_blacklisted(self, data: Dict[str, Any]) -> None:
        """Action when entering BLACKLISTED state."""
        logger.warning("Entered BLACKLISTED state")

    def _on_enter_maintenance(self, data: Dict[str, Any]) -> None:
        """Action when entering MAINTENANCE state."""
        logger.info("Entered MAINTENANCE state")

    def _on_enter_disabled(self, data: Dict[str, Any]) -> None:
        """Action when entering DISABLED state."""
        logger.debug("Entered DISABLED state")

    # State exit actions
    def _on_exit_active(self, data: Dict[str, Any]) -> None:
        """Action when exiting ACTIVE state."""
        logger.debug("Exited ACTIVE state")

    def _on_exit_inactive(self, data: Dict[str, Any]) -> None:
        """Action when exiting INACTIVE state."""
        logger.debug("Exited INACTIVE state")

    def _on_exit_failing(self, data: Dict[str, Any]) -> None:
        """Action when exiting FAILING state."""
        logger.debug("Exited FAILING state")

    def _on_exit_blacklisted(self, data: Dict[str, Any]) -> None:
        """Action when exiting BLACKLISTED state."""
        logger.info("Exited BLACKLISTED state")

    def _on_exit_maintenance(self, data: Dict[str, Any]) -> None:
        """Action when exiting MAINTENANCE state."""
        logger.info("Exited MAINTENANCE state")

    def _on_exit_disabled(self, data: Dict[str, Any]) -> None:
        """Action when exiting DISABLED state."""
        logger.debug("Exited DISABLED state")

    def __str__(self) -> str:
        """String representation."""
        return (
            f"SourceStateMachine(state={self.current_state.value}, "
            f"duration={self.get_state_duration():.1f}s)"
        )

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"SourceStateMachine(state={self.current_state.value}, "
            f"entry_time={self.state_entry_time.isoformat()}, "
            f"transitions={len(self.transition_history)})"
        )
