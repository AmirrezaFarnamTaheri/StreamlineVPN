#!/usr/bin/env python3
"""
Observer Pattern Implementation
===============================

Implements observer pattern for event handling and notifications
throughout the VPN merger application.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Set, Union
from dataclasses import dataclass
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Represents an event in the system."""
    
    id: str
    type: str
    data: Any
    timestamp: datetime
    source: str
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.metadata is None:
            self.metadata = {}


class EventHandler(ABC):
    """Abstract base class for event handlers."""
    
    def __init__(self, name: str):
        """Initialize the event handler.
        
        Args:
            name: Handler name
        """
        self.name = name
        self._enabled = True
        self._event_count = 0
        self._error_count = 0
    
    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle an event.
        
        Args:
            event: Event to handle
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if handler is enabled."""
        return self._enabled
    
    def enable(self) -> None:
        """Enable the handler."""
        self._enabled = True
        logger.debug(f"Enabled event handler: {self.name}")
    
    def disable(self) -> None:
        """Disable the handler."""
        self._enabled = False
        logger.debug(f"Disabled event handler: {self.name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            "name": self.name,
            "enabled": self._enabled,
            "event_count": self._event_count,
            "error_count": self._error_count,
            "success_rate": (self._event_count - self._error_count) / max(self._event_count, 1)
        }


class FunctionEventHandler(EventHandler):
    """Event handler that wraps a function."""
    
    def __init__(self, name: str, handler_func: Callable[[Event], Any]):
        """Initialize function event handler.
        
        Args:
            name: Handler name
            handler_func: Function to handle events
        """
        super().__init__(name)
        self.handler_func = handler_func
    
    async def handle(self, event: Event) -> None:
        """Handle an event using the wrapped function.
        
        Args:
            event: Event to handle
        """
        if not self._enabled:
            return
        
        try:
            self._event_count += 1
            
            # Check if function is async
            if asyncio.iscoroutinefunction(self.handler_func):
                await self.handler_func(event)
            else:
                self.handler_func(event)
                
        except Exception as e:
            self._error_count += 1
            logger.error(f"Error in event handler {self.name}: {e}")


class EventBus:
    """Central event bus for managing events and observers."""
    
    def __init__(self):
        """Initialize the event bus."""
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._metrics: Dict[str, Any] = {
            "total_events": 0,
            "events_by_type": {},
            "handler_errors": 0
        }
    
    def subscribe(self, event_type: str, handler: Union[EventHandler, Callable]) -> str:
        """Subscribe to events of a specific type.
        
        Args:
            event_type: Type of events to subscribe to
            handler: Event handler or function
            
        Returns:
            Handler ID for unsubscribing
        """
        if isinstance(handler, EventHandler):
            event_handler = handler
        else:
            # Create function handler
            handler_id = str(uuid.uuid4())
            event_handler = FunctionEventHandler(handler_id, handler)
        
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(event_handler)
        logger.debug(f"Subscribed handler {event_handler.name} to event type {event_type}")
        
        return event_handler.name
    
    def subscribe_global(self, handler: Union[EventHandler, Callable]) -> str:
        """Subscribe to all events.
        
        Args:
            handler: Event handler or function
            
        Returns:
            Handler ID for unsubscribing
        """
        if isinstance(handler, EventHandler):
            event_handler = handler
        else:
            # Create function handler
            handler_id = str(uuid.uuid4())
            event_handler = FunctionEventHandler(handler_id, handler)
        
        self._global_handlers.append(event_handler)
        logger.debug(f"Subscribed global handler {event_handler.name}")
        
        return event_handler.name
    
    def unsubscribe(self, event_type: str, handler_name: str) -> bool:
        """Unsubscribe a handler from specific event type.
        
        Args:
            event_type: Event type
            handler_name: Handler name
            
        Returns:
            True if handler was unsubscribed
        """
        if event_type in self._handlers:
            handlers = self._handlers[event_type]
            for i, handler in enumerate(handlers):
                if handler.name == handler_name:
                    del handlers[i]
                    logger.debug(f"Unsubscribed handler {handler_name} from event type {event_type}")
                    return True
        return False
    
    def unsubscribe_global(self, handler_name: str) -> bool:
        """Unsubscribe a global handler.
        
        Args:
            handler_name: Handler name
            
        Returns:
            True if handler was unsubscribed
        """
        for i, handler in enumerate(self._global_handlers):
            if handler.name == handler_name:
                del self._global_handlers[i]
                logger.debug(f"Unsubscribed global handler {handler_name}")
                return True
        return False
    
    async def publish(self, event_type: str, data: Any, source: str = "unknown", metadata: Optional[Dict[str, Any]] = None) -> None:
        """Publish an event.
        
        Args:
            event_type: Type of event
            data: Event data
            source: Event source
            metadata: Additional metadata
        """
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            data=data,
            timestamp=datetime.now(),
            source=source,
            metadata=metadata or {}
        )
        
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Update metrics
        self._metrics["total_events"] += 1
        if event_type not in self._metrics["events_by_type"]:
            self._metrics["events_by_type"][event_type] = 0
        self._metrics["events_by_type"][event_type] += 1
        
        # Notify handlers
        await self._notify_handlers(event)
        
        logger.debug(f"Published event {event_type} from {source}")
    
    async def _notify_handlers(self, event: Event) -> None:
        """Notify all relevant handlers of an event.
        
        Args:
            event: Event to notify handlers about
        """
        # Notify type-specific handlers
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                if handler.is_enabled():
                    try:
                        await handler.handle(event)
                    except Exception as e:
                        self._metrics["handler_errors"] += 1
                        logger.error(f"Error in event handler {handler.name}: {e}")
        
        # Notify global handlers
        for handler in self._global_handlers:
            if handler.is_enabled():
                try:
                    await handler.handle(event)
                except Exception as e:
                    self._metrics["handler_errors"] += 1
                    logger.error(f"Error in global event handler {handler.name}: {e}")
    
    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Event]:
        """Get event history.
        
        Args:
            event_type: Filter by event type (None for all)
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        events = self._event_history
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        return events[-limit:] if limit > 0 else events
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics."""
        metrics = self._metrics.copy()
        
        # Add handler statistics
        metrics["handlers"] = {}
        for event_type, handlers in self._handlers.items():
            metrics["handlers"][event_type] = [handler.get_stats() for handler in handlers]
        
        metrics["global_handlers"] = [handler.get_stats() for handler in self._global_handlers]
        
        return metrics
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
        logger.debug("Cleared event history")
    
    def reset_metrics(self) -> None:
        """Reset metrics."""
        self._metrics = {
            "total_events": 0,
            "events_by_type": {},
            "handler_errors": 0
        }
        logger.debug("Reset event bus metrics")


class LoggingEventHandler(EventHandler):
    """Event handler that logs events."""
    
    def __init__(self, name: str = "logging", log_level: int = logging.INFO):
        """Initialize logging event handler.
        
        Args:
            name: Handler name
            log_level: Logging level
        """
        super().__init__(name)
        self.log_level = log_level
        self.logger = logging.getLogger(f"event.{name}")
    
    async def handle(self, event: Event) -> None:
        """Log the event.
        
        Args:
            event: Event to log
        """
        self._event_count += 1
        
        message = f"Event {event.type} from {event.source}: {event.data}"
        self.logger.log(self.log_level, message)


class MetricsEventHandler(EventHandler):
    """Event handler that collects metrics."""
    
    def __init__(self, name: str = "metrics"):
        """Initialize metrics event handler.
        
        Args:
            name: Handler name
        """
        super().__init__(name)
        self._metrics: Dict[str, Any] = {
            "events_processed": 0,
            "events_by_type": {},
            "events_by_source": {},
            "last_event_time": None
        }
    
    async def handle(self, event: Event) -> None:
        """Collect metrics from the event.
        
        Args:
            event: Event to process
        """
        self._event_count += 1
        
        # Update metrics
        self._metrics["events_processed"] += 1
        self._metrics["last_event_time"] = event.timestamp
        
        # Count by type
        if event.type not in self._metrics["events_by_type"]:
            self._metrics["events_by_type"][event.type] = 0
        self._metrics["events_by_type"][event.type] += 1
        
        # Count by source
        if event.source not in self._metrics["events_by_source"]:
            self._metrics["events_by_source"][event.source] = 0
        self._metrics["events_by_source"][event.source] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        return self._metrics.copy()


class NotificationEventHandler(EventHandler):
    """Event handler that sends notifications."""
    
    def __init__(self, name: str = "notifications", notification_service: Optional[Any] = None):
        """Initialize notification event handler.
        
        Args:
            name: Handler name
            notification_service: Notification service to use
        """
        super().__init__(name)
        self.notification_service = notification_service
        self.notification_types: Set[str] = {"error", "warning", "info"}
    
    async def handle(self, event: Event) -> None:
        """Send notification for the event.
        
        Args:
            event: Event to process
        """
        self._event_count += 1
        
        # Check if this event type should trigger notifications
        event_type = event.metadata.get("notification_type", "info")
        if event_type not in self.notification_types:
            return
        
        if self.notification_service:
            try:
                await self.notification_service.send_notification(
                    message=f"Event {event.type}: {event.data}",
                    notification_type=event_type,
                    metadata=event.metadata
                )
            except Exception as e:
                self._error_count += 1
                logger.error(f"Failed to send notification: {e}")


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus.
    
    Returns:
        Global EventBus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
        
        # Add default handlers
        _event_bus.subscribe_global(LoggingEventHandler())
        _event_bus.subscribe_global(MetricsEventHandler())
    
    return _event_bus


def reset_event_bus() -> None:
    """Reset the global event bus."""
    global _event_bus
    if _event_bus:
        _event_bus.clear_history()
        _event_bus.reset_metrics()
    _event_bus = None
