#!/usr/bin/env python3
"""
Base Service Implementation
===========================

Provides base service classes and common functionality for all services.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar

from ..core.interfaces import ServiceInterface

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseService(ServiceInterface):
    """Base service implementation with common functionality."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the base service.
        
        Args:
            name: Service name
            config: Service configuration
        """
        self.name = name
        self.config = config or {}
        self._initialized = False
        self._shutdown = False
        self._health_status = "unknown"
        self._dependencies: List[ServiceInterface] = []
        self._metrics: Dict[str, Any] = {}
        
    async def initialize(self) -> None:
        """Initialize the service."""
        if self._initialized:
            logger.warning(f"Service {self.name} already initialized")
            return
            
        try:
            logger.info(f"Initializing service: {self.name}")
            await self._initialize_dependencies()
            await self._do_initialize()
            self._initialized = True
            self._health_status = "healthy"
            logger.info(f"Service {self.name} initialized successfully")
        except Exception as e:
            self._health_status = "unhealthy"
            logger.error(f"Failed to initialize service {self.name}: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the service."""
        if self._shutdown:
            logger.warning(f"Service {self.name} already shutdown")
            return
            
        try:
            logger.info(f"Shutting down service: {self.name}")
            await self._do_shutdown()
            await self._shutdown_dependencies()
            self._shutdown = True
            self._health_status = "shutdown"
            logger.info(f"Service {self.name} shutdown successfully")
        except Exception as e:
            logger.error(f"Error during service {self.name} shutdown: {e}")
            raise
    
    def is_healthy(self) -> bool:
        """Check if the service is healthy."""
        return self._health_status == "healthy"
    
    def get_health_status(self) -> str:
        """Get current health status."""
        return self._health_status
    
    def add_dependency(self, service: ServiceInterface) -> None:
        """Add a service dependency.
        
        Args:
            service: Service dependency to add
        """
        self._dependencies.append(service)
        logger.debug(f"Added dependency {service.name} to service {self.name}")
    
    def get_dependencies(self) -> List[ServiceInterface]:
        """Get service dependencies."""
        return self._dependencies.copy()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return self._metrics.copy()
    
    def update_metric(self, key: str, value: Any) -> None:
        """Update a service metric.
        
        Args:
            key: Metric key
            value: Metric value
        """
        self._metrics[key] = value
    
    @abstractmethod
    async def _do_initialize(self) -> None:
        """Service-specific initialization logic."""
        pass
    
    @abstractmethod
    async def _do_shutdown(self) -> None:
        """Service-specific shutdown logic."""
        pass
    
    async def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        for dependency in self._dependencies:
            if not dependency._initialized:
                await dependency.initialize()
    
    async def _shutdown_dependencies(self) -> None:
        """Shutdown service dependencies."""
        for dependency in reversed(self._dependencies):
            if not dependency._shutdown:
                await dependency.shutdown()


