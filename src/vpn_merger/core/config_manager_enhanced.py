#!/usr/bin/env python3
"""
Enhanced Configuration Manager
==============================

Advanced configuration management with support for enhanced YAML structure,
validation, monitoring, and quality controls.

This module is now a thin orchestration layer that delegates parsing and
data models to `config_parser` and `config_models` for better modularity.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import yaml
except ImportError:
    yaml = None

from .config_models import (
    EnhancedConfig,
    ProcessingConfig,
    QualityConfig,
    MonitoringConfig,
    SecurityConfig,
    OutputConfig,
)
from .config_parser import parse_enhanced_config, get_default_enhanced_config

logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_CONFIG_PATH = "config/sources.enhanced.yaml"


class EnhancedConfigurationManager:
    """Enhanced configuration manager with advanced features."""
    
    def __init__(self, config_path: Union[str, Path] = DEFAULT_CONFIG_PATH):
        """Initialize the enhanced configuration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = Path(config_path)
        self.config: Optional[EnhancedConfig] = None
        self._load_config()
        
    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            if yaml is None:
                logger.warning("PyYAML not available, using default configuration")
                self.config = get_default_enhanced_config()
                return
                
            if not self.config_path.exists():
                logger.warning(f"Config file {self.config_path} not found, using default configuration")
                self.config = get_default_enhanced_config()
                return
                
            with open(self.config_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
                
            if not config_data:
                logger.warning("Empty config file, using default configuration")
                self.config = get_default_enhanced_config()
                return
                
            self.config = parse_enhanced_config(config_data)
            logger.info(f"Loaded enhanced configuration from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config = get_default_enhanced_config()
            
    def _parse_config(self, config_data: Dict[str, Any]) -> EnhancedConfig:
        """Backwards-compatible method delegating to config_parser."""
        return parse_enhanced_config(config_data)

    def _get_default_config(self) -> EnhancedConfig:
        """Backwards-compatible method delegating to config_parser."""
        return get_default_enhanced_config()
        
    def get_processing_config(self) -> ProcessingConfig:
        """Get processing configuration.
        
        Returns:
            Processing configuration
        """
        if self.config:
            return self.config.processing
        return ProcessingConfig()
        
    def get_quality_config(self) -> QualityConfig:
        """Get quality configuration.
        
        Returns:
            Quality configuration
        """
        if self.config:
            return self.config.quality
        return QualityConfig()
        
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration.
        
        Returns:
            Monitoring configuration
        """
        if self.config:
            return self.config.monitoring
        return MonitoringConfig()
        
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration.
        
        Returns:
            Security configuration
        """
        if self.config:
            return self.config.security
        return SecurityConfig()
        
    def get_output_config(self) -> OutputConfig:
        """Get output configuration.
        
        Returns:
            Output configuration
        """
        if self.config:
            return self.config.output
        return OutputConfig()
        
    def get_sources_config(self) -> Dict[str, Any]:
        """Get sources configuration.
        
        Returns:
            Sources configuration
        """
        if self.config:
            return self.config.sources
        return {}
        
    def get_concurrent_limit(self) -> int:
        """Get concurrent processing limit.
        
        Returns:
            Concurrent limit
        """
        return self.get_processing_config().concurrent_limit
        
    def get_timeout(self) -> int:
        """Get request timeout.
        
        Returns:
            Timeout in seconds
        """
        return self.get_processing_config().timeout
        
    def get_max_retries(self) -> int:
        """Get maximum retry attempts.
        
        Returns:
            Maximum retries
        """
        return self.get_processing_config().max_retries
        
    def get_min_quality_score(self) -> float:
        """Get minimum quality score threshold.
        
        Returns:
            Minimum quality score
        """
        return self.get_quality_config().min_score
        
    def get_quality_weights(self) -> Dict[str, float]:
        """Get quality scoring weights.
        
        Returns:
            Quality scoring weights
        """
        return self.get_quality_config().scoring_weights
        
    def get_alert_thresholds(self) -> Dict[str, float]:
        """Get alert thresholds.
        
        Returns:
            Alert thresholds
        """
        return self.get_monitoring_config().alert_thresholds
        
    def get_output_formats(self) -> Dict[str, bool]:
        """Get output formats configuration.
        
        Returns:
            Output formats configuration
        """
        return self.get_output_config().formats
        
    def get_output_directory(self) -> str:
        """Get output directory.
        
        Returns:
            Output directory path
        """
        return self.get_output_config().directory
        
    def is_ssl_validation_enabled(self) -> bool:
        """Check if SSL validation is enabled.
        
        Returns:
            True if SSL validation is enabled
        """
        return self.get_security_config().ssl_validation.get("enabled", True)
        
    def is_deduplication_enabled(self) -> bool:
        """Check if deduplication is enabled.
        
        Returns:
            True if deduplication is enabled
        """
        return self.get_quality_config().deduplication
        
    def is_metrics_enabled(self) -> bool:
        """Check if metrics collection is enabled.
        
        Returns:
            True if metrics collection is enabled
        """
        return self.get_monitoring_config().metrics_enabled
        
    def get_health_check_interval(self) -> int:
        """Get health check interval.
        
        Returns:
            Health check interval in seconds
        """
        return self.get_monitoring_config().health_check_interval
        
    def get_rate_limiting_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration.
        
        Returns:
            Rate limiting configuration
        """
        return self.get_processing_config().rate_limiting
        
    def get_caching_config(self) -> Dict[str, Any]:
        """Get caching configuration.
        
        Returns:
            Caching configuration
        """
        return self.get_processing_config().caching
        
    def get_memory_management_config(self) -> Dict[str, Any]:
        """Get memory management configuration.
        
        Returns:
            Memory management configuration
        """
        return self.get_processing_config().memory_management
        
    def get_retry_policy(self) -> Dict[str, Any]:
        """Get retry policy configuration.
        
        Returns:
            Retry policy configuration
        """
        return self.get_processing_config().retry_policy
        
    def get_content_validation_config(self) -> Dict[str, Any]:
        """Get content validation configuration.
        
        Returns:
            Content validation configuration
        """
        return self.get_quality_config().content_validation
        
    def get_source_filtering_config(self) -> Dict[str, Any]:
        """Get source filtering configuration.
        
        Returns:
            Source filtering configuration
        """
        return self.get_quality_config().source_filtering
        
    def get_quality_thresholds(self) -> Dict[str, float]:
        """Get quality thresholds.
        
        Returns:
            Quality thresholds
        """
        return self.get_quality_config().quality_thresholds
        
    def get_alert_channels(self) -> List[Dict[str, Any]]:
        """Get alert channels configuration.
        
        Returns:
            Alert channels configuration
        """
        return self.get_monitoring_config().alert_channels
        
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration.
        
        Returns:
            Logging configuration
        """
        return self.get_monitoring_config().logging
        
    def get_performance_monitoring_config(self) -> Dict[str, Any]:
        """Get performance monitoring configuration.
        
        Returns:
            Performance monitoring configuration
        """
        return self.get_monitoring_config().performance_monitoring
        
    def get_compression_config(self) -> Dict[str, Any]:
        """Get compression configuration.
        
        Returns:
            Compression configuration
        """
        return self.get_output_config().compression
        
    def get_file_management_config(self) -> Dict[str, Any]:
        """Get file management configuration.
        
        Returns:
            File management configuration
        """
        return self.get_output_config().file_management
        
    def get_quality_control_config(self) -> Dict[str, Any]:
        """Get quality control configuration.
        
        Returns:
            Quality control configuration
        """
        return self.get_output_config().quality_control
        
    def reload_config(self) -> None:
        """Reload configuration from file."""
        logger.info("Reloading enhanced configuration")
        self._load_config()
        
    def validate_config(self) -> bool:
        """Validate configuration.
        
        Returns:
            True if configuration is valid
        """
        if not self.config:
            logger.error("Configuration not loaded")
            return False
            
        try:
            # Validate processing configuration
            processing = self.config.processing
            if processing.concurrent_limit <= 0:
                logger.error("Invalid concurrent_limit: must be positive")
                return False
                
            if processing.timeout <= 0:
                logger.error("Invalid timeout: must be positive")
                return False
                
            if processing.max_retries < 0:
                logger.error("Invalid max_retries: must be non-negative")
                return False
                
            # Validate quality configuration
            quality = self.config.quality
            if not 0 <= quality.min_score <= 1:
                logger.error("Invalid min_score: must be between 0 and 1")
                return False
                
            # Validate monitoring configuration
            monitoring = self.config.monitoring
            if monitoring.health_check_interval <= 0:
                logger.error("Invalid health_check_interval: must be positive")
                return False
                
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
            
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary.
        
        Returns:
            Configuration summary
        """
        if not self.config:
            return {"error": "Configuration not loaded"}
            
        return {
            "metadata": self.config.metadata,
            "processing": {
                "concurrent_limit": self.config.processing.concurrent_limit,
                "timeout": self.config.processing.timeout,
                "max_retries": self.config.processing.max_retries,
                "batch_size": self.config.processing.batch_size
            },
            "quality": {
                "min_score": self.config.quality.min_score,
                "deduplication": self.config.quality.deduplication,
                "protocol_validation": self.config.quality.protocol_validation
            },
            "monitoring": {
                "metrics_enabled": self.config.monitoring.metrics_enabled,
                "health_check_interval": self.config.monitoring.health_check_interval
            },
            "security": {
                "ssl_validation": self.config.security.ssl_validation.get("enabled", True)
            },
            "output": {
                "directory": self.config.output.directory,
                "formats": self.config.output.formats
            }
        }


# Global instance
_enhanced_config_manager: Optional[EnhancedConfigurationManager] = None


def get_enhanced_config_manager() -> EnhancedConfigurationManager:
    """Get the global enhanced configuration manager instance.
    
    Returns:
        Enhanced configuration manager instance
    """
    global _enhanced_config_manager
    if _enhanced_config_manager is None:
        config_path = os.getenv("VPN_SOURCES_CONFIG", DEFAULT_CONFIG_PATH)
        _enhanced_config_manager = EnhancedConfigurationManager(config_path)
    return _enhanced_config_manager


def reset_enhanced_config_manager() -> None:
    """Reset the global enhanced configuration manager instance."""
    global _enhanced_config_manager
    _enhanced_config_manager = None
    logger.debug("Enhanced configuration manager instance reset")
