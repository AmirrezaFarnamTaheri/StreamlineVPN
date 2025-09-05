"""
State Manager
=============

State management system for sources.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .fsm import SourceStateMachine, SourceState, SourceEvent
from ..utils.logging import get_logger

logger = get_logger(__name__)

class StateManager:
    """State management system for sources."""
    
    def __init__(self):
        """Initialize state manager."""
        self.state_machines: Dict[str, SourceStateMachine] = {}
        self.state_history: Dict[str, List[Dict[str, Any]]] = {}
        self.auto_transition_rules: Dict[SourceState, Dict[str, Any]] = {
            SourceState.FAILING: {
                "max_duration": 300,  # 5 minutes
                "max_failures": 5,
                "transition_to": SourceState.BLACKLISTED
            },
            SourceState.INACTIVE: {
                "max_duration": 1800,  # 30 minutes
                "transition_to": SourceState.DISABLED
            }
        }
    
    def get_or_create_state_machine(self, source_id: str) -> SourceStateMachine:
        """Get or create state machine for source.
        
        Args:
            source_id: Source identifier
            
        Returns:
            State machine instance
        """
        if source_id not in self.state_machines:
            self.state_machines[source_id] = SourceStateMachine()
            self.state_history[source_id] = []
            logger.debug(f"Created state machine for source {source_id}")
        
        return self.state_machines[source_id]
    
    def transition_source(
        self, 
        source_id: str, 
        event: SourceEvent, 
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Transition source state.
        
        Args:
            source_id: Source identifier
            event: Event that triggered transition
            data: Additional data for the transition
            
        Returns:
            True if transition was successful, False otherwise
        """
        state_machine = self.get_or_create_state_machine(source_id)
        
        if data is None:
            data = {}
        
        # Add source_id to data
        data["source_id"] = source_id
        
        # Perform transition
        success = state_machine.transition(event, data)
        
        if success:
            # Record in history
            self.state_history[source_id].append({
                "timestamp": datetime.now().isoformat(),
                "event": event.value,
                "state": state_machine.current_state.value,
                "data": data
            })
            
            # Check for auto-transitions
            self._check_auto_transitions(source_id)
        
        return success
    
    def get_source_state(self, source_id: str) -> Optional[SourceState]:
        """Get current state of source.
        
        Args:
            source_id: Source identifier
            
        Returns:
            Current state or None if not found
        """
        if source_id in self.state_machines:
            return self.state_machines[source_id].current_state
        return None
    
    def get_source_state_duration(self, source_id: str) -> Optional[float]:
        """Get duration in current state.
        
        Args:
            source_id: Source identifier
            
        Returns:
            Duration in seconds or None if not found
        """
        if source_id in self.state_machines:
            return self.state_machines[source_id].get_state_duration()
        return None
    
    def get_source_history(self, source_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get state history for source.
        
        Args:
            source_id: Source identifier
            limit: Maximum number of records to return
            
        Returns:
            List of state history records
        """
        if source_id not in self.state_history:
            return []
        
        history = self.state_history[source_id]
        if limit is None:
            return history.copy()
        return history[-limit:]
    
    def get_sources_by_state(self, state: SourceState) -> List[str]:
        """Get sources in specific state.
        
        Args:
            state: State to filter by
            
        Returns:
            List of source IDs in the state
        """
        sources = []
        for source_id, state_machine in self.state_machines.items():
            if state_machine.current_state == state:
                sources.append(source_id)
        return sources
    
    def get_state_statistics(self) -> Dict[str, Any]:
        """Get state statistics.
        
        Returns:
            State statistics
        """
        stats = {
            "total_sources": len(self.state_machines),
            "states": {},
            "transitions": 0
        }
        
        # Count sources by state
        for state in SourceState:
            sources = self.get_sources_by_state(state)
            stats["states"][state.value] = len(sources)
        
        # Count total transitions
        for history in self.state_history.values():
            stats["transitions"] += len(history)
        
        return stats
    
    def reset_source(self, source_id: str) -> bool:
        """Reset source state machine.
        
        Args:
            source_id: Source identifier
            
        Returns:
            True if reset successfully, False otherwise
        """
        if source_id in self.state_machines:
            self.state_machines[source_id].reset()
            self.state_history[source_id].clear()
            logger.info(f"Reset state machine for source {source_id}")
            return True
        return False
    
    def remove_source(self, source_id: str) -> bool:
        """Remove source state machine.
        
        Args:
            source_id: Source identifier
            
        Returns:
            True if removed successfully, False otherwise
        """
        if source_id in self.state_machines:
            del self.state_machines[source_id]
            del self.state_history[source_id]
            logger.info(f"Removed state machine for source {source_id}")
            return True
        return False
    
    def _check_auto_transitions(self, source_id: str) -> None:
        """Check for automatic transitions based on rules.
        
        Args:
            source_id: Source identifier
        """
        if source_id not in self.state_machines:
            return
        
        state_machine = self.state_machines[source_id]
        current_state = state_machine.current_state
        
        if current_state not in self.auto_transition_rules:
            return
        
        rules = self.auto_transition_rules[current_state]
        
        # Check duration-based transitions
        if "max_duration" in rules:
            duration = state_machine.get_state_duration()
            if duration > rules["max_duration"]:
                target_state = rules["transition_to"]
                self._force_transition(source_id, target_state, "auto_duration")
                return
        
        # Check failure-based transitions
        if "max_failures" in rules:
            failure_count = self._count_recent_failures(source_id)
            if failure_count >= rules["max_failures"]:
                target_state = rules["transition_to"]
                self._force_transition(source_id, target_state, "auto_failures")
                return
    
    def _force_transition(self, source_id: str, target_state: SourceState, reason: str) -> None:
        """Force transition to target state.
        
        Args:
            source_id: Source identifier
            target_state: Target state
            reason: Reason for forced transition
        """
        state_machine = self.state_machines[source_id]
        old_state = state_machine.current_state
        
        # Create a custom transition record
        transition_record = {
            "from_state": old_state.value,
            "to_state": target_state.value,
            "event": "force_transition",
            "timestamp": datetime.now().isoformat(),
            "data": {"reason": reason, "source_id": source_id}
        }
        
        state_machine.transition_history.append(transition_record)
        state_machine.current_state = target_state
        state_machine.state_entry_time = datetime.now()
        
        # Record in history
        self.state_history[source_id].append({
            "timestamp": datetime.now().isoformat(),
            "event": "force_transition",
            "state": target_state.value,
            "data": {"reason": reason}
        })
        
        logger.info(f"Forced transition for source {source_id}: {old_state.value} -> {target_state.value} ({reason})")
    
    def _count_recent_failures(self, source_id: str, minutes: int = 10) -> int:
        """Count recent failures for source.
        
        Args:
            source_id: Source identifier
            minutes: Time window in minutes
            
        Returns:
            Number of recent failures
        """
        if source_id not in self.state_history:
            return 0
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        failure_count = 0
        
        for record in self.state_history[source_id]:
            record_time = datetime.fromisoformat(record["timestamp"])
            if record_time > cutoff_time and record["event"] == "failure":
                failure_count += 1
        
        return failure_count
