#!/usr/bin/env python3
"""
Enhanced Component Registry
===========================

Advanced component registry with plugin support, lifecycle management,
and dynamic module loading capabilities.
"""

import importlib
import inspect
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Callable

from .interfaces import ServiceInterface
from .di_container import DIContainer, get_container

logger = logging.getLogger(__name__)

T = TypeVar('T')


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
        tags: Optional[List[str]] = None
    ):
        """Initialize component metadata.
        
        Args:
            name: Component name
            component_type: Component type/class name
            instance: Component instance
            factory: Factory function for creating instances
            dependencies: List of dependency names
            lifecycle: Component lifecycle (singleton, transient, scoped)
            version: Component version
            description: Component description
            tags: Component tags
        """
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


class PluginManager:
    """Manages plugin loading and registration."""
    
    def __init__(self):
        """Initialize the plugin manager."""
        self._plugins: Dict[str, Any] = {}
        self._plugin_metadata: Dict[str, Dict[str, Any]] = {}
        self._plugin_directories: List[Path] = []
        
    def add_plugin_directory(self, directory: Path) -> None:
        """Add a directory to search for plugins.
        
        Args:
            directory: Directory path to add
        """
        if directory not in self._plugin_directories:
            self._plugin_directories.append(directory)
            logger.debug(f"Added plugin directory: {directory}")
    
    def load_plugin(self, plugin_path: str) -> Any:
        """Load a plugin from a file path.
        
        Args:
            plugin_path: Path to the plugin file
            
        Returns:
            Loaded plugin instance
        """
        try:
            # Add plugin directory to Python path
            plugin_dir = Path(plugin_path).parent
            if str(plugin_dir) not in sys.path:
                sys.path.insert(0, str(plugin_dir))
            
            # Import the plugin module
            module_name = Path(plugin_path).stem
            module = importlib.import_module(module_name)
            
            # Look for plugin class or function
            plugin_instance = None
            if hasattr(module, 'Plugin'):
                plugin_class = getattr(module, 'Plugin')
                plugin_instance = plugin_class()
            elif hasattr(module, 'create_plugin'):
                plugin_instance = getattr(module, 'create_plugin')()
            elif hasattr(module, 'main'):
                plugin_instance = getattr(module, 'main')
            
            if plugin_instance:
                self._plugins[module_name] = plugin_instance
                self._plugin_metadata[module_name] = {
                    'path': plugin_path,
                    'module': module,
                    'loaded_at': None
                }
                logger.info(f"Loaded plugin: {module_name}")
                return plugin_instance
            else:
                logger.warning(f"No plugin found in {plugin_path}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_path}: {e}")
            return None
    
    def load_plugins_from_directory(self, directory: Path) -> List[Any]:
        """Load all plugins from a directory.
        
        Args:
            directory: Directory to search for plugins
            
        Returns:
            List of loaded plugin instances
        """
        loaded_plugins = []
        
        if not directory.exists():
            logger.warning(f"Plugin directory does not exist: {directory}")
            return loaded_plugins
        
        for plugin_file in directory.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
                
            plugin = self.load_plugin(str(plugin_file))
            if plugin:
                loaded_plugins.append(plugin)
        
        logger.info(f"Loaded {len(loaded_plugins)} plugins from {directory}")
        return loaded_plugins
    
    def get_plugin(self, name: str) -> Optional[Any]:
        """Get a loaded plugin by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance or None if not found
        """
        return self._plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, Any]:
        """Get all loaded plugins."""
        return self._plugins.copy()
    
    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            True if plugin was unloaded successfully
        """
        if name in self._plugins:
            del self._plugins[name]
            if name in self._plugin_metadata:
                del self._plugin_metadata[name]
            logger.info(f"Unloaded plugin: {name}")
            return True
        return False

# Rebind classes to modularized implementations to keep file slimmer logically
from .registry_models import ComponentMetadata as _ReExportComponentMetadata  # noqa: E402
from .plugin_manager import PluginManager as _ReExportPluginManager  # noqa: E402

ComponentMetadata = _ReExportComponentMetadata
PluginManager = _ReExportPluginManager


class EnhancedComponentRegistry:
    """Enhanced component registry with advanced features."""
    
    def __init__(self, container: Optional[DIContainer] = None):
        """Initialize the enhanced component registry.
        
        Args:
            container: Dependency injection container
        """
        self.container = container or get_container()
        self._components: Dict[str, ComponentMetadata] = {}
        self._component_types: Dict[str, Type] = {}
        self._factories: Dict[str, Callable] = {}
        self._interfaces: Dict[str, Type] = {}
        self._plugin_manager = PluginManager()
        self._auto_discovery_enabled = True
        
    def register_component(
        self,
        name: str,
        component: Any,
        component_type: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        lifecycle: str = "singleton",
        version: str = "1.0.0",
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> None:
        """Register a component with metadata.
        
        Args:
            name: Component name
            component: Component instance
            component_type: Component type name
            dependencies: List of dependency names
            lifecycle: Component lifecycle
            version: Component version
            description: Component description
            tags: Component tags
        """
        if not component_type:
            component_type = type(component).__name__
        
        metadata = ComponentMetadata(
            name=name,
            component_type=component_type,
            instance=component,
            dependencies=dependencies or [],
            lifecycle=lifecycle,
            version=version,
            description=description,
            tags=tags or []
        )
        
        self._components[name] = metadata
        
        # Register with DI container
        if lifecycle == "singleton":
            self.container.register_singleton(name, component)
        else:
            self.container.register_factory(name, lambda c: component)
        
        logger.debug(f"Registered component: {name} ({component_type})")
    
    def register_factory(
        self,
        name: str,
        factory: Callable,
        component_type: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        lifecycle: str = "transient",
        version: str = "1.0.0",
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> None:
        """Register a factory function.
        
        Args:
            name: Factory name
            factory: Factory function
            component_type: Component type name
            dependencies: List of dependency names
            lifecycle: Component lifecycle
            version: Component version
            description: Component description
            tags: Component tags
        """
        if not component_type:
            # Try to infer type from factory signature
            sig = inspect.signature(factory)
            if sig.return_annotation != inspect.Signature.empty:
                component_type = sig.return_annotation.__name__
            else:
                component_type = "Unknown"
        
        metadata = ComponentMetadata(
            name=name,
            component_type=component_type,
            instance=None,
            factory=factory,
            dependencies=dependencies or [],
            lifecycle=lifecycle,
            version=version,
            description=description,
            tags=tags or []
        )
        
        self._components[name] = metadata
        self._factories[name] = factory
        self.container.register_factory(name, factory)
        
        logger.debug(f"Registered factory: {name} ({component_type})")
    
    def register_interface(self, name: str, interface_type: Type) -> None:
        """Register an interface type.
        
        Args:
            name: Interface name
            interface_type: Interface type/class
        """
        self._interfaces[name] = interface_type
        logger.debug(f"Registered interface: {name}")
    
    def get_component(self, name: str) -> Any:
        """Get a component by name.
        
        Args:
            name: Component name
            
        Returns:
            Component instance
        """
        if name in self._components:
            metadata = self._components[name]
            metadata.last_accessed = None  # Update access time
            metadata.access_count += 1
            
            if metadata.lifecycle == "singleton":
                return metadata.instance
            elif metadata.factory:
                return metadata.factory(self.container)
            else:
                return metadata.instance
        
        # Fallback to container
        return self.container.get(name)
    
    def get_components_by_type(self, component_type: str) -> List[Any]:
        """Get all components of a specific type.
        
        Args:
            component_type: Component type name
            
        Returns:
            List of component instances
        """
        components = []
        for metadata in self._components.values():
            if metadata.component_type == component_type:
                components.append(metadata.instance)
        return components
    
    def get_components_by_tag(self, tag: str) -> List[Any]:
        """Get all components with a specific tag.
        
        Args:
            tag: Tag name
            
        Returns:
            List of component instances
        """
        components = []
        for metadata in self._components.values():
            if tag in metadata.tags:
                components.append(metadata.instance)
        return components
    
    def get_component_metadata(self, name: str) -> Optional[ComponentMetadata]:
        """Get component metadata.
        
        Args:
            name: Component name
            
        Returns:
            Component metadata or None if not found
        """
        return self._components.get(name)
    
    def list_components(self) -> List[str]:
        """List all registered component names."""
        return list(self._components.keys())
    
    def list_components_by_type(self) -> Dict[str, List[str]]:
        """List components grouped by type."""
        by_type = {}
        for name, metadata in self._components.items():
            component_type = metadata.component_type
            if component_type not in by_type:
                by_type[component_type] = []
            by_type[component_type].append(name)
        return by_type
    
    def has_component(self, name: str) -> bool:
        """Check if a component is registered.
        
        Args:
            name: Component name
            
        Returns:
            True if component is registered
        """
        return name in self._components or self.container.has(name)
    
    def remove_component(self, name: str) -> bool:
        """Remove a component.
        
        Args:
            name: Component name
            
        Returns:
            True if component was removed
        """
        if name in self._components:
            del self._components[name]
            logger.debug(f"Removed component: {name}")
            return True
        return False
    
    def clear_components(self) -> None:
        """Clear all registered components."""
        self._components.clear()
        self._factories.clear()
        self.container.clear()
        logger.info("Cleared all components")
    
    def auto_discover_components(self, module_path: str) -> None:
        """Automatically discover and register components from a module.
        
        Args:
            module_path: Path to the module to scan
        """
        try:
            module = importlib.import_module(module_path)
            
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and not name.startswith('_'):
                    # Check if it's a service
                    if issubclass(obj, ServiceInterface):
                        self.register_component(
                            name.lower(),
                            obj(),
                            component_type=name,
                            description=f"Auto-discovered service: {name}"
                        )
                    # Check if it has a factory method
                    elif hasattr(obj, 'create') and callable(getattr(obj, 'create')):
                        self.register_factory(
                            name.lower(),
                            getattr(obj, 'create'),
                            component_type=name,
                            description=f"Auto-discovered factory: {name}"
                        )
            
            logger.info(f"Auto-discovered components from {module_path}")
            
        except Exception as e:
            logger.error(f"Failed to auto-discover components from {module_path}: {e}")
    
    def get_plugin_manager(self) -> PluginManager:
        """Get the plugin manager.
        
        Returns:
            Plugin manager instance
        """
        return self._plugin_manager
    
    def enable_auto_discovery(self) -> None:
        """Enable automatic component discovery."""
        self._auto_discovery_enabled = True
        logger.debug("Enabled auto-discovery")
    
    def disable_auto_discovery(self) -> None:
        """Disable automatic component discovery."""
        self._auto_discovery_enabled = False
        logger.debug("Disabled auto-discovery")
    
    def get_registry_info(self) -> Dict[str, Any]:
        """Get comprehensive registry information.
        
        Returns:
            Dictionary containing registry information
        """
        return {
            "total_components": len(self._components),
            "total_factories": len(self._factories),
            "total_interfaces": len(self._interfaces),
            "total_plugins": len(self._plugin_manager.get_all_plugins()),
            "components_by_type": self.list_components_by_type(),
            "auto_discovery_enabled": self._auto_discovery_enabled,
            "component_metadata": {
                name: {
                    "type": metadata.component_type,
                    "lifecycle": metadata.lifecycle,
                    "version": metadata.version,
                    "dependencies": metadata.dependencies,
                    "tags": metadata.tags,
                    "access_count": metadata.access_count
                }
                for name, metadata in self._components.items()
            }
        }


# Global enhanced registry instance
_enhanced_registry: Optional[EnhancedComponentRegistry] = None


def get_enhanced_registry() -> EnhancedComponentRegistry:
    """Get the global enhanced component registry.
    
    Returns:
        Global EnhancedComponentRegistry instance
    """
    global _enhanced_registry
    if _enhanced_registry is None:
        _enhanced_registry = EnhancedComponentRegistry()
    return _enhanced_registry


def reset_enhanced_registry() -> None:
    """Reset the global enhanced component registry."""
    global _enhanced_registry
    if _enhanced_registry:
        _enhanced_registry.clear_components()
    _enhanced_registry = None
