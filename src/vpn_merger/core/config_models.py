"""
Config data models for the Enhanced Configuration Manager.

Separated from the manager to keep responsibilities clean and files compact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SourceValidationConfig:
    """Configuration for source validation."""

    min_configs: int = 10
    max_response_time: int = 30
    required_protocols: List[str] = field(default_factory=lambda: ["vmess"])
    ssl_required: bool = False
    content_validation: str = "basic"  # strict, moderate, basic


@dataclass
class SourceMonitoringConfig:
    """Configuration for source monitoring."""

    health_check_interval: int = 3600
    failure_threshold: int = 5
    alert_on_downtime: bool = False


@dataclass
class SourceConfig:
    """Configuration for a single source."""

    url: str
    weight: float = 1.0
    protocols: List[str] = field(default_factory=list)
    expected_configs: int = 100
    format: str = "raw"
    region: str = "global"
    maintainer: str = "unknown"
    source_type: str = "unknown"
    validation: Optional[SourceValidationConfig] = None
    monitoring: Optional[SourceMonitoringConfig] = None


@dataclass
class ProcessingConfig:
    """Configuration for processing settings."""

    concurrent_limit: int = 100
    timeout: int = 30
    batch_size: int = 20
    max_retries: int = 3
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    rate_limiting: Dict[str, Any] = field(default_factory=dict)
    memory_management: Dict[str, Any] = field(default_factory=dict)
    caching: Dict[str, Any] = field(default_factory=dict)
    deduplication: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityConfig:
    """Configuration for quality settings."""

    min_score: float = 0.5
    scoring_weights: Dict[str, float] = field(default_factory=dict)
    deduplication: bool = True
    protocol_validation: str = "strict"
    content_validation: Dict[str, Any] = field(default_factory=dict)
    source_filtering: Dict[str, Any] = field(default_factory=dict)
    quality_thresholds: Dict[str, float] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    """Configuration for monitoring settings."""

    metrics_enabled: bool = True
    health_check_interval: int = 60
    metrics_collection_interval: int = 30
    alert_thresholds: Dict[str, float] = field(default_factory=dict)
    alert_channels: List[Dict[str, Any]] = field(default_factory=list)
    logging: Dict[str, Any] = field(default_factory=dict)
    performance_monitoring: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityConfig:
    """Configuration for security settings."""

    ssl_validation: Dict[str, Any] = field(default_factory=dict)
    content_security: Dict[str, Any] = field(default_factory=dict)
    access_control: Dict[str, Any] = field(default_factory=dict)
    threat_detection: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OutputConfig:
    """Configuration for output settings."""

    directory: str = "output"
    formats: Dict[str, bool] = field(default_factory=dict)
    compression: Dict[str, Any] = field(default_factory=dict)
    file_management: Dict[str, Any] = field(default_factory=dict)
    quality_control: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnhancedConfig:
    """Enhanced configuration container."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    sources: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

