"""
Service Container
================

Dependency injection container for VPN merger services.
"""

import logging
from typing import Dict, Any, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceContainer:
    """Dependency injection container for managing service instances."""
    
    def __init__(self):
        """Initialize the service container."""
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
    
    def register(self, service_name: str, service_instance: Any = None, 
                instance: Any = None, factory: callable = None) -> None:
        """Register a service instance.
        
        Args:
            service_name: Name of the service
            service_instance: Service instance to register (deprecated, use instance)
            instance: Service instance to register
            factory: Factory function to create service instances
        """
        if instance is not None:
            self._services[service_name] = instance
        elif factory is not None:
            self._factories[service_name] = factory
        elif service_instance is not None:
            self._services[service_name] = service_instance
        else:
            raise ValueError("Must provide either instance or factory")
        
        logger.debug(f"Registered service: {service_name}")
    
    def register_singleton(self, service_name: str, service_class: Type[T], **kwargs) -> None:
        """Register a singleton service.
        
        Args:
            service_name: Name of the service
            service_class: Service class to instantiate
            **kwargs: Constructor arguments
        """
        self._factories[service_name] = lambda: service_class(**kwargs)
        logger.debug(f"Registered singleton factory: {service_name}")
    
    def register_factory(self, service_name: str, factory_func: callable) -> None:
        """Register a factory function for a service.
        
        Args:
            service_name: Name of the service
            factory_func: Factory function to create service instances
        """
        self._factories[service_name] = factory_func
        logger.debug(f"Registered factory: {service_name}")
    
    def get(self, service_name: str) -> Any:
        """Get a service instance.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service is not registered
        """
        # Check if already instantiated
        if service_name in self._singletons:
            return self._singletons[service_name]
        
        # Check if we have a direct instance
        if service_name in self._services:
            return self._services[service_name]
        
        # Check if we have a factory
        if service_name in self._factories:
            instance = self._factories[service_name]()
            self._singletons[service_name] = instance
            return instance
        
        raise KeyError(f"Service '{service_name}' not registered")
    
    def has(self, service_name: str) -> bool:
        """Check if a service is registered.
        
        Args:
            service_name: Name of the service to check
            
        Returns:
            True if service is registered, False otherwise
        """
        return (service_name in self._services or 
                service_name in self._factories or 
                service_name in self._singletons)
    
    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()
    
    def create_scope(self) -> 'ServiceContainer':
        """Create a new scope container.
        
        Returns:
            New ServiceContainer instance for scoped services
        """
        scope = ServiceContainer()
        # Copy services from parent to scope
        scope._services.update(self._services)
        scope._factories.update(self._factories)
        scope._singletons.update(self._singletons)
        return scope
        logger.debug("Service container cleared")


# Global service container instance
container = ServiceContainer()