class ServiceManager:
    """Manages service lifecycle and dependencies."""
    
    def __init__(self):
        """Initialize the service manager."""
        self._services: Dict[str, ServiceInterface] = {}
        self._service_graph: Dict[str, List[str]] = {}
        self._initialized = False
        
    def register_service(self, service: ServiceInterface) -> None:
        """Register a service.
        
        Args:
            service: Service to register
        """
        self._services[service.name] = service
        self._service_graph[service.name] = []
        logger.debug(f"Registered service: {service.name}")
    
    def add_service_dependency(self, service_name: str, dependency_name: str) -> None:
        """Add a dependency between services.
        
        Args:
            service_name: Name of the service
            dependency_name: Name of the dependency
        """
        if service_name not in self._service_graph:
            self._service_graph[service_name] = []
        
        if dependency_name not in self._service_graph[service_name]:
            self._service_graph[service_name].append(dependency_name)
            logger.debug(f"Added dependency {dependency_name} to service {service_name}")
    
    async def initialize_all(self) -> None:
        """Initialize all services in dependency order."""
        if self._initialized:
            logger.warning("Services already initialized")
            return
            
        try:
            # Topological sort to determine initialization order
            init_order = self._topological_sort()
            
            logger.info(f"Initializing services in order: {init_order}")
            
            for service_name in init_order:
                if service_name in self._services:
                    service = self._services[service_name]
                    
                    # Add dependencies
                    for dep_name in self._service_graph.get(service_name, []):
                        if dep_name in self._services:
                            service.add_dependency(self._services[dep_name])
                    
                    await service.initialize()
            
            self._initialized = True
            logger.info("All services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            await self.shutdown_all()
            raise
    
    async def shutdown_all(self) -> None:
        """Shutdown all services."""
        try:
            # Shutdown in reverse order
            service_names = list(self._services.keys())
            for service_name in reversed(service_names):
                service = self._services[service_name]
                if service._initialized and not service._shutdown:
                    await service.shutdown()
            
            self._initialized = False
            logger.info("All services shutdown successfully")
            
        except Exception as e:
            logger.error(f"Error during service shutdown: {e}")
            raise
    
    def get_service(self, name: str) -> Optional[ServiceInterface]:
        """Get a service by name.
        
        Args:
            name: Service name
            
        Returns:
            Service instance or None if not found
        """
        return self._services.get(name)
    
    def get_all_services(self) -> Dict[str, ServiceInterface]:
        """Get all registered services."""
        return self._services.copy()
    
    def get_service_health(self) -> Dict[str, str]:
        """Get health status of all services."""
        return {
            name: service.get_health_status()
            for name, service in self._services.items()
        }
    
    def _topological_sort(self) -> List[str]:
        """Perform topological sort of services based on dependencies."""
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(node: str) -> None:
            if node in temp_visited:
                raise ValueError(f"Circular dependency detected involving {node}")
            if node in visited:
                return
                
            temp_visited.add(node)
            
            # Visit dependencies first
            for dep in self._service_graph.get(node, []):
                visit(dep)
            
            temp_visited.remove(node)
            visited.add(node)
            result.append(node)
        
        # Visit all nodes
        for node in self._service_graph:
            if node not in visited:
                visit(node)
        
        return result


class ServiceRegistry:
    """Registry for service types and factories."""
    
    def __init__(self):
        """Initialize the service registry."""
        self._service_types: Dict[str, Type[ServiceInterface]] = {}
        self._service_factories: Dict[str, callable] = {}
        
    def register_service_type(self, name: str, service_type: Type[ServiceInterface]) -> None:
        """Register a service type.
        
        Args:
            name: Service type name
            service_type: Service class
        """
        self._service_types[name] = service_type
        logger.debug(f"Registered service type: {name}")
    
    def register_service_factory(self, name: str, factory: callable) -> None:
        """Register a service factory.
        
        Args:
            name: Service type name
            factory: Factory function
        """
        self._service_factories[name] = factory
        logger.debug(f"Registered service factory: {name}")
    
    def create_service(self, name: str, service_type: str, config: Optional[Dict[str, Any]] = None) -> ServiceInterface:
        """Create a service instance.
        
        Args:
            name: Service instance name
            service_type: Service type name
            config: Service configuration
            
        Returns:
            Service instance
        """
        if service_type in self._service_factories:
            return self._service_factories[service_type](name, config)
        elif service_type in self._service_types:
            service_class = self._service_types[service_type]
            return service_class(name, config)
        else:
            raise ValueError(f"Unknown service type: {service_type}")
    
    def get_service_types(self) -> List[str]:
        """Get all registered service types."""
        return list(self._service_types.keys()) + list(self._service_factories.keys())


# Global service manager instance
_service_manager: Optional[ServiceManager] = None
_service_registry: Optional[ServiceRegistry] = None


def get_service_manager() -> ServiceManager:
    """Get the global service manager.
    
    Returns:
        Global ServiceManager instance
    """
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager()
    return _service_manager


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry.
    
    Returns:
        Global ServiceRegistry instance
    """
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry


def reset_service_manager() -> None:
    """Reset the global service manager."""
    global _service_manager
    if _service_manager:
        asyncio.create_task(_service_manager.shutdown_all())
    _service_manager = None


def reset_service_registry() -> None:
    """Reset the global service registry."""
    global _service_registry
    _service_registry = None
