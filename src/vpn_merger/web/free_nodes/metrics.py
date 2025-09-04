from __future__ import annotations

try:
    from prometheus_client import Counter, Gauge, Histogram
    from prometheus_fastapi_instrumentator import Instrumentator
except Exception:  # pragma: no cover

    class _Noop:
        def __getattr__(self, *_):
            return self

        def __call__(self, *a, **k):
            return self

    Instrumentator = _Noop()  # type: ignore

    class Counter:  # type: ignore
        def __init__(self, *a, **k):
            pass

        def labels(self, *a, **k):
            return self

        def inc(self, *a, **k):
            pass

    class Histogram:  # type: ignore
        def __init__(self, *a, **k):
            pass

        def labels(self, *a, **k):
            return self

        def observe(self, *a, **k):
            pass

    class Gauge:  # type: ignore
        def __init__(self, *a, **k):
            pass

        def labels(self, *a, **k):
            return self

        def set(self, *a, **k):
            pass


NODES_PROCESSED = Counter(
    "nodes_processed_total",
    "Total nodes parsed/merged by background workers",
    labelnames=("source", "result"),
)

FETCH_DURATION = Histogram(
    "node_fetch_duration_seconds",
    "Duration of source fetch and parse",
    labelnames=("source",),
    buckets=(0.1, 0.3, 0.5, 1, 2, 5, 10),
)

QUALITY_SCORE = Gauge(
    "node_quality_score",
    "Latest quality score for a node",
    labelnames=("proto", "region"),
)


