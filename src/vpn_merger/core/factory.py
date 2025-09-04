"""
Factory Pattern for VPN Merger Components
=========================================

Provides factory classes for creating VPN merger components with proper
dependency injection and configuration management.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .di_container import DIContainer, get_container
from .config_processor import ConfigurationProcessor
from .output import OutputManager
from .source_manager import SourceManager
from .source_processor import SourceProcessor

logger = logging.getLogger(__name__)


class VPNMergerFactory:
    """Factory for creating VPN merger components with dependency injection.
    
    This factory manages the creation of all major components in the VPN merger
    system, ensuring proper dependency injection and reducing tight coupling.
    """
    
    def __init__(self, container: Optional[DIContainer] = None):
        """Initialize the factory.
        
        Args:
            container: Dependency injection container (uses global if None)
        """
        self.container = container or get_container()
        
    def create_source_manager(self, config_path: str | Path = "config/sources.unified.yaml") -> SourceManager:
        """Create a SourceManager instance.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            SourceManager instance
        """
        if not self.container.has("source_manager"):
            source_manager = SourceManager(config_path)
            self.container.register_singleton("source_manager", source_manager)
            logger.debug("Created SourceManager instance")
        return self.container.get("source_manager")
        
    def create_config_processor(self) -> ConfigurationProcessor:
        """Create a ConfigurationProcessor instance.
        
        Returns:
            ConfigurationProcessor instance
        """
        if not self.container.has("config_processor"):
            config_processor = ConfigurationProcessor()
            self.container.register_singleton("config_processor", config_processor)
            logger.debug("Created ConfigurationProcessor instance")
        return self.container.get("config_processor")
        
    def create_source_processor(self) -> SourceProcessor:
        """Create a SourceProcessor instance.
        
        Returns:
            SourceProcessor instance
        """
        if not self.container.has("source_processor"):
            source_processor = SourceProcessor()
            self.container.register_singleton("source_processor", source_processor)
            logger.debug("Created SourceProcessor instance")
        return self.container.get("source_processor")
        
    def create_output_manager(self) -> OutputManager:
        """Create an OutputManager instance.
        
        Returns:
            OutputManager instance
        """
        if not self.container.has("output_manager"):
            output_manager = OutputManager()
            self.container.register_singleton("output_manager", output_manager)
            logger.debug("Created OutputManager instance")
        return self.container.get("output_manager")
        
    def create_merger(self, config_path: str | Path = "config/sources.unified.yaml") -> "VPNSubscriptionMerger":
        """Create a VPNSubscriptionMerger instance with all dependencies.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            VPNSubscriptionMerger instance
        """
        # Import here to avoid circular imports
        from .merger import VPNSubscriptionMerger
        
        if not self.container.has("merger"):
            # Create dependencies
            source_manager = self.create_source_manager(config_path)
            source_processor = self.create_source_processor()
            output_manager = self.create_output_manager()
            
            # Create merger with injected dependencies
            merger = VPNSubscriptionMerger(
                source_manager=source_manager,
                source_processor=source_processor,
                output_manager=output_manager
            )
            self.container.register_singleton("merger", merger)
            logger.debug("Created VPNSubscriptionMerger instance with dependencies")
            
        return self.container.get("merger")
        
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the factory with settings.
        
        Args:
            config: Configuration dictionary
        """
        self.container.register_config(config)
        logger.debug(f"Configured factory with: {list(config.keys())}")


class ComponentRegistry:
    """Registry for managing component lifecycle and dependencies.
    
    This registry provides a centralized way to manage component creation,
    configuration, and lifecycle across the application.
    """
    
    def __init__(self):
        """Initialize the component registry."""
        self.container = get_container()
        self.factory = VPNMergerFactory(self.container)
        
    def register_default_components(self, config: Dict[str, Any]) -> None:
        """Register default components with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.factory.configure(config)
        
        # Pre-create core components
        self.factory.create_source_manager()
        self.factory.create_config_processor()
        self.factory.create_source_processor()
        self.factory.create_output_manager()
        
        logger.info("Registered default components")
        
    def get_component(self, name: str) -> Any:
        """Get a component by name.
        
        Args:
            name: Component name
            
        Returns:
            Component instance
        """
        return self.container.get(name)
        
    def has_component(self, name: str) -> bool:
        """Check if component exists.
        
        Args:
            name: Component name
            
        Returns:
            True if component exists
        """
        return self.container.has(name)
        
    def clear_components(self) -> None:
        """Clear all registered components."""
        self.container.clear()
        logger.info("Cleared all registered components")


# Global registry instance
_registry: Optional[ComponentRegistry] = None


def get_registry() -> ComponentRegistry:
    """Get the global component registry.
    
    Returns:
        Global ComponentRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ComponentRegistry()
    return _registry


def reset_registry() -> None:
    """Reset the global component registry."""
    global _registry
    if _registry:
        _registry.clear_components()
    _registry = None
