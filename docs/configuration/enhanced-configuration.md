# Enhanced Configuration System

## Overview

The Enhanced Configuration System provides advanced YAML structure with comprehensive settings for processing, quality controls, monitoring, and security. This system replaces the basic configuration with a more robust and feature-rich approach.

## Table of Contents

- [Configuration Structure](#configuration-structure)
- [Enhanced YAML Format](#enhanced-yaml-format)
- [Processing Settings](#processing-settings)
- [Quality Configuration](#quality-configuration)
- [Monitoring Configuration](#monitoring-configuration)
- [Security Configuration](#security-configuration)
- [Output Configuration](#output-configuration)
- [Configuration Validation](#configuration-validation)
- [Usage Examples](#usage-examples)
- [Migration Guide](#migration-guide)

## Configuration Structure

### Enhanced YAML Format

The enhanced configuration uses a structured YAML format with the following top-level sections:

```yaml
metadata:
  version: "3.0.0"
  description: "Enhanced VPN subscription sources"
  last_updated: "2024-12-29"
  maintainer: "vpn-merger-team"

sources:
  tier_1_premium:
    description: "High-quality, reliable sources"
    reliability_score: 0.95
    priority: 1
    urls:
      - url: "https://example.com/sources.txt"
        weight: 1.0
        protocols: ["vmess", "vless"]
        expected_configs: 500
        validation:
          min_configs: 100
          max_response_time: 5
          required_protocols: ["vmess"]
        monitoring:
          health_check_interval: 300
          failure_threshold: 2

settings:
  processing:
    concurrent_limit: 100
    timeout: 30
    retry_policy:
      max_retries: 3
      backoff_factor: 2
  quality:
    min_score: 0.5
    deduplication: true
    protocol_validation: strict
  monitoring:
    metrics_enabled: true
    health_check_interval: 60
    alert_thresholds:
      error_rate: 0.1
      response_time: 10
```

## Processing Settings

### Concurrent Processing

```yaml
processing:
  concurrent_limit: 100        # Maximum concurrent requests
  timeout: 30                  # Request timeout in seconds
  batch_size: 20               # Batch processing size
  max_retries: 3               # Maximum retry attempts
```

### Retry Policy

```yaml
retry_policy:
  max_retries: 3
  backoff_factor: 2
  backoff_max: 60
  retry_on_errors: ["timeout", "connection_error", "server_error"]
```

### Rate Limiting

```yaml
rate_limiting:
  enabled: true
  requests_per_minute: 60
  burst_limit: 10
  per_host_limit: 20
```

### Memory Management

```yaml
memory_management:
  max_memory_usage: "2GB"
  cleanup_interval: 300
  garbage_collection_threshold: 0.8
```

### Caching

```yaml
caching:
  enabled: true
  cache_size: 1000
  cache_ttl: 3600
  cache_backend: "memory"  # memory, redis, file
```

### Deduplication

```yaml
deduplication:
  enabled: true
  method: "bloom_filter"  # bloom_filter, hash_set, content_hash
  bloom_filter_size: 1000000
  hash_set_max_size: 100000
```

## Quality Configuration

### Quality Scoring

```yaml
quality:
  min_score: 0.5
  scoring_weights:
    historical_reliability: 0.25
    ssl_certificate: 0.15
    response_time: 0.15
    content_quality: 0.20
    protocol_diversity: 0.15
    uptime_consistency: 0.10
```

### Protocol Validation

```yaml
protocol_validation: "strict"  # strict, moderate, basic
```

### Content Validation

```yaml
content_validation:
  enabled: true
  min_length: 10
  max_length: 10000
  allowed_chars: "a-zA-Z0-9:/?=&._-"
  suspicious_patterns:
    - ".*\\.xyz$"
    - ".*\\.tk$"
    - ".*\\.ml$"
```

### Source Filtering

```yaml
source_filtering:
  enabled: true
  min_configs: 10
  max_response_time: 30
  required_protocols: ["vmess"]
  blocked_domains:
    - "malicious.com"
    - "spam.com"
    - "fake-vpn.com"
```

### Quality Thresholds

```yaml
quality_thresholds:
  excellent: 0.8
  good: 0.6
  fair: 0.4
  poor: 0.0
```

## Monitoring Configuration

### Metrics Collection

```yaml
monitoring:
  metrics_enabled: true
  health_check_interval: 60
  metrics_collection_interval: 30
```

### Alert Thresholds

```yaml
alert_thresholds:
  error_rate: 0.1
  response_time: 10
  memory_usage: 0.8
  disk_usage: 0.9
  cpu_usage: 0.8
```

### Alert Channels

```yaml
alert_channels:
  - type: "webhook"
    url: "${ALERT_WEBHOOK}"
    enabled: true
    severity: ["critical", "warning"]
  - type: "email"
    recipients: ["${ALERT_EMAIL}"]
    enabled: true
    severity: ["critical"]
  - type: "slack"
    channel: "${SLACK_CHANNEL}"
    enabled: true
    severity: ["critical", "warning", "info"]
```

### Logging Configuration

```yaml
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  handlers:
    - console
    - file
    - syslog
  file_rotation:
    enabled: true
    max_size: "100MB"
    backup_count: 5
```

### Performance Monitoring

```yaml
performance_monitoring:
  enabled: true
  cpu_monitoring: true
  memory_monitoring: true
  disk_monitoring: true
  network_monitoring: true
  custom_metrics:
    - "sources_processed_per_second"
    - "configs_generated_per_minute"
    - "average_response_time"
    - "error_rate_by_source"
```

## Security Configuration

### SSL Validation

```yaml
security:
  ssl_validation:
    enabled: true
    verify_certificates: true
    check_hostname: true
    allowed_ciphers: ["TLS_AES_256_GCM_SHA384", "TLS_CHACHA20_POLY1305_SHA256"]
```

### Content Security

```yaml
content_security:
  enabled: true
  max_content_size: "10MB"
  allowed_content_types: ["text/plain", "application/json", "application/x-yaml"]
  scan_for_malware: false
  content_sandboxing: false
```

### Access Control

```yaml
access_control:
  enabled: false
  allowed_ips: []
  blocked_ips: []
  rate_limiting_per_ip: 100
```

### Threat Detection

```yaml
threat_detection:
  enabled: true
  suspicious_domains: true
  content_analysis: true
  behavioral_analysis: false
```

## Output Configuration

### File Formats

```yaml
output:
  directory: "output"
  formats:
    raw: true
    base64: true
    csv: true
    json: true
    yaml: true
    clash: true
    singbox: true
```

### Compression

```yaml
compression:
  enabled: true
  algorithm: "gzip"
  level: 6
```

### File Management

```yaml
file_management:
  max_files: 100
  cleanup_old_files: true
  retention_days: 30
  backup_enabled: true
  backup_interval: "daily"
```

### Quality Control

```yaml
quality_control:
  validate_output: true
  min_configs_per_file: 1
  max_configs_per_file: 100000
  deduplicate_output: true
```

## Configuration Validation

### Using the Configuration Validator

```python
from vpn_merger.core import validate_config_file, ValidationResult

# Validate configuration file
result = validate_config_file("config/sources.enhanced.yaml")

if result.is_valid:
    print("Configuration is valid")
else:
    print("Configuration has errors:")
    for error in result.errors:
        print(f"  {error.field}: {error.message}")
        
    print("Warnings:")
    for warning in result.warnings:
        print(f"  {warning.field}: {warning.message}")
```

### Validation Rules

The configuration validator checks:

- **Structure**: Required sections and proper nesting
- **Types**: Correct data types for all fields
- **Ranges**: Valid ranges for numeric values
- **Enums**: Valid values for enumerated fields
- **URLs**: Proper URL format and length
- **Protocols**: Valid VPN protocol names
- **Regions**: Valid geographic region codes
- **Formats**: Valid output format names

### Custom Validation

```python
from vpn_merger.core import ConfigurationValidator

validator = ConfigurationValidator()
result = validator.validate_config_file("config/sources.enhanced.yaml")

# Check specific validation results
if result.errors:
    print(f"Found {len(result.errors)} errors")
if result.warnings:
    print(f"Found {len(result.warnings)} warnings")
```

## Usage Examples

### Basic Configuration Loading

```python
from vpn_merger.core import get_enhanced_config_manager

# Get enhanced configuration manager
config_manager = get_enhanced_config_manager()

# Get processing settings
concurrent_limit = config_manager.get_concurrent_limit()
timeout = config_manager.get_timeout()
max_retries = config_manager.get_max_retries()

# Get quality settings
min_quality = config_manager.get_min_quality_score()
quality_weights = config_manager.get_quality_weights()

# Get monitoring settings
metrics_enabled = config_manager.is_metrics_enabled()
health_interval = config_manager.get_health_check_interval()
```

### Advanced Configuration Usage

```python
from vpn_merger.core import EnhancedConfigurationManager

# Initialize with custom config path
config_manager = EnhancedConfigurationManager("config/sources.enhanced.yaml")

# Get processing configuration
processing_config = config_manager.get_processing_config()
print(f"Concurrent limit: {processing_config.concurrent_limit}")
print(f"Timeout: {processing_config.timeout}")
print(f"Batch size: {processing_config.batch_size}")

# Get quality configuration
quality_config = config_manager.get_quality_config()
print(f"Min score: {quality_config.min_score}")
print(f"Deduplication: {quality_config.deduplication}")
print(f"Protocol validation: {quality_config.protocol_validation}")

# Get monitoring configuration
monitoring_config = config_manager.get_monitoring_config()
print(f"Metrics enabled: {monitoring_config.metrics_enabled}")
print(f"Health check interval: {monitoring_config.health_check_interval}")

# Get security configuration
security_config = config_manager.get_security_config()
print(f"SSL validation: {security_config.ssl_validation}")

# Get output configuration
output_config = config_manager.get_output_config()
print(f"Output directory: {output_config.directory}")
print(f"Output formats: {output_config.formats}")
```

### Configuration Validation

```python
from vpn_merger.core import validate_config_file, validate_config_data

# Validate configuration file
result = validate_config_file("config/sources.enhanced.yaml")

if result.is_valid:
    print("✅ Configuration is valid")
else:
    print("❌ Configuration has errors:")
    for error in result.errors:
        print(f"  Error: {error.field} - {error.message}")
        
    if result.warnings:
        print("⚠️  Warnings:")
        for warning in result.warnings:
            print(f"  Warning: {warning.field} - {warning.message}")

# Validate configuration data
config_data = {
    "sources": {
        "tier_1_premium": {
            "urls": [
                {
                    "url": "https://example.com/sources.txt",
                    "weight": 1.0,
                    "protocols": ["vmess", "vless"]
                }
            ]
        }
    },
    "settings": {
        "processing": {
            "concurrent_limit": 100,
            "timeout": 30
        }
    }
}

result = validate_config_data(config_data)
print(f"Configuration data is valid: {result.is_valid}")
```

### Environment Variable Integration

```python
import os
from vpn_merger.core import get_enhanced_config_manager

# Set environment variables
os.environ["VPN_SOURCES_CONFIG"] = "config/sources.enhanced.yaml"
os.environ["VPN_CONCURRENT_LIMIT"] = "150"
os.environ["VPN_TIMEOUT"] = "45"
os.environ["VPN_ALERT_WEBHOOK"] = "https://hooks.slack.com/..."
os.environ["VPN_ALERT_EMAIL"] = "admin@example.com"

# Configuration manager will use environment variables
config_manager = get_enhanced_config_manager()

# Get configuration summary
summary = config_manager.get_config_summary()
print("Configuration Summary:")
for key, value in summary.items():
    print(f"  {key}: {value}")
```

## Migration Guide

### From Basic to Enhanced Configuration

1. **Update Configuration File**
   ```yaml
   # Old format
   sources:
     tier_1_premium:
       - "https://example1.com"
       - "https://example2.com"
   
   # New format
   sources:
     tier_1_premium:
       description: "High-quality sources"
       reliability_score: 0.95
       priority: 1
       urls:
         - url: "https://example1.com"
           weight: 1.0
           protocols: ["vmess", "vless"]
           expected_configs: 500
   ```

2. **Add Settings Section**
   ```yaml
   settings:
     processing:
       concurrent_limit: 100
       timeout: 30
       max_retries: 3
     quality:
       min_score: 0.5
       deduplication: true
     monitoring:
       metrics_enabled: true
       health_check_interval: 60
   ```

3. **Update Code Usage**
   ```python
   # Old way
   from vpn_merger.core import get_config_manager
   config_manager = get_config_manager()
   
   # New way
   from vpn_merger.core import get_enhanced_config_manager
   config_manager = get_enhanced_config_manager()
   ```

4. **Validate Configuration**
   ```python
   from vpn_merger.core import validate_config_file
   
   result = validate_config_file("config/sources.enhanced.yaml")
   if not result.is_valid:
       print("Configuration validation failed")
       for error in result.errors:
           print(f"Error: {error.message}")
   ```

### Configuration Migration Script

```python
#!/usr/bin/env python3
"""
Configuration Migration Script
==============================

Migrates basic configuration to enhanced configuration format.
"""

import yaml
from pathlib import Path

def migrate_config(old_config_path: str, new_config_path: str):
    """Migrate configuration from basic to enhanced format."""
    
    # Load old configuration
    with open(old_config_path, 'r') as f:
        old_config = yaml.safe_load(f)
    
    # Create enhanced configuration structure
    enhanced_config = {
        "metadata": {
            "version": "3.0.0",
            "description": "Migrated from basic configuration",
            "last_updated": "2024-12-29",
            "maintainer": "vpn-merger-team"
        },
        "sources": {},
        "settings": {
            "processing": {
                "concurrent_limit": 100,
                "timeout": 30,
                "max_retries": 3,
                "batch_size": 20
            },
            "quality": {
                "min_score": 0.5,
                "deduplication": True,
                "protocol_validation": "strict"
            },
            "monitoring": {
                "metrics_enabled": True,
                "health_check_interval": 60
            },
            "security": {
                "ssl_validation": {
                    "enabled": True
                }
            },
            "output": {
                "directory": "output",
                "formats": {
                    "raw": True,
                    "base64": True,
                    "csv": True,
                    "json": True
                }
            }
        }
    }
    
    # Migrate sources
    if "sources" in old_config:
        for tier_name, urls in old_config["sources"].items():
            if isinstance(urls, list):
                enhanced_config["sources"][tier_name] = {
                    "description": f"Migrated {tier_name} sources",
                    "reliability_score": 0.8,
                    "priority": 1,
                    "urls": []
                }
                
                for url in urls:
                    enhanced_config["sources"][tier_name]["urls"].append({
                        "url": url,
                        "weight": 1.0,
                        "protocols": ["vmess", "vless"],
                        "expected_configs": 100,
                        "format": "raw",
                        "region": "global",
                        "maintainer": "unknown",
                        "source_type": "migrated"
                    })
    
    # Save enhanced configuration
    with open(new_config_path, 'w') as f:
        yaml.dump(enhanced_config, f, default_flow_style=False, indent=2)
    
    print(f"Configuration migrated from {old_config_path} to {new_config_path}")

if __name__ == "__main__":
    migrate_config("config/sources.unified.yaml", "config/sources.enhanced.yaml")
```

## Best Practices

### Configuration Organization

1. **Use Descriptive Names**: Choose clear, descriptive names for tiers and sources
2. **Set Appropriate Priorities**: Use priority values to control processing order
3. **Configure Validation**: Set appropriate validation rules for each source
4. **Enable Monitoring**: Configure monitoring for critical sources
5. **Set Quality Thresholds**: Define quality thresholds based on your requirements

### Performance Optimization

1. **Concurrent Limits**: Set appropriate concurrent limits based on system resources
2. **Timeout Values**: Configure timeouts based on network conditions
3. **Caching**: Enable caching for frequently accessed sources
4. **Deduplication**: Use efficient deduplication methods
5. **Memory Management**: Configure memory limits and cleanup intervals

### Security Considerations

1. **SSL Validation**: Enable SSL validation for all HTTPS sources
2. **Content Validation**: Configure content validation rules
3. **Access Control**: Implement access control for sensitive sources
4. **Threat Detection**: Enable threat detection features
5. **Rate Limiting**: Configure rate limiting to prevent abuse

### Monitoring and Alerting

1. **Health Checks**: Configure health check intervals for all sources
2. **Alert Thresholds**: Set appropriate alert thresholds
3. **Multiple Channels**: Configure multiple alert channels for redundancy
4. **Logging**: Enable comprehensive logging
5. **Performance Monitoring**: Monitor system performance metrics

## Troubleshooting

### Common Issues

1. **Configuration Validation Errors**
   - Check YAML syntax
   - Verify required fields
   - Validate data types and ranges

2. **Performance Issues**
   - Adjust concurrent limits
   - Increase timeout values
   - Enable caching

3. **Memory Issues**
   - Reduce cache size
   - Enable garbage collection
   - Increase cleanup intervals

4. **Network Issues**
   - Check timeout values
   - Verify SSL certificates
   - Test source accessibility

### Debug Configuration

```python
from vpn_merger.core import get_enhanced_config_manager

# Get configuration manager
config_manager = get_enhanced_config_manager()

# Get configuration summary
summary = config_manager.get_config_summary()
print("Configuration Summary:")
for key, value in summary.items():
    print(f"  {key}: {value}")

# Validate configuration
if config_manager.validate_config():
    print("✅ Configuration is valid")
else:
    print("❌ Configuration validation failed")
```

This enhanced configuration system provides a robust foundation for managing VPN subscription sources with advanced features for processing, quality control, monitoring, and security.
