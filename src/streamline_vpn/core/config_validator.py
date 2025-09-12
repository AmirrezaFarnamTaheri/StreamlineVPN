"""
Enhanced Configuration Validator
=================================

Validates and auto-fixes configuration files with comprehensive checks.
"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse


class ConfigurationValidator:
    """Enhanced configuration validator with auto-fix capabilities."""

    def __init__(self):
        self.validation_rules = {
            "sources": self._validate_sources,
            "processing": self._validate_processing,
            "output": self._validate_output,
            "cache": self._validate_cache,
            "security": self._validate_security,
            "monitoring": self._validate_monitoring,
        }

        self.auto_fix_rules = {
            "missing_sections": self._fix_missing_sections,
            "invalid_urls": self._fix_invalid_urls,
            "out_of_range_values": self._fix_out_of_range_values,
            "deprecated_fields": self._fix_deprecated_fields,
        }

        self.issues: List[Dict[str, Any]] = []
        self.fixes_applied: List[str] = []

    def validate_config_file(self, config_path: str) -> Dict[str, Any]:
        """Validate a configuration file."""
        path = Path(config_path)

        if not path.exists():
            return {
                "valid": False,
                "error": "FILE_NOT_FOUND",
                "message": f"Configuration file not found: {path}",
            }

        try:
            with open(path, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            return {
                "valid": False,
                "error": "YAML_PARSE_ERROR",
                "message": f"Failed to parse YAML: {exc}",
            }

        return self.validate_config(config)

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration dictionary."""
        self.issues = []

        # Check for required sections
        required_sections = ["sources"]
        for section in required_sections:
            if section not in config:
                self.issues.append(
                    {
                        "type": "MISSING_SECTION",
                        "section": section,
                        "severity": "error",
                        "message": f'Required section "{section}" is missing',
                    }
                )

        # Validate each section
        for section, validator in self.validation_rules.items():
            if section in config:
                validator(config[section], config)

        # Check for deprecated fields
        self._check_deprecated_fields(config)

        # Generate result
        return {
            "valid": not any(
                issue["severity"] == "error" for issue in self.issues
            ),
            "issues": self.issues,
            "warnings": [
                i for i in self.issues if i["severity"] == "warning"
            ],
            "errors": [i for i in self.issues if i["severity"] == "error"],
            "suggestions": self._generate_suggestions(config),
        }

    def _validate_sources(
        self, sources: Any, config: Dict[str, Any]
    ) -> None:
        """Validate sources section."""
        if not isinstance(sources, dict):
            self.issues.append(
                {
                    "type": "INVALID_TYPE",
                    "field": "sources",
                    "severity": "error",
                    "message": "Sources must be a dictionary of tiers",
                }
            )
            return

        valid_tiers = [
            "premium",
            "reliable",
            "bulk",
            "experimental",
            "community",
            "tier_1",
            "tier_2",
            "tier_3",
        ]

        for tier_name, tier_data in sources.items():
            # Check tier name
            if not any(valid in tier_name.lower() for valid in valid_tiers):
                self.issues.append(
                    {
                        "type": "UNKNOWN_TIER",
                        "field": f"sources.{tier_name}",
                        "severity": "warning",
                        "message": f"Unknown tier name: {tier_name}",
                    }
                )

            # Validate tier data
            if isinstance(tier_data, dict):
                self._validate_tier_dict(tier_name, tier_data)
            elif isinstance(tier_data, list):
                self._validate_tier_list(tier_name, tier_data)
            else:
                self.issues.append(
                    {
                        "type": "INVALID_TYPE",
                        "field": f"sources.{tier_name}",
                        "severity": "error",
                        "message": (
                            "Tier data must be a dictionary or list"
                        ),
                    }
                )

    def _validate_tier_dict(
        self, tier_name: str, tier_data: Dict[str, Any]
    ) -> None:
        """Validate tier dictionary format."""
        if "urls" in tier_data:
            urls = tier_data["urls"]
            if isinstance(urls, list):
                for i, url_item in enumerate(urls):
                    if isinstance(url_item, str):
                        self._validate_url(
                            url_item, f"sources.{tier_name}.urls[{i}]"
                        )
                    elif isinstance(url_item, dict):
                        if "url" in url_item:
                            self._validate_url(
                                url_item["url"],
                                f"sources.{tier_name}.urls[{i}].url",
                            )
                        self._validate_source_metadata(
                            url_item, f"sources.{tier_name}.urls[{i}]"
                        )

    def _validate_tier_list(
        self, tier_name: str, tier_data: List[Any]
    ) -> None:
        """Validate tier list format."""
        for i, url in enumerate(tier_data):
            if isinstance(url, str):
                self._validate_url(url, f"sources.{tier_name}[{i}]")
            else:
                self.issues.append(
                    {
                        "type": "INVALID_TYPE",
                        "field": f"sources.{tier_name}[{i}]",
                        "severity": "error",
                        "message": "URL must be a string",
                    }
                )

    def _validate_url(self, url: str, field: str) -> None:
        """Validate URL format."""
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                self.issues.append(
                    {
                        "type": "INVALID_URL",
                        "field": field,
                        "severity": "error",
                        "message": f"Invalid URL format: {url}",
                    }
                )
            elif result.scheme not in ["http", "https"]:
                self.issues.append(
                    {
                        "type": "INVALID_SCHEME",
                        "field": field,
                        "severity": "warning",
                        "message": (
                            f"URL scheme should be http or https: {url}"
                        ),
                    }
                )
        except Exception:
            self.issues.append(
                {
                    "type": "INVALID_URL",
                    "field": field,
                    "severity": "error",
                    "message": f"Cannot parse URL: {url}",
                }
            )

    def _validate_source_metadata(
        self, metadata: Dict[str, Any], field: str
    ) -> None:
        """Validate source metadata."""
        # Validate weight
        if "weight" in metadata:
            weight = metadata["weight"]
            if not isinstance(weight, (int, float)):
                self.issues.append(
                    {
                        "type": "INVALID_TYPE",
                        "field": f"{field}.weight",
                        "severity": "error",
                        "message": "Weight must be a number",
                    }
                )
            elif not (0 <= weight <= 1):
                self.issues.append(
                    {
                        "type": "OUT_OF_RANGE",
                        "field": f"{field}.weight",
                        "severity": "warning",
                        "message": "Weight should be between 0 and 1",
                    }
                )

        # Validate protocols
        if "protocols" in metadata:
            protocols = metadata["protocols"]
            if not isinstance(protocols, list):
                self.issues.append(
                    {
                        "type": "INVALID_TYPE",
                        "field": f"{field}.protocols",
                        "severity": "error",
                        "message": "Protocols must be a list",
                    }
                )
            else:
                valid_protocols = [
                    "vmess",
                    "vless",
                    "trojan",
                    "ss",
                    "ssr",
                    "hysteria",
                    "hysteria2",
                    "tuic",
                ]
                for protocol in protocols:
                    if protocol not in valid_protocols:
                        self.issues.append(
                            {
                                "type": "UNKNOWN_PROTOCOL",
                                "field": f"{field}.protocols",
                                "severity": "warning",
                                "message": f"Unknown protocol: {protocol}",
                            }
                        )

    def _validate_processing(
        self, processing: Any, config: Dict[str, Any]
    ) -> None:
        """Validate processing section."""
        if not isinstance(processing, dict):
            self.issues.append(
                {
                    "type": "INVALID_TYPE",
                    "field": "processing",
                    "severity": "error",
                    "message": "Processing must be a dictionary",
                }
            )
            return

        # Validate numeric fields
        numeric_fields = {
            "max_concurrent": (1, 1000),
            "timeout": (1, 300),
            "retry_attempts": (0, 10),
            "retry_delay": (0, 60),
            "batch_size": (1, 100),
        }

        for field, (min_val, max_val) in numeric_fields.items():
            if field in processing:
                value = processing[field]
                if not isinstance(value, (int, float)):
                    self.issues.append(
                        {
                            "type": "INVALID_TYPE",
                            "field": f"processing.{field}",
                            "severity": "error",
                            "message": f"{field} must be a number",
                        }
                    )
                elif not (min_val <= value <= max_val):
                    self.issues.append(
                        {
                            "type": "OUT_OF_RANGE",
                            "field": f"processing.{field}",
                            "severity": "warning",
                            "message": (
                                f"{field} should be between "
                                f"{min_val} and {max_val}"
                            ),
                        }
                    )

    def _validate_output(self, output: Any, config: Dict[str, Any]) -> None:
        """Validate output section."""
        if not isinstance(output, dict):
            return

        if "formats" in output:
            formats = output["formats"]
            if isinstance(formats, list):
                valid_formats = [
                    "raw",
                    "base64",
                    "json",
                    "csv",
                    "yaml",
                    "clash",
                    "singbox",
                ]
                for fmt in formats:
                    if fmt not in valid_formats:
                        self.issues.append(
                            {
                                "type": "UNKNOWN_FORMAT",
                                "field": "output.formats",
                                "severity": "warning",
                                "message": f"Unknown output format: {fmt}",
                            }
                        )

    def _validate_cache(self, cache: Any, config: Dict[str, Any]) -> None:
        """Validate cache section."""
        if not isinstance(cache, dict):
            return

        if "ttl" in cache:
            ttl = cache["ttl"]
            if not isinstance(ttl, (int, float)):
                self.issues.append(
                    {
                        "type": "INVALID_TYPE",
                        "field": "cache.ttl",
                        "severity": "error",
                        "message": "TTL must be a number",
                    }
                )
            elif ttl < 0:
                self.issues.append(
                    {
                        "type": "INVALID_VALUE",
                        "field": "cache.ttl",
                        "severity": "error",
                        "message": "TTL cannot be negative",
                    }
                )

    def _validate_security(
        self, security: Any, config: Dict[str, Any]
    ) -> None:
        """Validate security section."""
        if not isinstance(security, dict):
            return
        # Security validation will be implemented based on requirements

    def _validate_monitoring(
        self, monitoring: Any, config: Dict[str, Any]
    ) -> None:
        """Validate monitoring section."""
        if not isinstance(monitoring, dict):
            return
        # Monitoring validation will be implemented based on requirements

    def _check_deprecated_fields(self, config: Dict[str, Any]) -> None:
        """Check for deprecated fields."""
        deprecated_fields = {
            "vpn_sources": "sources",
            "output_directory": "output.directory",
            "enable_cache": "cache.enabled",
        }

        for old_field, new_field in deprecated_fields.items():
            if old_field in config:
                self.issues.append(
                    {
                        "type": "DEPRECATED_FIELD",
                        "field": old_field,
                        "severity": "warning",
                        "message": (
                            f'Field "{old_field}" is deprecated, '
                            f'use "{new_field}" instead'
                        ),
                    }
                )

    def _generate_suggestions(self, config: Dict[str, Any]) -> List[str]:
        """Generate configuration improvement suggestions."""
        suggestions: List[str] = []

        # Check for missing recommended sections
        recommended_sections = ["processing", "output", "cache", "monitoring"]
        for section in recommended_sections:
            if section not in config:
                suggestions.append(
                    f'Consider adding "{section}" section for better control'
                )

        # Check source count
        if "sources" in config:
            total_sources = sum(
                (
                    len(tier)
                    if isinstance(tier, list)
                    else len(tier.get("urls", []))
                )
                for tier in config["sources"].values()
            )
            if total_sources < 5:
                suggestions.append(
                    "Consider adding more sources for better coverage"
                )
            elif total_sources > 100:
                suggestions.append(
                    "Consider reducing sources to improve performance"
                )

        # Check for performance settings
        if "processing" in config:
            processing = config["processing"]
            if processing.get("max_concurrent", 50) > 100:
                suggestions.append(
                    "High concurrency may cause rate limiting issues"
                )

        return suggestions

    def auto_fix_config(
        self, config: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str]]:
        """Automatically fix common configuration issues."""
        self.fixes_applied = []
        fixed_config = json.loads(json.dumps(config))  # Deep copy

        for fix_name, fix_func in self.auto_fix_rules.items():
            fix_func(fixed_config)

        return fixed_config, self.fixes_applied

    def _fix_missing_sections(self, config: Dict[str, Any]) -> None:
        """Add missing required sections."""
        if "sources" not in config:
            config["sources"] = {"default": []}
            self.fixes_applied.append('Added missing "sources" section')

    def _fix_invalid_urls(self, config: Dict[str, Any]) -> None:
        """Fix invalid URLs where possible."""
        # URL validation and fixing will be implemented as needed

    def _fix_out_of_range_values(self, config: Dict[str, Any]) -> None:
        """Fix out-of-range values."""
        if "processing" in config:
            processing = config["processing"]
            if "max_concurrent" in processing:
                if processing["max_concurrent"] > 1000:
                    processing["max_concurrent"] = 100
                    self.fixes_applied.append("Reduced max_concurrent to 100")
                elif processing["max_concurrent"] < 1:
                    processing["max_concurrent"] = 50
                    self.fixes_applied.append(
                        "Increased max_concurrent to 50"
                    )

    def _fix_deprecated_fields(self, config: Dict[str, Any]) -> None:
        """Update deprecated fields."""
        if "vpn_sources" in config:
            config["sources"] = config.pop("vpn_sources")
            self.fixes_applied.append('Renamed "vpn_sources" to "sources"')


