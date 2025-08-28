from __future__ import annotations

import asyncio
import time
from typing import Any, Deque, Dict, List, Optional
from collections import deque

try:
    from vpn_merger.core.events import Event, EventBus, EventType  # type: ignore
except Exception:  # pragma: no cover
    Event = object  # type: ignore
    EventBus = object  # type: ignore
    class EventType:  # type: ignore
        SOURCE_FETCHED = "source_fetched"
        BATCH_READY = "batch_ready"
        ERROR_OCCURRED = "error_occurred"


class DashboardEventSubscriber:
    """Aggregates EventBus events into dashboard-friendly stats and broadcasts."""

    def __init__(self, dashboard_manager, total_sources: int = 0, min_interval: float = 0.5):
        self.dashboard_manager = dashboard_manager
        self.total_sources = total_sources
        self.active_sources = 0
        self.total_configs = 0
        self.valid_configs = 0
        self.current_phase = "idle"
        self.start_time = time.time()
        self.recent_configs: Deque[Dict[str, Any]] = deque(maxlen=20)
        self._sources_seen: set[str] = set()
        self._last_broadcast: float = 0.0
        self._min_interval: float = float(min_interval)
        self.invalid_hosts: int = 0

    def set_total_sources(self, n: int) -> None:
        self.total_sources = int(n)

    async def on_source_fetched(self, event: Event) -> None:
        data = getattr(event, 'data', {}) or {}
        url = str(data.get('url', ''))
        count = int(data.get('count', 0))
        reachable = int(data.get('reachable', 0))
        samples = data.get('samples') or []
        if url and url not in self._sources_seen:
            self._sources_seen.add(url)
            if count > 0:
                self.active_sources += 1
        self.total_configs += count
        self.valid_configs += reachable
        self.current_phase = "fetching"
        for s in samples[-5:]:
            # Normalize to expected keys in the UI
            self.recent_configs.append({
                'protocol': s.get('protocol', ''),
                'host': s.get('host', ''),
                'port': s.get('port', None),
                'ping_ms': s.get('ping_ms', None),
            })
        await self._broadcast()

    async def on_batch_ready(self, event: Event) -> None:
        self.current_phase = "writing"
        await self._broadcast(force=True)

    async def on_error(self, event: Event) -> None:
        # Could be used to increment error counters or include in payload
        await self._broadcast()

    async def on_invalid_host(self, event: Event) -> None:
        self.invalid_hosts += 1
        await self._broadcast()

    def _processing_speed(self) -> float:
        elapsed = max(0.001, time.time() - self.start_time)
        return float(self.total_configs) / elapsed

    async def _broadcast(self, force: bool = False) -> None:
        if not self.dashboard_manager:
            return
        now = time.time()
        if not force and (now - self._last_broadcast) < self._min_interval:
            return
        payload = {
            'total_sources': self.total_sources,
            'active_sources': self.active_sources,
            'total_configs': self.total_configs,
            'valid_configs': self.valid_configs,
            'invalid_hosts': self.invalid_hosts,
            'processing_speed': self._processing_speed(),
            'current_phase': self.current_phase,
            'errors': [],
            'recent_configs': list(self.recent_configs)[-10:],
        }
        try:
            await self.dashboard_manager.broadcast_status(payload)
            self._last_broadcast = now
        except Exception:
            pass


def attach(bus: EventBus, dashboard_manager, total_sources: int = 0) -> DashboardEventSubscriber:
    """Attach dashboard subscribers to the provided EventBus and return aggregator instance."""
    agg = DashboardEventSubscriber(dashboard_manager, total_sources)
    bus.subscribe(EventType.SOURCE_FETCHED, agg.on_source_fetched)
    bus.subscribe(EventType.BATCH_READY, agg.on_batch_ready)
    bus.subscribe(EventType.ERROR_OCCURRED, agg.on_error)
    bus.subscribe(EventType.INVALID_HOST_SKIPPED, agg.on_invalid_host)
    return agg
