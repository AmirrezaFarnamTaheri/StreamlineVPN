from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from contextlib import asynccontextmanager


class TracingService:
    """Enhanced distributed tracing via OTLP exporter."""

    def __init__(self, service_name: str = "vpn_merger", endpoint: str = "localhost:4317"):
        provider = TracerProvider()
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer(service_name)
        try:
            AioHttpClientInstrumentor().instrument()
        except Exception:
            pass

    @asynccontextmanager
    async def trace(self, operation: str, attributes: dict | None = None):
        with self.tracer.start_as_current_span(operation) as span:
            if attributes:
                for k, v in attributes.items():
                    try:
                        span.set_attribute(k, v)
                    except Exception:
                        pass
            try:
                yield span
            except Exception as e:
                try:
                    span.record_exception(e)
                except Exception:
                    pass
                raise

    def trace_method(self, func):
        async def wrapper(*args, **kwargs):
            op = f"{func.__module__}.{func.__name__}"
            async with self.trace(op):
                return await func(*args, **kwargs)
        return wrapper

