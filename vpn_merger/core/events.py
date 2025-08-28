from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable, Dict, List
import asyncio


class EventType(Enum):
    SOURCE_FETCHED = "source_fetched"
    CONFIG_PARSED = "config_parsed"
    TEST_COMPLETED = "test_completed"
    BATCH_READY = "batch_ready"
    ERROR_OCCURRED = "error_occurred"
    INVALID_HOST_SKIPPED = "invalid_host_skipped"


@dataclass
class Event:
    type: EventType
    data: Any
    timestamp: float
    source: str = ""


class EventBus:
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._running = False

    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: Event) -> None:
        await self._queue.put(event)

    async def start(self) -> None:
        self._running = True
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._process_event(event)
            except asyncio.TimeoutError:
                continue

    async def _process_event(self, event: Event) -> None:
        for handler in self._handlers.get(event.type, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception:
                # best-effort; continue processing
                pass
