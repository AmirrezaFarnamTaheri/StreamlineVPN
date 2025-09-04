"""
Dependency Injection Container
=============================

Provides a centralized dependency injection container to manage component
dependencies and reduce tight coupling throughout the application.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar

from ..models.configuration import VPNConfiguration
from .config_processor import ConfigurationProcessor
from .output import OutputManager
from .source_manager import SourceManager
from .source_processor import SourceProcessor

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DIContainer:
    """Dependency Injection Container for managing component dependencies.
    
    This container manages the lifecycle and dependencies of all major components
    in the VPN merger system, reducing tight coupling and enabling easier testing.
    """
    
    def __init__(self):
        """Initialize the dependency injection container."""
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._config: Dict[str, Any] = {}
        
    def register_config(self, config: Dict[str, Any]) -> None:
        """Register configuration settings.
        
        Args:
            config: Configuration dictionary
        """
        self._config.update(config)
        logger.debug(f"Registered configuration: {list(config.keys())}")
        
    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton instance.
        
        Args:
            name: Component name
            instance: Component instance
        """
        self._singletons[name] = instance
        logger.debug(f"Registered singleton: {name}")
        
    def register_factory(self, name: str, factory: callable) -> None:
        """Register a factory function for creating instances.
        
        Args:
            name: Component name
            factory: Factory function
        """
        self._factories[name] = factory
        logger.debug(f"Registered factory: {name}")
        
    def get(self, name: str) -> Any:
        """Get a component instance.
        
        Args:
            name: Component name
            
        Returns:
            Component instance
            
        Raises:
            KeyError: If component is not registered
        """
        # Check singletons first
        if name in self._singletons:
            return self._singletons[name]
            
        # Check factories
        if name in self._factories:
            instance = self._factories[name](self)
            self._instances[name] = instance
            return instance
            
        # Check instances
        if name in self._instances:
            return self._instances[name]
            
        raise KeyError(f"Component '{name}' not registered")
        
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self._config.get(key, default)
        
    def has(self, name: str) -> bool:
        """Check if component is registered.
        
        Args:
            name: Component name
            
        Returns:
            True if component is registered
        """
        return name in self._singletons or name in self._factories or name in self._instances
        
    def clear(self) -> None:
        """Clear all registered components."""
        self._instances.clear()
        self._factories.clear()
        self._singletons.clear()
        self._config.clear()
        logger.debug("Cleared all registered components")


# Global container instance
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """Get the global dependency injection container.
    
    Returns:
        Global DIContainer instance
    """
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def reset_container() -> None:
    """Reset the global dependency injection container."""
    global _container
    if _container:
        _container.clear()
    _container = None
