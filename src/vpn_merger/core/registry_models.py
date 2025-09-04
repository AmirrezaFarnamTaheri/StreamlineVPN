"""
Registry models: component metadata container.
"""

from __future__ import annotations

from typing import Any, Callable, List, Optional


class ComponentMetadata:
    """Metadata for registered components."""

    def __init__(
        self,
        name: str,
        component_type: str,
        instance: Any,
        factory: Optional[Callable] = None,
        dependencies: Optional[List[str]] = None,
        lifecycle: str = "singleton",
        version: str = "1.0.0",
        description: str = "",
        tags: Optional[List[str]] = None,
    ):
        self.name = name
        self.component_type = component_type
        self.instance = instance
        self.factory = factory
        self.dependencies = dependencies or []
        self.lifecycle = lifecycle
        self.version = version
        self.description = description
        self.tags = tags or []
        self.created_at = None
        self.last_accessed = None
        self.access_count = 0