def validate_config_file(config_path: str) -> Dict[str, Any]:
    """Validate a configuration file path using the default validator."""
    validator = ConfigurationValidator()
    return validator.validate_config_file(config_path)


def validate_config_data(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration data using the default validator."""
    validator = ConfigurationValidator()
    return validator.validate_config(config)


def main() -> int:
    """CLI interface for configuration validation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate StreamlineVPN configuration"
    )
    parser.add_argument("config", help="Path to configuration file")
    parser.add_argument(
        "--fix", action="store_true", help="Auto-fix issues"
    )
    parser.add_argument(
        "--output", help="Output path for fixed configuration"
    )

    args = parser.parse_args()

    validator = ConfigurationValidator()

    # Load configuration
    with open(args.config, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    # Validate
    result = validator.validate_config(config)

    # Import logger for this CLI tool
    from ..utils.logging import get_logger
    logger = get_logger(__name__)
    
    status_icon = '✅' if result['valid'] else '❌'
    logger.info("=== Configuration Validation %s ===", status_icon)
    logger.info("Errors: %d", len(result['errors']))
    logger.info("Warnings: %d", len(result['warnings']))

    if result["errors"]:
        logger.error("=== Errors ===")
        for error in result["errors"]:
            logger.error("  [%s] %s: %s", error['type'], error['field'], error['message'])

    if result["warnings"]:
        logger.warning("=== Warnings ===")
        for warning in result["warnings"]:
            logger.warning("  [%s] %s: %s", warning['type'], warning['field'], warning['message'])

    if result["suggestions"]:
        logger.info("=== Suggestions ===")
        for suggestion in result["suggestions"]:
            logger.info("  • %s", suggestion)

    # Apply fixes if requested
    if args.fix:
        fixed_config, fixes = validator.auto_fix_config(config)

        if fixes:
            logger.info("=== Applied %d Fixes ===", len(fixes))
            for fix in fixes:
                logger.info("  • %s", fix)

            output_path = args.output or args.config.replace(
                ".yaml", "_fixed.yaml"
            )
            with open(output_path, "w", encoding="utf-8") as file:
                yaml.dump(fixed_config, file, default_flow_style=False)
            logger.info("Fixed configuration saved to: %s", output_path)

    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
