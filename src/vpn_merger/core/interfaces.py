#!/usr/bin/env python3
"""
Interface Abstractions for VPN Merger
=====================================

Defines clear interfaces and abstractions for all major components
to enable loose coupling and better testability.
"""

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ..models.configuration import VPNConfiguration


@runtime_checkable
class SourceManagerInterface(Protocol):
    """Interface for source management components."""
    
    def get_all_sources(self) -> List[str]:
        """Get all available sources."""
        ...
    
    def get_prioritized_sources(self) -> List[str]:
        """Get prioritized sources."""
        ...
    
    def add_custom_sources(self, sources: List[str]) -> None:
        """Add custom sources."""
        ...
    
    def remove_sources(self, sources: List[str]) -> None:
        """Remove sources."""
        ...
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get source statistics."""
        ...


@runtime_checkable
class SourceProcessorInterface(Protocol):
    """Interface for source processing components."""
    
    async def process_sources_batch(
        self, 
        sources: List[str], 
        batch_size: int = 10, 
        max_concurrent: int = 50
    ) -> List[VPNConfiguration]:
        """Process sources in batches."""
        ...
    
    async def validate_sources(self, sources: List[str]) -> Dict[str, Dict[str, Any]]:
        """Validate sources."""
        ...
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        ...
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get processing summary."""
        ...
    
    def reset_statistics(self) -> None:
        """Reset processing statistics."""
        ...


@runtime_checkable
class OutputManagerInterface(Protocol):
    """Interface for output management components."""
    
    def save_results(
        self, 
        results: List[VPNConfiguration], 
        output_dir: Optional[Path] = None
    ) -> Dict[str, str]:
        """Save results to various formats."""
        ...
    
    def get_supported_formats(self) -> List[str]:
        """Get supported output formats."""
        ...


@runtime_checkable
class ConfigurationProcessorInterface(Protocol):
    """Interface for configuration processing components."""
    
    def process_configuration(self, config_data: str) -> List[VPNConfiguration]:
        """Process configuration data."""
        ...
    
    def validate_configuration(self, config: VPNConfiguration) -> bool:
        """Validate a configuration."""
        ...


class ServiceInterface(ABC):
    """Base interface for all services."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the service."""
        pass
    
    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if the service is healthy."""
        pass


class CacheInterface(ABC):
    """Interface for caching components."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass


class EventBusInterface(ABC):
    """Interface for event bus components."""
    
    @abstractmethod
    async def publish(self, event_type: str, data: Any) -> None:
        """Publish an event."""
        pass
    
    @abstractmethod
    async def subscribe(self, event_type: str, handler: callable) -> None:
        """Subscribe to an event."""
        pass
    
    @abstractmethod
    async def unsubscribe(self, event_type: str, handler: callable) -> None:
        """Unsubscribe from an event."""
        pass


class MetricsInterface(ABC):
    """Interface for metrics collection."""
    
    @abstractmethod
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        pass
    
    @abstractmethod
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a gauge metric."""
        pass
    
    @abstractmethod
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram metric."""
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        pass


class SecurityValidatorInterface(ABC):
    """Interface for security validation components."""
    
    @abstractmethod
    async def validate_input(self, input_data: str) -> bool:
        """Validate input for security threats."""
        pass
    
    @abstractmethod
    async def validate_path(self, path: str) -> bool:
        """Validate file path for security."""
        pass
    
    @abstractmethod
    async def validate_url(self, url: str) -> bool:
        """Validate URL for security."""
        pass


class DiscoveryInterface(ABC):
    """Interface for source discovery components."""
    
    @abstractmethod
    async def discover_sources(self) -> List[str]:
        """Discover new sources."""
        pass
    
    @abstractmethod
    async def monitor_sources(self) -> None:
        """Monitor sources for changes."""
        pass
    
    @abstractmethod
    def get_discovered_sources(self) -> List[str]:
        """Get discovered sources."""
        pass


