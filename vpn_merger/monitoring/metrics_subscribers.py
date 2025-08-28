from __future__ import annotations

from typing import Any, Dict
from collections import deque
import time


def attach(bus, metrics) -> None:
    """Attach metrics subscribers to the EventBus.

    SOURCE_FETCHED -> record_source_processed + record_config_found per protocol
    TEST_COMPLETED -> record_connection_test
    BATCH_READY    -> set_active_configs
    """

    async def on_source_fetched(event):
        data: Dict[str, Any] = getattr(event, 'data', {}) or {}
        metrics.record_source_processed(True)
        protocol_counts: Dict[str, int] = dict(data.get('protocol_counts') or {})
        for proto, cnt in protocol_counts.items():
            # Source type unknown in this context
            for _ in range(int(cnt)):
                metrics.record_config_found(proto or 'Unknown', 'unknown')

    async def on_test_completed(event):
        data: Dict[str, Any] = getattr(event, 'data', {}) or {}
        success = bool(data.get('success', False))
        latency = data.get('latency')
        latency_val = float(latency) if isinstance(latency, (int, float)) else 0.0
        metrics.record_connection_test(latency_val, success)

    async def on_batch_ready(event):
        data: Dict[str, Any] = getattr(event, 'data', {}) or {}
        count = int(data.get('count', 0))
        metrics.set_active_configs(count)

    from vpn_merger.core.events import EventType  # type: ignore
    bus.subscribe(EventType.SOURCE_FETCHED, on_source_fetched)
    bus.subscribe(EventType.TEST_COMPLETED, on_test_completed)
    bus.subscribe(EventType.BATCH_READY, on_batch_ready)
    # Invalid host skips
    # Track sliding window for last minute rate
    _win = deque()

    async def on_invalid_host(event):
        metrics.record_invalid_host_skipped()
        now = time.time()
        _win.append(now)
        # prune older than 60s
        cutoff = now - 60.0
        while _win and _win[0] < cutoff:
            _win.popleft()
        metrics.set_invalid_hosts_rate(len(_win))
    bus.subscribe(EventType.INVALID_HOST_SKIPPED, on_invalid_host)
