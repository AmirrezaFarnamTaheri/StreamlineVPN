"""
Core VPN Merger Components
=========================

Core functionality for VPN configuration processing, merging, and management.
"""

from .config_manager import ConfigurationManager, get_config_manager, reset_config_manager
from .config_processor import ConfigurationProcessor
from .validation import ConfigurationValidator, ValidationResult, ValidationError
from .di_container import DIContainer, get_container, reset_container
from .config_manager_enhanced import EnhancedConfigurationManager, EnhancedConfig, get_enhanced_config_manager, reset_enhanced_config_manager
from .enhanced_registry import EnhancedComponentRegistry, get_enhanced_registry, reset_enhanced_registry
from .enhanced_source_validator import EnhancedSourceValidator
from .factory import VPNMergerFactory, ComponentRegistry, get_registry, reset_registry
from .interfaces import (
    SourceManagerInterface,
    SourceProcessorInterface,
    OutputManagerInterface,
    ConfigurationProcessorInterface,
    ServiceInterface,
    CacheInterface,
    EventBusInterface,
    MetricsInterface,
    SecurityValidatorInterface,
    DiscoveryInterface,
    QualityPredictorInterface,
    GeographicOptimizerInterface,
    AnalyticsInterface,
    NotificationInterface,
    DatabaseInterface,
    ConfigurationManagerInterface,
    PluginInterface,
    MiddlewareInterface,
    HealthCheckInterface,
    RateLimiterInterface,
    CircuitBreakerInterface,
    RetryInterface
)
from .merger import VPNSubscriptionMerger
from .observers import (
    Event,
    EventHandler,
    FunctionEventHandler,
    EventBus,
    LoggingEventHandler,
    MetricsEventHandler,
    NotificationEventHandler,
    get_event_bus,
    reset_event_bus
)
from .output import OutputManager
from .source_manager import SourceManager
from .source_processor import SourceProcessor
from .source_validator import UnifiedSourceValidator
from .strategies import (
    BaseProcessingStrategy,
    QualityBasedProcessingStrategy,
    GeographicProcessingStrategy,
    PerformanceProcessingStrategy,
    BaseValidationStrategy,
    ProtocolValidationStrategy,
    SecurityValidationStrategy,
    StrategyManager,
    get_strategy_manager,
    reset_strategy_manager
)

__all__ = [
    # Configuration Management
    "ConfigurationManager",
    "get_config_manager",
    "reset_config_manager",
    "ConfigurationProcessor",
    "ConfigurationValidator",
    "ValidationResult",
    "ValidationError",
    "EnhancedConfigurationManager",
    "EnhancedConfig",
    "get_enhanced_config_manager",
    "reset_enhanced_config_manager",
    "EnhancedSourceValidator",
    
    # Core Components
    "OutputManager",
    "SourceManager",
    "SourceProcessor",
    "UnifiedSourceValidator",
    "VPNSubscriptionMerger",
    
    # Architecture Components
    "DIContainer",
    "get_container",
    "reset_container",
    "VPNMergerFactory",
    "ComponentRegistry",
    "get_registry",
    "reset_registry",
    "EnhancedComponentRegistry",
    "get_enhanced_registry",
    "reset_enhanced_registry",
    
    # Interfaces
    "SourceManagerInterface",
    "SourceProcessorInterface",
    "OutputManagerInterface",
    "ConfigurationProcessorInterface",
    "ServiceInterface",
    "CacheInterface",
    "EventBusInterface",
    "MetricsInterface",
    "SecurityValidatorInterface",
    "DiscoveryInterface",
    "QualityPredictorInterface",
    "GeographicOptimizerInterface",
    "AnalyticsInterface",
    "NotificationInterface",
    "DatabaseInterface",
    "ConfigurationManagerInterface",
    "PluginInterface",
    "MiddlewareInterface",
    "HealthCheckInterface",
    "RateLimiterInterface",
    "CircuitBreakerInterface",
    "RetryInterface",
    
    # Event System
    "Event",
    "EventHandler",
    "FunctionEventHandler",
    "EventBus",
    "LoggingEventHandler",
    "MetricsEventHandler",
    "NotificationEventHandler",
    "get_event_bus",
    "reset_event_bus",
    
    # Strategy Pattern
    "BaseProcessingStrategy",
    "QualityBasedProcessingStrategy",
    "GeographicProcessingStrategy",
    "PerformanceProcessingStrategy",
    "BaseValidationStrategy",
    "ProtocolValidationStrategy",
    "SecurityValidationStrategy",
    "StrategyManager",
    "get_strategy_manager",
    "reset_strategy_manager",
]
