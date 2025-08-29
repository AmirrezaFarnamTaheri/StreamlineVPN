from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Iterator, Optional


@contextmanager
def tracer_span(name: str, attributes: Optional[Dict[str, object]] = None) -> Iterator[None]:
    """Start a tracing span if OpenTelemetry is available; else no-op."""
    try:
        from opentelemetry import trace  # type: ignore
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(name) as span:  # type: ignore
            if attributes:
                try:
                    for k, v in attributes.items():
                        span.set_attribute(k, v)  # type: ignore[attr-defined]
                except Exception:
                    pass
            yield
            return
    except Exception:
        pass
    # fallback
    yield

