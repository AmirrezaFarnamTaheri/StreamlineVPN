"""
Lightweight OpenTelemetry initialization with env-driven toggle.
Auto-instruments aiohttp client/server, SQLAlchemy, and Redis when enabled.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import TracerProvider

# Try to import OpenTelemetry components, but make them optional
try:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
    from opentelemetry.instrumentation.aiohttp_server import AioHttpServerInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

_meter = None


def init_observability(service_name: str = "vpn-merger") -> TracerProvider | None:
    if not OPENTELEMETRY_AVAILABLE:
        return None
        
    if os.getenv("OTEL_ENABLED", "false").lower() not in ("1", "true", "yes"):  # disabled
        return None

    endpoint = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # Metrics via OTLP
    metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
    reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)
    global _meter
    _meter = metrics.get_meter(service_name)

    # Auto-instrumentation
    AioHttpClientInstrumentor().instrument()
    AioHttpServerInstrumentor().instrument()
    try:
        SQLAlchemyInstrumentor().instrument()
    except Exception:
        pass
    try:
        RedisInstrumentor().instrument()
    except Exception:
        pass

    return provider


def get_meter_if_any():
    return _meter
