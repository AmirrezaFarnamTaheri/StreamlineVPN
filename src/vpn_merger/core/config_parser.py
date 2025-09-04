"""
Parser and defaults for EnhancedConfig.

Split out from the manager to improve modularity and testability.
"""

from __future__ import annotations

from typing import Any, Dict

from .config_models import (
    EnhancedConfig,
    ProcessingConfig,
    QualityConfig,
    MonitoringConfig,
    SecurityConfig,
    OutputConfig,
)

DEFAULT_CONCURRENT_LIMIT = 100
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3


def parse_enhanced_config(config_data: Dict[str, Any]) -> EnhancedConfig:
    """Parse configuration data into structured objects."""
    metadata = config_data.get("metadata", {})
    sources = config_data.get("sources", {})
    settings = config_data.get("settings", {})

    processing_data = settings.get("processing", {})
    processing = ProcessingConfig(
        concurrent_limit=processing_data.get("concurrent_limit", DEFAULT_CONCURRENT_LIMIT),
        timeout=processing_data.get("timeout", DEFAULT_TIMEOUT),
        batch_size=processing_data.get("batch_size", 20),
        max_retries=processing_data.get("max_retries", DEFAULT_MAX_RETRIES),
        retry_policy=processing_data.get("retry_policy", {}),
        rate_limiting=processing_data.get("rate_limiting", {}),
        memory_management=processing_data.get("memory_management", {}),
        caching=processing_data.get("caching", {}),
        deduplication=processing_data.get("deduplication", {}),
    )

    quality_data = settings.get("quality", {})
    quality = QualityConfig(
        min_score=quality_data.get("min_score", 0.5),
        scoring_weights=quality_data.get("scoring_weights", {}),
        deduplication=quality_data.get("deduplication", True),
        protocol_validation=quality_data.get("protocol_validation", "strict"),
        content_validation=quality_data.get("content_validation", {}),
        source_filtering=quality_data.get("source_filtering", {}),
        quality_thresholds=quality_data.get("quality_thresholds", {}),
    )

    monitoring_data = settings.get("monitoring", {})
    monitoring = MonitoringConfig(
        metrics_enabled=monitoring_data.get("metrics_enabled", True),
        health_check_interval=monitoring_data.get("health_check_interval", 60),
        metrics_collection_interval=monitoring_data.get("metrics_collection_interval", 30),
        alert_thresholds=monitoring_data.get("alert_thresholds", {}),
        alert_channels=monitoring_data.get("alert_channels", []),
        logging=monitoring_data.get("logging", {}),
        performance_monitoring=monitoring_data.get("performance_monitoring", {}),
    )

    security_data = settings.get("security", {})
    security = SecurityConfig(
        ssl_validation=security_data.get("ssl_validation", {}),
        content_security=security_data.get("content_security", {}),
        access_control=security_data.get("access_control", {}),
        threat_detection=security_data.get("threat_detection", {}),
    )

    output_data = settings.get("output", {})
    output = OutputConfig(
        directory=output_data.get("directory", "output"),
        formats=output_data.get("formats", {}),
        compression=output_data.get("compression", {}),
        file_management=output_data.get("file_management", {}),
        quality_control=output_data.get("quality_control", {}),
    )

    return EnhancedConfig(
        metadata=metadata,
        sources=sources,
        settings=settings,
        processing=processing,
        quality=quality,
        monitoring=monitoring,
        security=security,
        output=output,
    )


def get_default_enhanced_config() -> EnhancedConfig:
    """Default EnhancedConfig instance for safe fallbacks."""
    return EnhancedConfig(
        metadata={
            "version": "3.0.0",
            "description": "Default enhanced configuration",
            "last_updated": "2024-12-29",
        },
        sources={},
        settings={},
        processing=ProcessingConfig(),
        quality=QualityConfig(),
        monitoring=MonitoringConfig(),
        security=SecurityConfig(),
        output=OutputConfig(),
    )

