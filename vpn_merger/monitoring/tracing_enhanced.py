from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.aiohttp import AioHttpClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from contextlib import asynccontextmanager, contextmanager
from typing import Dict, Any, Optional, Union
import logging
import os
import time
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

class TracingService:
    """Enhanced distributed tracing service using OpenTelemetry."""
    
    def __init__(self, service_name: str = "vpn_merger", 
                 service_version: str = "2.0.0",
                 environment: str = "development",
                 otlp_endpoint: Optional[str] = None):
        
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.otlp_endpoint = otlp_endpoint or os.getenv("OTLP_ENDPOINT", "localhost:4317")
        
        # Initialize tracing
        self._setup_tracing()
        
        # Auto-instrument libraries
        self._setup_instrumentation()
        
        logger.info(f"Tracing service initialized for {service_name} v{service_version}")
    
    def _setup_tracing(self):
        """Setup OpenTelemetry tracing."""
        try:
            # Create tracer provider
            provider = TracerProvider()
            
            # Add span processors
            if self.environment == "development":
                # Console exporter for development
                console_exporter = ConsoleSpanExporter()
                provider.add_span_processor(BatchSpanProcessor(console_exporter))
            
            # OTLP exporter for production
            try:
                otlp_exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint)
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            except Exception as e:
                logger.warning(f"Could not setup OTLP exporter: {e}")
            
            # Set global tracer provider
            trace.set_tracer_provider(provider)
            
            # Get tracer
            self.tracer = trace.get_tracer(self.service_name, self.service_version)
            
        except Exception as e:
            logger.error(f"Failed to setup tracing: {e}")
            # Fallback to no-op tracer
            self.tracer = trace.get_tracer(__name__)
    
    def _setup_instrumentation(self):
        """Setup automatic instrumentation for common libraries."""
        try:
            # HTTP client instrumentation
            AioHttpClientInstrumentor().instrument()
            
            # Logging instrumentation
            LoggingInstrumentor().instrument()
            
            # Database instrumentation (if available)
            try:
                Psycopg2Instrumentor().instrument()
            except ImportError:
                logger.debug("psycopg2 not available, skipping instrumentation")
            
            # Redis instrumentation (if available)
            try:
                RedisInstrumentor().instrument()
            except ImportError:
                logger.debug("redis not available, skipping instrumentation")
                
        except Exception as e:
            logger.warning(f"Could not setup all instrumentation: {e}")
    
    @asynccontextmanager
    async def trace(self, operation: str, attributes: Optional[Dict[str, Any]] = None):
        """Trace an async operation."""
        with self.tracer.start_as_current_span(operation) as span:
            # Set default attributes
            span.set_attribute("service.name", self.service_name)
            span.set_attribute("service.version", self.service_version)
            span.set_attribute("environment", self.environment)
            
            # Set custom attributes
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
            finally:
                span.set_status(trace.Status(trace.StatusCode.OK))
    
    @contextmanager
    def trace_sync(self, operation: str, attributes: Optional[Dict[str, Any]] = None):
        """Trace a synchronous operation."""
        with self.tracer.start_as_current_span(operation) as span:
            # Set default attributes
            span.set_attribute("service.name", self.service_name)
            span.set_attribute("service.version", self.service_version)
            span.set_attribute("environment", self.environment)
            
            # Set custom attributes
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
            finally:
                span.set_status(trace.Status(trace.StatusCode.OK))
    
    def trace_method(self, operation: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
        """Decorator for tracing methods."""
        def decorator(func):
            op_name = operation or f"{func.__module__}.{func.__name__}"
            
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    async with self.trace(op_name, attributes):
                        return await func(*args, **kwargs)
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    with self.trace_sync(op_name, attributes):
                        return func(*args, **kwargs)
                return sync_wrapper
        
        return decorator
    
    def trace_class_methods(self, cls, exclude_methods: Optional[list] = None):
        """Decorator to trace all methods of a class."""
        exclude_methods = exclude_methods or ['__init__', '__del__', '__repr__']
        
        for method_name in dir(cls):
            if (method_name.startswith('_') or 
                method_name in exclude_methods or
                not callable(getattr(cls, method_name))):
                continue
            
            method = getattr(cls, method_name)
            if asyncio.iscoroutinefunction(method):
                setattr(cls, method_name, self.trace_method(f"{cls.__name__}.{method_name}")(method))
            else:
                setattr(cls, method_name, self.trace_method(f"{cls.__name__}.{method_name}")(method))
        
        return cls
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add an event to the current span."""
        current_span = trace.get_current_span()
        if current_span.is_recording():
            current_span.add_event(name, attributes or {})
    
    def set_attribute(self, key: str, value: Any):
        """Set an attribute on the current span."""
        current_span = trace.get_current_span()
        if current_span.is_recording():
            current_span.set_attribute(key, value)
    
    def record_exception(self, exception: Exception, attributes: Optional[Dict[str, Any]] = None):
        """Record an exception on the current span."""
        current_span = trace.get_current_span()
        if current_span.is_recording():
            current_span.record_exception(exception, attributes or {})
    
    def get_trace_id(self) -> Optional[str]:
        """Get the current trace ID."""
        current_span = trace.get_current_span()
        if current_span.is_recording():
            return current_span.get_span_context().trace_id
        return None
    
    def get_span_id(self) -> Optional[str]:
        """Get the current span ID."""
        current_span = trace.get_current_span()
        if current_span.is_recording():
            return current_span.get_span_context().span_id
        return None

class PerformanceTracer:
    """Specialized tracer for performance monitoring."""
    
    def __init__(self, tracing_service: TracingService):
        self.tracing = tracing_service
    
    @asynccontextmanager
    async def trace_operation(self, operation: str, **attributes):
        """Trace an operation with performance metrics."""
        start_time = time.time()
        
        async with self.tracing.trace(operation, attributes) as span:
            try:
                yield span
            finally:
                duration = time.time() - start_time
                span.set_attribute("operation.duration", duration)
                
                # Add performance attributes
                span.set_attribute("operation.start_time", start_time)
                span.set_attribute("operation.end_time", time.time())
    
    def trace_function_call(self, func_name: str, **attributes):
        """Decorator to trace function calls with performance metrics."""
        def decorator(func):
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    start_time = time.time()
                    
                    with self.tracing.trace_sync(f"function.{func_name}", attributes) as span:
                        try:
                            result = await func(*args, **kwargs)
                            return result
                        finally:
                            duration = time.time() - start_time
                            span.set_attribute("function.duration", duration)
                            span.set_attribute("function.start_time", start_time)
                            span.set_attribute("function.end_time", time.time())
                
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    start_time = time.time()
                    
                    with self.tracing.trace_sync(f"function.{func_name}", attributes) as span:
                        try:
                            result = func(*args, **kwargs)
                            return result
                        finally:
                            duration = time.time() - start_time
                            span.set_attribute("function.duration", duration)
                            span.set_attribute("function.start_time", start_time)
                            span.set_attribute("function.end_time", time.time())
                
                return sync_wrapper
        
        return decorator

class DatabaseTracer:
    """Specialized tracer for database operations."""
    
    def __init__(self, tracing_service: TracingService):
        self.tracing = tracing_service
    
    @asynccontextmanager
    async def trace_query(self, query: str, params: Optional[Dict] = None, **attributes):
        """Trace a database query."""
        query_attributes = {
            "db.operation": "query",
            "db.statement": query,
            "db.parameters": str(params) if params else None,
            **attributes
        }
        
        async with self.tracing.trace("database.query", query_attributes) as span:
            start_time = time.time()
            try:
                yield span
            finally:
                duration = time.time() - start_time
                span.set_attribute("db.duration", duration)
    
    @asynccontextmanager
    async def trace_transaction(self, **attributes):
        """Trace a database transaction."""
        tx_attributes = {
            "db.operation": "transaction",
            **attributes
        }
        
        async with self.tracing.trace("database.transaction", tx_attributes) as span:
            start_time = time.time()
            try:
                yield span
            finally:
                duration = time.time() - start_time
                span.set_attribute("db.duration", duration)

class HTTPTracer:
    """Specialized tracer for HTTP operations."""
    
    def __init__(self, tracing_service: TracingService):
        self.tracing = tracing_service
    
    @asynccontextmanager
    async def trace_request(self, method: str, url: str, **attributes):
        """Trace an HTTP request."""
        request_attributes = {
            "http.method": method,
            "http.url": url,
            "http.scheme": "https" if url.startswith("https://") else "http",
            **attributes
        }
        
        async with self.tracing.trace("http.request", request_attributes) as span:
            start_time = time.time()
            try:
                yield span
            finally:
                duration = time.time() - start_time
                span.set_attribute("http.duration", duration)
    
    @asynccontextmanager
    async def trace_response(self, status_code: int, **attributes):
        """Trace an HTTP response."""
        response_attributes = {
            "http.status_code": status_code,
            "http.status_class": f"{status_code // 100}xx",
            **attributes
        }
        
        async with self.tracing.trace("http.response", response_attributes) as span:
            yield span

class CacheTracer:
    """Specialized tracer for cache operations."""
    
    def __init__(self, tracing_service: TracingService):
        self.tracing = tracing_service
    
    @asynccontextmanager
    async def trace_cache_operation(self, operation: str, key: str, cache_tier: str = "l1", **attributes):
        """Trace a cache operation."""
        cache_attributes = {
            "cache.operation": operation,
            "cache.key": key,
            "cache.tier": cache_tier,
            **attributes
        }
        
        async with self.tracing.trace("cache.operation", cache_attributes) as span:
            start_time = time.time()
            try:
                yield span
            finally:
                duration = time.time() - start_time
                span.set_attribute("cache.duration", duration)

# Global tracing service instance
_tracing_service: Optional[TracingService] = None

def get_tracing_service() -> TracingService:
    """Get the global tracing service instance."""
    global _tracing_service
    if _tracing_service is None:
        _tracing_service = TracingService()
    return _tracing_service

def trace(operation: str, attributes: Optional[Dict[str, Any]] = None):
    """Trace an operation using the global tracing service."""
    return get_tracing_service().trace(operation, attributes)

def trace_sync(operation: str, attributes: Optional[Dict[str, Any]] = None):
    """Trace a synchronous operation using the global tracing service."""
    return get_tracing_service().trace_sync(operation, attributes)

def trace_method(operation: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """Trace a method using the global tracing service."""
    return get_tracing_service().trace_method(operation, attributes)

# Convenience functions for common tracing patterns
async def trace_source_fetch(source_url: str, **attributes):
    """Trace a source fetch operation."""
    async with trace("source.fetch", {"source.url": source_url, **attributes}):
        pass

async def trace_config_processing(protocol: str, config_count: int, **attributes):
    """Trace config processing operation."""
    async with trace("config.processing", {
        "config.protocol": protocol,
        "config.count": config_count,
        **attributes
    }):
        pass

async def trace_output_generation(format: str, config_count: int, **attributes):
    """Trace output generation operation."""
    async with trace("output.generation", {
        "output.format": format,
        "output.config_count": config_count,
        **attributes
    }):
        pass

