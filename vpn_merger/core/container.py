from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Type


@dataclass
class ServiceContainer:
    """Lightweight dependency injection container.

    - register(Type, instance=...) for singletons
    - register(Type, factory=lambda: ...) for lazy singletons
    - get(Type) to resolve
    - create_scope() to create a scoped container sharing factories
    """

    _services: Dict[Type, Any] = field(default_factory=dict)
    _factories: Dict[Type, Callable[[], Any]] = field(default_factory=dict)

    def register(self, service_type: Type, instance: Any | None = None, factory: Callable[[], Any] | None = None) -> None:
        if instance is not None and factory is not None:
            raise ValueError("Provide either instance or factory, not both")
        if instance is None and factory is None:
            raise ValueError("Must provide either instance or factory")
        if instance is not None:
            self._services[service_type] = instance
        else:
            assert factory is not None
            self._factories[service_type] = factory

    def get(self, service_type: Type) -> Any:
        if service_type in self._services:
            return self._services[service_type]
        if service_type in self._factories:
            inst = self._factories[service_type]()
            self._services[service_type] = inst
            return inst
        raise KeyError(f"Service {service_type} not registered")

    def create_scope(self) -> "ServiceContainer":
        scope = ServiceContainer()
        scope._factories = self._factories.copy()
        return scope

