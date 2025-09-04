"""
Configuration Validator
=======================

Validates VPN merger configuration files for structure and content.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)

# Validation constants
MAX_URL_LENGTH = 2048
MAX_CONCURRENT_LIMIT = 1000
MAX_TIMEOUT = 300
MAX_RETRIES = 10
VALID_PROTOCOLS = {
    "vmess", "vless", "trojan", "shadowsocks", "shadowsocksr",
    "http", "https", "socks", "socks5", "hysteria", "hysteria2",
    "tuic", "wireguard", "all"
}
VALID_REGIONS = {
    "global", "AS", "EU", "US", "AF", "OC", "SA", "NA", "ME"
}
VALID_FORMATS = {"raw", "base64", "json", "yaml", "xml"}
VALID_SOURCE_TYPES = {
    "aggregator", "community", "regional", "protocol_specific",
    "experimental", "specialized", "validated"
}


@dataclass
class ValidationError:
    """Represents a validation error."""
    field: str
    message: str
    severity: str = "error"  # error, warning, info


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.errors:
            self.is_valid = True


class ConfigurationValidator:
    """Validates VPN merger configuration files."""

    def __init__(self):
        """Initialize configuration validator."""
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def validate_config_file(self, config_path: Union[str, Path]) -> ValidationResult:
        """Validate a configuration file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Validation result with errors and warnings
        """
        self.errors.clear()
        self.warnings.clear()
        
        try:
            config_path = Path(config_path)
            if not config_path.exists():
                self.errors.append(ValidationError(
                    field="config_path",
                    message=f"Configuration file not found: {config_path}"
                ))
                return ValidationResult(False, self.errors, self.warnings)
            
            if yaml is None:
                self.errors.append(ValidationError(
                    field="dependencies",
                    message="PyYAML is required for configuration validation"
                ))
                return ValidationResult(False, self.errors, self.warnings)
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if not isinstance(config_data, dict):
                self.errors.append(ValidationError(
                    field="root",
                    message="Configuration must be a YAML dictionary"
                ))
                return ValidationResult(False, self.errors, self.warnings)
            
            self._validate_config_structure(config_data)
            
        except yaml.YAMLError as e:
            self.errors.append(ValidationError(
                field="yaml",
                message=f"Invalid YAML syntax: {e}"
            ))
        except Exception as e:
            self.errors.append(ValidationError(
                field="general",
                message=f"Error reading configuration: {e}"
            ))
        
        return ValidationResult(len(self.errors) == 0, self.errors, self.warnings)

    def _validate_config_structure(self, config_data: Dict[str, Any]) -> None:
        """Validate basic configuration structure.
        
        Args:
            config_data: Configuration data to validate
        """
        required_fields = ["metadata", "sources"]
        for field in required_fields:
            if field not in config_data:
                self.errors.append(ValidationError(
                    field=field,
                    message=f"Required field '{field}' is missing"
                ))
        
        # Validate metadata
        if "metadata" in config_data:
            self._validate_metadata(config_data["metadata"])
        
        # Validate sources
        if "sources" in config_data:
            self._validate_sources(config_data["sources"])

    def _validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """Validate metadata section.
        
        Args:
            metadata: Metadata configuration to validate
        """
        if not isinstance(metadata, dict):
            self.errors.append(ValidationError(
                field="metadata",
                message="Metadata must be a dictionary"
            ))
            return
        
        # Check for required metadata fields
        required_metadata = ["name", "version", "description"]
        for field in required_metadata:
            if field not in metadata:
                self.warnings.append(ValidationError(
                    field=f"metadata.{field}",
                    message=f"Recommended metadata field '{field}' is missing",
                    severity="warning"
                ))

    def _validate_sources(self, sources: Dict[str, Any]) -> None:
        """Validate sources section.
        
        Args:
            sources: Sources configuration to validate
        """
        if not isinstance(sources, dict):
            self.errors.append(ValidationError(
                field="sources",
                message="Sources must be a dictionary"
            ))
            return
        
        # Validate each source tier
        for tier_name, tier_config in sources.items():
            if isinstance(tier_config, dict):
                self._validate_source_tier(tier_name, tier_config)

    def _validate_source_tier(self, tier_name: str, tier_config: Dict[str, Any]) -> None:
        """Validate a source tier configuration.
        
        Args:
            tier_name: Name of the source tier
            tier_config: Tier configuration to validate
        """
        # Validate tier metadata
        if "metadata" in tier_config:
            metadata = tier_config["metadata"]
            if isinstance(metadata, dict):
                if "type" in metadata:
                    if metadata["type"] not in VALID_SOURCE_TYPES:
                        self.errors.append(ValidationError(
                            field=f"sources.{tier_name}.metadata.type",
                            message=f"Invalid source type: {metadata['type']}"
                        ))
        
        # Validate URLs
        if "urls" in tier_config:
            urls = tier_config["urls"]
            if isinstance(urls, list):
                for i, url_config in enumerate(urls):
                    if isinstance(url_config, dict):
                        self._validate_source_url(f"sources.{tier_name}.urls[{i}]", url_config)

    def _validate_source_url(self, field_path: str, url_config: Dict[str, Any]) -> None:
        """Validate a source URL configuration.
        
        Args:
            field_path: Path to the field being validated
            url_config: URL configuration to validate
        """
        # Validate URL
        if "url" in url_config:
            url = url_config["url"]
            if not isinstance(url, str):
                self.errors.append(ValidationError(
                    field=f"{field_path}.url",
                    message="URL must be a string"
                ))
            elif len(url) > MAX_URL_LENGTH:
                self.errors.append(ValidationError(
                    field=f"{field_path}.url",
                    message=f"URL too long (max {MAX_URL_LENGTH} characters)"
                ))
            elif not self._is_valid_url(url):
                self.errors.append(ValidationError(
                    field=f"{field_path}.url",
                    message="Invalid URL format"
                ))
        
        # Validate weight
        if "weight" in url_config:
            weight = url_config["weight"]
            if not isinstance(weight, (int, float)):
                self.errors.append(ValidationError(
                    field=f"{field_path}.weight",
                    message="Weight must be a number"
                ))
            elif weight < 0:
                self.errors.append(ValidationError(
                    field=f"{field_path}.weight",
                    message="Weight must be non-negative"
                ))
        
        # Validate protocols
        if "protocols" in url_config:
            protocols = url_config["protocols"]
            if isinstance(protocols, list):
                for protocol in protocols:
                    if protocol not in VALID_PROTOCOLS:
                        self.errors.append(ValidationError(
                            field=f"{field_path}.protocols",
                            message=f"Invalid protocol: {protocol}"
                        ))

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL has valid format.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL format is valid
        """
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(url))
