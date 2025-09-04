"""
Configuration Manager
====================

Centralized configuration management for the VPN merger system.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Centralized configuration manager for VPN merger components.
    
    This manager handles configuration loading, validation, and distribution
    to components throughout the system.
    """
    
    def __init__(self, config_path: Optional[str | Path] = None):
        """Initialize the configuration manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = Path(config_path) if config_path else Path("config/sources.unified.yaml")
        self._config: Dict[str, Any] = {}
        self._environment_config: Dict[str, Any] = {}
        
        # Load default configuration
        self._load_defaults()
        self._load_environment()
        
    def _load_defaults(self) -> None:
        """Load default configuration values."""
        self._config = {
            "sources": {
                "config_path": str(self.config_path),
                "max_sources": 100,
                "priority_enabled": True,
            },
            "processing": {
                "max_concurrent": 50,
                "batch_size": 10,
                "timeout": 30,
                "max_retries": 3,
            },
            "output": {
                "formats": ["txt", "json", "yaml"],
                "output_dir": "output",
                "include_metadata": True,
            },
            "ml": {
                "enabled": False,
                "model_path": "models/",
                "prediction_threshold": 0.5,
            },
            "cache": {
                "enabled": False,
                "redis_url": "redis://localhost:6379",
                "ttl": 3600,
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        }
        
    def _load_environment(self) -> None:
        """Load configuration from environment variables."""
        env_mapping = {
            "VPN_MERGER_MAX_SOURCES": ("sources", "max_sources"),
            "VPN_MERGER_MAX_CONCURRENT": ("processing", "max_concurrent"),
            "VPN_MERGER_BATCH_SIZE": ("processing", "batch_size"),
            "VPN_MERGER_TIMEOUT": ("processing", "timeout"),
            "VPN_MERGER_OUTPUT_DIR": ("output", "output_dir"),
            "VPN_MERGER_ML_ENABLED": ("ml", "enabled"),
            "VPN_MERGER_CACHE_ENABLED": ("cache", "enabled"),
            "VPN_MERGER_REDIS_URL": ("cache", "redis_url"),
            "VPN_MERGER_LOG_LEVEL": ("logging", "level"),
        }
        
        for env_var, (section, key) in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if key in ["max_sources", "max_concurrent", "batch_size", "timeout", "max_retries", "ttl"]:
                    value = int(value)
                elif key in ["enabled"]:
                    value = value.lower() in ("true", "1", "yes", "on")
                elif key in ["prediction_threshold"]:
                    value = float(value)
                    
                self._config[section][key] = value
                self._environment_config[env_var] = value
                
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        return self._config.get(section, {}).get(key, default)
        
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire configuration section.
        
        Args:
            section: Configuration section name
            
        Returns:
            Configuration section dictionary
        """
        return self._config.get(section, {})
        
    def set(self, section: str, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            value: Configuration value
        """
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value
        logger.debug(f"Set config: {section}.{key} = {value}")
        
    def update_section(self, section: str, values: Dict[str, Any]) -> None:
        """Update an entire configuration section.
        
        Args:
            section: Configuration section name
            values: Configuration values to update
        """
        if section not in self._config:
            self._config[section] = {}
        self._config[section].update(values)
        logger.debug(f"Updated config section: {section}")
        
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration.
        
        Returns:
            Complete configuration dictionary
        """
        return self._config.copy()
        
    def get_environment_config(self) -> Dict[str, Any]:
        """Get configuration loaded from environment variables.
        
        Returns:
            Environment configuration dictionary
        """
        return self._environment_config.copy()
        
    def validate(self) -> bool:
        """Validate the current configuration.
        
        Returns:
            True if configuration is valid
        """
        try:
            # Validate required sections
            required_sections = ["sources", "processing", "output"]
            for section in required_sections:
                if section not in self._config:
                    logger.error(f"Missing required configuration section: {section}")
                    return False
                    
            # Validate processing configuration
            processing = self._config.get("processing", {})
            if processing.get("max_concurrent", 0) <= 0:
                logger.error("max_concurrent must be positive")
                return False
                
            if processing.get("batch_size", 0) <= 0:
                logger.error("batch_size must be positive")
                return False
                
            # Validate sources configuration
            sources = self._config.get("sources", {})
            if sources.get("max_sources", 0) <= 0:
                logger.error("max_sources must be positive")
                return False
                
            logger.debug("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
            
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._config.clear()
        self._environment_config.clear()
        self._load_defaults()
        self._load_environment()
        logger.debug("Configuration reset to defaults")


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager.
    
    Returns:
        Global ConfigurationManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def reset_config_manager() -> None:
    """Reset the global configuration manager."""
    global _config_manager
    _config_manager = None