class QualityPredictorInterface(ABC):
    """Interface for quality prediction components."""
    
    @abstractmethod
    async def predict_quality(self, config: VPNConfiguration) -> float:
        """Predict configuration quality."""
        pass
    
    @abstractmethod
    async def train_model(self, training_data: List[VPNConfiguration]) -> None:
        """Train the quality prediction model."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        pass


class GeographicOptimizerInterface(ABC):
    """Interface for geographic optimization components."""
    
    @abstractmethod
    async def optimize_by_location(
        self, 
        configs: List[VPNConfiguration], 
        target_location: str
    ) -> List[VPNConfiguration]:
        """Optimize configurations by geographic location."""
        pass
    
    @abstractmethod
    async def get_server_locations(self, configs: List[VPNConfiguration]) -> Dict[str, List[str]]:
        """Get server locations for configurations."""
        pass


class AnalyticsInterface(ABC):
    """Interface for analytics components."""
    
    @abstractmethod
    async def track_event(self, event_name: str, data: Dict[str, Any]) -> None:
        """Track an analytics event."""
        pass
    
    @abstractmethod
    async def get_analytics_data(self, time_range: str) -> Dict[str, Any]:
        """Get analytics data for a time range."""
        pass
    
    @abstractmethod
    async def generate_report(self, report_type: str) -> Dict[str, Any]:
        """Generate an analytics report."""
        pass


class NotificationInterface(ABC):
    """Interface for notification components."""
    
    @abstractmethod
    async def send_notification(
        self, 
        message: str, 
        recipients: List[str], 
        notification_type: str = "info"
    ) -> None:
        """Send a notification."""
        pass
    
    @abstractmethod
    async def send_alert(self, alert_type: str, data: Dict[str, Any]) -> None:
        """Send an alert."""
        pass


class DatabaseInterface(ABC):
    """Interface for database components."""
    
    @abstractmethod
    async def save_configuration(self, config: VPNConfiguration) -> None:
        """Save a configuration to database."""
        pass
    
    @abstractmethod
    async def get_configurations(self, filters: Optional[Dict[str, Any]] = None) -> List[VPNConfiguration]:
        """Get configurations from database."""
        pass
    
    @abstractmethod
    async def delete_configuration(self, config_id: str) -> None:
        """Delete a configuration from database."""
        pass
    
    @abstractmethod
    async def update_configuration(self, config: VPNConfiguration) -> None:
        """Update a configuration in database."""
        pass


class ConfigurationManagerInterface(ABC):
    """Interface for configuration management components."""
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass
    
    @abstractmethod
    def load_config(self, config_path: Path) -> None:
        """Load configuration from file."""
        pass
    
    @abstractmethod
    def save_config(self, config_path: Path) -> None:
        """Save configuration to file."""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate current configuration."""
        pass


class PluginInterface(ABC):
    """Interface for plugin components."""
    
    @abstractmethod
    def get_name(self) -> str:
        """Get plugin name."""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Get plugin version."""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin."""
        pass
    
    @abstractmethod
    async def execute(self, data: Any) -> Any:
        """Execute plugin functionality."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass


class MiddlewareInterface(ABC):
    """Interface for middleware components."""
    
    @abstractmethod
    async def process_request(self, request: Any) -> Any:
        """Process incoming request."""
        pass
    
    @abstractmethod
    async def process_response(self, response: Any) -> Any:
        """Process outgoing response."""
        pass
    
    @abstractmethod
    async def handle_error(self, error: Exception) -> Any:
        """Handle errors."""
        pass


class HealthCheckInterface(ABC):
    """Interface for health check components."""
    
    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Perform health check."""
        pass
    
    @abstractmethod
    def get_health_status(self) -> str:
        """Get current health status."""
        pass
    
    @abstractmethod
    def register_health_check(self, name: str, check_func: callable) -> None:
        """Register a health check function."""
        pass


class RateLimiterInterface(ABC):
    """Interface for rate limiting components."""
    
    @abstractmethod
    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed under rate limit."""
        pass
    
    @abstractmethod
    async def get_remaining(self, key: str, limit: int, window: int) -> int:
        """Get remaining requests for a key."""
        pass
    
    @abstractmethod
    async def reset_limit(self, key: str) -> None:
        """Reset rate limit for a key."""
        pass


class CircuitBreakerInterface(ABC):
    """Interface for circuit breaker components."""
    
    @abstractmethod
    async def call(self, func: callable, *args, **kwargs) -> Any:
        """Call function through circuit breaker."""
        pass
    
    @abstractmethod
    def get_state(self) -> str:
        """Get circuit breaker state."""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset circuit breaker."""
        pass


class RetryInterface(ABC):
    """Interface for retry components."""
    
    @abstractmethod
    async def execute_with_retry(
        self, 
        func: callable, 
        max_attempts: int = 3, 
        delay: float = 1.0,
        backoff_factor: float = 2.0
    ) -> Any:
        """Execute function with retry logic."""
        pass
    
    @abstractmethod
    def should_retry(self, exception: Exception) -> bool:
        """Check if exception should trigger retry."""
        pass
