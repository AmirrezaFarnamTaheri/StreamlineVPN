---
title: Advanced Configuration Guide
---

This page documents configuration keys supported by StreamlineVPN’s validator and processing engine.

## Sections

- `sources`: required; tiers and URL lists
- `processing`: concurrency and retry settings
- `output`: formats selection
- `cache`: TTLs
- `security`: reserved for future policy tuning
- `monitoring`: basic enablement fields

## Example

```yaml
sources:
  premium:
    urls:
      - https://test-server.example/a.txt
      - { url: https://test-server.example/b.txt, weight: 0.9, protocols: [vmess, vless] }
  tier_1:
    - https://test-server.example/c.txt

processing:
  max_concurrent: 50     # 1..1000 (validator warns outside 1..1000)
  timeout: 30            # seconds
  retry_attempts: 3      # 0..10
  retry_delay: 1         # seconds
  batch_size: 20         # 1..100

output:
  formats: [json, clash, singbox]  # allowed: raw, base64, json, csv, yaml, clash, singbox

cache:
  ttl: 300               # seconds, >= 0

monitoring:
  enabled: true
```

## Deprecated fields

- `vpn_sources` → `sources`
- `output_directory` → manage output via CLI args and `output` dir
- `enable_cache` → `cache.enabled`

The validator reports deprecation warnings and issues where applicable.

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
from streamline_vpn.core import validate_config_file, ValidationResult

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
from streamline_vpn.core import ConfigurationValidator

validator = ConfigurationValidator()
result = validator.validate_config_file("config/sources.enhanced.yaml")

# Check specific validation results
if result.errors:
    print(f"Found {len(result.errors)} errors")
if result.warnings:
    print(f"Found {len(result.warnings)} warnings")
```

## Usage

- Define source tiers and URLs under `sources`.
- Tune `processing`, `output`, and `cache` based on your environment.
- Validate your YAML using the built‑in validator:

```python
from streamline_vpn.core.config_validator import validate_config_file

res = validate_config_file("config/sources.yaml")
print("valid:", res["valid"], "errors:", len(res["errors"]))
```

## Migration Guide

### Migration Tips

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
   from streamline_vpn.core import get_config_manager
   config_manager = get_config_manager()
   
   # New way
   from streamline_vpn.core import get_enhanced_config_manager
   config_manager = get_enhanced_config_manager()
   ```

4. **Validate Configuration**
   ```python
   from streamline_vpn.core import validate_config_file
   
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
    
    # Save configuration
    with open(new_config_path, 'w') as f:
        yaml.dump(enhanced_config, f, default_flow_style=False, indent=2)
    
    print(f"Configuration migrated from {old_config_path} to {new_config_path}")

if __name__ == "__main__":
    migrate_config("config/sources.yaml", "config/sources.yaml")
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
4. **Logging**: Enable logging
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
from streamline_vpn.core.config_validator import validate_config_file

res = validate_config_file("config/sources.yaml")
print("valid:", res["valid"]) 
```

This enhanced configuration system provides a robust foundation for managing VPN subscription sources with advanced features for processing, quality control, monitoring, and security.
