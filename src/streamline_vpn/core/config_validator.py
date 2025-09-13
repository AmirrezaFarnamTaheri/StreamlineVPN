"""
Fixed Configuration Validator
============================

Complete configuration validation with comprehensive error handling and validation rules.
"""

import json
import re
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import logging

logger = logging.getLogger(__name__)


class ConfigurationValidator:
    """Comprehensive configuration validator for StreamlineVPN."""

    SUPPORTED_PROTOCOLS = {
        'vless', 'vmess', 'trojan', 'shadowsocks', 'shadowsocksr', 'ss', 'ssr'
    }

    SUPPORTED_OUTPUT_FORMATS = {
        'json', 'yaml', 'clash', 'singbox', 'base64', 'csv'
    }

    def __init__(self):
        self.issues: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []

    def validate_config_file(self, config_path: str) -> Dict[str, Any]:
        """Validate configuration file and return detailed results."""
        self.issues.clear()
        self.warnings.clear()

        config_file = Path(config_path)

        # Check if file exists
        if not config_file.exists():
            return {
                'valid': False,
                'error': 'FILE_NOT_FOUND',
                'message': f'Configuration file not found: {config_path}',
                'issues': [],
                'warnings': []
            }

        # Check file permissions
        if not config_file.is_file():
            return {
                'valid': False,
                'error': 'INVALID_FILE_TYPE',
                'message': f'Path is not a file: {config_path}',
                'issues': [],
                'warnings': []
            }

        if not self._check_file_readable(config_file):
            return {
                'valid': False,
                'error': 'FILE_NOT_READABLE',
                'message': f'Cannot read file: {config_path}',
                'issues': [],
                'warnings': []
            }

        # Load and parse configuration
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Try YAML first, then JSON
            try:
                config = yaml.safe_load(content)
            except yaml.YAMLError as yaml_err:
                try:
                    config = json.loads(content)
                except json.JSONDecodeError as json_err:
                    return {
                        'valid': False,
                        'error': 'PARSE_ERROR',
                        'message': f'Failed to parse as YAML or JSON. YAML error: {yaml_err}, JSON error: {json_err}',
                        'issues': [],
                        'warnings': []
                    }

        except Exception as e:
            return {
                'valid': False,
                'error': 'READ_ERROR',
                'message': f'Error reading file: {e}',
                'issues': [],
                'warnings': []
            }

        # Validate the loaded configuration
        return self.validate_config(config)

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration data structure."""
        self.issues.clear()
        self.warnings.clear()

        if not isinstance(config, dict):
            self._add_issue('ROOT', 'INVALID_TYPE', 'Configuration must be a dictionary/object')
            return self._build_result()

        # Validate required sections
        self._validate_sources_section(config)
        self._validate_processing_section(config)
        self._validate_output_section(config)
        self._validate_security_section(config)
        self._validate_cache_section(config)

        return self._build_result()

    def _validate_sources_section(self, config: Dict[str, Any]) -> None:
        """Validate sources section."""
        if 'sources' not in config:
            self._add_issue('sources', 'MISSING_REQUIRED', 'Sources section is required')
            return

        sources = config['sources']
        if not isinstance(sources, dict):
            self._add_issue('sources', 'INVALID_TYPE', 'Sources must be a dictionary')
            return

        if not sources:
            self._add_warning('sources', 'EMPTY_SECTION', 'Sources section is empty')
            return

        # Validate each tier
        for tier_name, tier_data in sources.items():
            self._validate_source_tier(tier_name, tier_data)

    def _validate_source_tier(self, tier_name: str, tier_data: Any) -> None:
        """Validate a source tier."""
        tier_path = f'sources.{tier_name}'

        # Handle both list and dict formats
        if isinstance(tier_data, list):
            sources_list = tier_data
        elif isinstance(tier_data, dict):
            if 'urls' in tier_data:
                sources_list = tier_data['urls']
            else:
                self._add_issue(tier_path, 'MISSING_URLS', 'Tier dictionary must contain "urls" key')
                return
        else:
            self._add_issue(tier_path, 'INVALID_TYPE', 'Tier must be a list or dictionary with "urls" key')
            return

        if not isinstance(sources_list, list):
            self._add_issue(f'{tier_path}.urls', 'INVALID_TYPE', 'URLs must be a list')
            return

        if not sources_list:
            self._add_warning(tier_path, 'EMPTY_TIER', f'Tier "{tier_name}" has no sources')
            return

        # Validate each source in the tier
        for i, source in enumerate(sources_list):
            self._validate_source_entry(f'{tier_path}[{i}]', source)

    def _validate_source_entry(self, source_path: str, source: Any) -> None:
        """Validate a single source entry."""
        if isinstance(source, str):
            # Simple URL string
            self._validate_url(source_path, source)
        elif isinstance(source, dict):
            # Source object with metadata
            if 'url' not in source:
                self._add_issue(source_path, 'MISSING_URL', 'Source object must contain "url" field')
                return

            self._validate_url(f'{source_path}.url', source['url'])

            # Validate optional fields
            if 'weight' in source:
                self._validate_weight(f'{source_path}.weight', source['weight'])

            if 'protocols' in source:
                self._validate_protocols(f'{source_path}.protocols', source['protocols'])

            if 'timeout' in source:
                self._validate_timeout(f'{source_path}.timeout', source['timeout'])

            if 'headers' in source:
                self._validate_headers(f'{source_path}.headers', source['headers'])
        else:
            self._add_issue(source_path, 'INVALID_TYPE', 'Source must be a URL string or object')

    def _validate_url(self, field_path: str, url: Any) -> None:
        """Validate URL format."""
        if not isinstance(url, str):
            self._add_issue(field_path, 'INVALID_TYPE', 'URL must be a string')
            return

        if not url.strip():
            self._add_issue(field_path, 'EMPTY_VALUE', 'URL cannot be empty')
            return

        try:
            parsed = urlparse(url)
            if not parsed.scheme:
                self._add_issue(field_path, 'INVALID_URL', 'URL must include scheme (http/https)')
            elif parsed.scheme not in ['http', 'https']:
                self._add_warning(field_path, 'UNSUPPORTED_SCHEME', f'Unusual URL scheme: {parsed.scheme}')

            if not parsed.netloc:
                self._add_issue(field_path, 'INVALID_URL', 'URL must include hostname')

        except Exception as e:
            self._add_issue(field_path, 'INVALID_URL', f'Invalid URL format: {e}')

    def _validate_weight(self, field_path: str, weight: Any) -> None:
        """Validate source weight."""
        if not isinstance(weight, (int, float)):
            self._add_issue(field_path, 'INVALID_TYPE', 'Weight must be a number')
            return

        if weight < 0:
            self._add_issue(field_path, 'INVALID_VALUE', 'Weight cannot be negative')
        elif weight > 1.0:
            self._add_warning(field_path, 'OUT_OF_RANGE', 'Weight greater than 1.0 may cause unexpected behavior')

    def _validate_protocols(self, field_path: str, protocols: Any) -> None:
        """Validate protocol list."""
        if not isinstance(protocols, list):
            self._add_issue(field_path, 'INVALID_TYPE', 'Protocols must be a list')
            return

        for i, protocol in enumerate(protocols):
            if not isinstance(protocol, str):
                self._add_issue(f'{field_path}[{i}]', 'INVALID_TYPE', 'Protocol must be a string')
                continue

            if protocol.lower() not in self.SUPPORTED_PROTOCOLS:
                self._add_warning(f'{field_path}[{i}]', 'UNKNOWN_PROTOCOL', f'Unknown protocol: {protocol}')

    def _validate_timeout(self, field_path: str, timeout: Any) -> None:
        """Validate timeout value."""
        if not isinstance(timeout, (int, float)):
            self._add_issue(field_path, 'INVALID_TYPE', 'Timeout must be a number')
            return

        if timeout <= 0:
            self._add_issue(field_path, 'INVALID_VALUE', 'Timeout must be positive')
        elif timeout > 300:
            self._add_warning(field_path, 'HIGH_VALUE', 'Timeout greater than 300 seconds may cause delays')

    def _validate_headers(self, field_path: str, headers: Any) -> None:
        """Validate HTTP headers."""
        if not isinstance(headers, dict):
            self._add_issue(field_path, 'INVALID_TYPE', 'Headers must be a dictionary')
            return

        for key, value in headers.items():
            if not isinstance(key, str):
                self._add_issue(f'{field_path}.{key}', 'INVALID_TYPE', 'Header name must be a string')
            if not isinstance(value, str):
                self._add_issue(f'{field_path}.{key}', 'INVALID_TYPE', 'Header value must be a string')

    def _validate_processing_section(self, config: Dict[str, Any]) -> None:
        """Validate processing configuration."""
        if 'processing' not in config:
            return  # Optional section

        processing = config['processing']
        if not isinstance(processing, dict):
            self._add_issue('processing', 'INVALID_TYPE', 'Processing section must be a dictionary')
            return

        # Validate specific processing options
        if 'max_concurrent' in processing:
            max_concurrent = processing['max_concurrent']
            if not isinstance(max_concurrent, int):
                self._add_issue('processing.max_concurrent', 'INVALID_TYPE', 'max_concurrent must be an integer')
            elif max_concurrent < 1:
                self._add_issue('processing.max_concurrent', 'INVALID_VALUE', 'max_concurrent must be at least 1')
            elif max_concurrent > 1000:
                self._add_warning('processing.max_concurrent', 'HIGH_VALUE', 'Very high concurrency may cause performance issues')

        if 'timeout' in processing:
            self._validate_timeout('processing.timeout', processing['timeout'])

        if 'retry_attempts' in processing:
            retry_attempts = processing['retry_attempts']
            if not isinstance(retry_attempts, int):
                self._add_issue('processing.retry_attempts', 'INVALID_TYPE', 'retry_attempts must be an integer')
            elif retry_attempts < 0:
                self._add_issue('processing.retry_attempts', 'INVALID_VALUE', 'retry_attempts cannot be negative')

    def _validate_output_section(self, config: Dict[str, Any]) -> None:
        """Validate output configuration."""
        if 'output' not in config:
            return  # Optional section

        output = config['output']
        if not isinstance(output, dict):
            self._add_issue('output', 'INVALID_TYPE', 'Output section must be a dictionary')
            return

        if 'formats' in output:
            formats = output['formats']
            if not isinstance(formats, list):
                self._add_issue('output.formats', 'INVALID_TYPE', 'Formats must be a list')
            else:
                for i, fmt in enumerate(formats):
                    if not isinstance(fmt, str):
                        self._add_issue(f'output.formats[{i}]', 'INVALID_TYPE', 'Format must be a string')
                    elif fmt.lower() not in self.SUPPORTED_OUTPUT_FORMATS:
                        self._add_warning(f'output.formats[{i}]', 'UNKNOWN_FORMAT', f'Unknown output format: {fmt}')

        if 'directory' in output:
            directory = output['directory']
            if not isinstance(directory, str):
                self._add_issue('output.directory', 'INVALID_TYPE', 'Output directory must be a string')
            elif not directory.strip():
                self._add_issue('output.directory', 'EMPTY_VALUE', 'Output directory cannot be empty')

    def _validate_security_section(self, config: Dict[str, Any]) -> None:
        """Validate security configuration."""
        if 'security' not in config:
            return  # Optional section

        security = config['security']
        if not isinstance(security, dict):
            self._add_issue('security', 'INVALID_TYPE', 'Security section must be a dictionary')
            return

        # Validate specific security options
        boolean_fields = ['enable_validation', 'strict_mode', 'allow_insecure']
        for field in boolean_fields:
            if field in security:
                if not isinstance(security[field], bool):
                    self._add_issue(f'security.{field}', 'INVALID_TYPE', f'{field} must be a boolean')

        if 'blacklist' in security:
            blacklist = security['blacklist']
            if not isinstance(blacklist, list):
                self._add_issue('security.blacklist', 'INVALID_TYPE', 'Blacklist must be a list')
            else:
                for i, item in enumerate(blacklist):
                    if not isinstance(item, str):
                        self._add_issue(f'security.blacklist[{i}]', 'INVALID_TYPE', 'Blacklist item must be a string')

    def _validate_cache_section(self, config: Dict[str, Any]) -> None:
        """Validate cache configuration."""
        if 'cache' not in config:
            return  # Optional section

        cache = config['cache']
        if not isinstance(cache, dict):
            self._add_issue('cache', 'INVALID_TYPE', 'Cache section must be a dictionary')
            return

        if 'enabled' in cache:
            if not isinstance(cache['enabled'], bool):
                self._add_issue('cache.enabled', 'INVALID_TYPE', 'Cache enabled must be a boolean')

        if 'ttl' in cache:
            ttl = cache['ttl']
            if not isinstance(ttl, int):
                self._add_issue('cache.ttl', 'INVALID_TYPE', 'Cache TTL must be an integer')
            elif ttl < 0:
                self._add_issue('cache.ttl', 'INVALID_VALUE', 'Cache TTL cannot be negative')

    def _check_file_readable(self, file_path: Path) -> bool:
        """Check if file is readable."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1)  # Try to read one character
            return True
        except Exception:
            return False

    def _add_issue(self, field: str, issue_type: str, message: str) -> None:
        """Add a validation issue."""
        self.issues.append({
            'field': field,
            'type': issue_type,
            'message': message,
            'severity': 'error'
        })

    def _add_warning(self, field: str, issue_type: str, message: str) -> None:
        """Add a validation warning."""
        self.warnings.append({
            'field': field,
            'type': issue_type,
            'message': message,
            'severity': 'warning'
        })

    def _build_result(self) -> Dict[str, Any]:
        """Build validation result."""
        return {
            'valid': len(self.issues) == 0,
            'issues': self.issues,
            'warnings': self.warnings,
            'summary': {
                'total_issues': len(self.issues),
                'total_warnings': len(self.warnings),
                'critical_issues': len([i for i in self.issues if i.get('severity') == 'error']),
                'has_errors': len(self.issues) > 0
            }
        }

    def fix_common_issues(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to fix common configuration issues."""
        fixed_config = json.loads(json.dumps(config))  # Deep copy

        # Ensure required sections exist
        if 'sources' not in fixed_config:
            fixed_config['sources'] = {}

        if 'processing' not in fixed_config:
            fixed_config['processing'] = {}

        # Set reasonable defaults
        if 'max_concurrent' not in fixed_config['processing']:
            fixed_config['processing']['max_concurrent'] = 100

        # Fix max_concurrent if it's out of range
        max_concurrent = fixed_config['processing'].get('max_concurrent')
        if isinstance(max_concurrent, int):
            if max_concurrent < 1:
                fixed_config['processing']['max_concurrent'] = 1
            elif max_concurrent > 1000:
                fixed_config['processing']['max_concurrent'] = 1000

        # Add default output section if missing
        if 'output' not in fixed_config:
            fixed_config['output'] = {
                'formats': ['json', 'clash'],
                'directory': 'output'
            }

        return fixed_config


# Convenience functions
def validate_config_file(config_path: str) -> Dict[str, Any]:
    """Validate a configuration file."""
    validator = ConfigurationValidator()
    return validator.validate_config_file(config_path)


def validate_config_data(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration data."""
    validator = ConfigurationValidator()
    return validator.validate_config(config)


def fix_config_issues(config: Dict[str, Any]) -> Dict[str, Any]:
    """Fix common configuration issues."""
    validator = ConfigurationValidator()
    return validator.fix_common_issues(config)


# Example usage
if __name__ == "__main__":
    # Test with a sample configuration
    sample_config = {
        "sources": {
            "tier_1": [
                "https://example.com/config1.txt",
                {
                    "url": "https://example.com/config2.txt",
                    "weight": 0.8,
                    "protocols": ["vless", "vmess"]
                }
            ]
        },
        "processing": {
            "max_concurrent": 50,
            "timeout": 30
        },
        "output": {
            "formats": ["json", "clash"],
            "directory": "output"
        }
    }

    validator = ConfigurationValidator()
    result = validator.validate_config(sample_config)

    print("Validation Result:")
    print(f"Valid: {result['valid']}")
    print(f"Issues: {len(result['issues'])}")
    print(f"Warnings: {len(result['warnings'])}")

    if result['issues']:
        print("\nIssues:")
        for issue in result['issues']:
            print(f"  - {issue['field']}: {issue['message']}")

    if result['warnings']:
        print("\nWarnings:")
        for warning in result['warnings']:
            print(f"  - {warning['field']}: {warning['message']}")
