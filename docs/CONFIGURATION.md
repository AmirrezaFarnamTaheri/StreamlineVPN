# Configuration Guide

## Overview

The VPN Subscription Merger uses a unified configuration system to manage sources, settings, and behavior. All configuration is centralized in YAML format for easy management and version control.

## Configuration Files

### Main Configuration: `config/sources.unified.yaml`

This is the primary configuration file containing all VPN sources organized by tiers:

```yaml
sources:
  tier_1_premium:
    - "https://example1.com"
    - "https://example2.com"
  
  tier_2_reliable:
    - "https://example3.com"
    - "https://example4.com"
  
  tier_3_bulk:
    - "https://example5.com"
    - "https://example6.com"
  
  specialized:
    - "https://specialized1.com"
    - "https://specialized2.com"
  
  regional:
    - "https://regional1.com"
    - "https://regional2.com"
  
  experimental:
    - "https://experimental1.com"
    - "https://experimental2.com"
```

### Tier System

- **tier_1_premium**: High-quality, reliable sources (processed first)
- **tier_2_reliable**: Good quality sources with occasional issues
- **tier_3_bulk**: Large volume sources for comprehensive coverage
- **specialized**: Protocol-specific or niche sources
- **regional**: Geographic-specific sources
- **experimental**: New or testing sources

## Environment Variables

### Core Settings

```bash
# Source configuration
VPN_SOURCES_CONFIG=config/sources.unified.yaml

# Processing settings
VPN_CONCURRENT_LIMIT=50
VPN_TIMEOUT=30
VPN_MAX_RETRIES=3

# Output settings
VPN_OUTPUT_DIR=output
VPN_WRITE_BASE64=true
VPN_WRITE_CSV=true
VPN_WRITE_JSON=true
```

### Advanced Settings

```bash
# Performance tuning
VPN_CHUNK_SIZE=1048576  # 1MB
VPN_SEMAPHORE_LIMIT=20
VPN_BLOOM_FILTER_SIZE=1000000

# Logging
VPN_LOG_LEVEL=INFO
VPN_LOG_FILE=vpn_merger.log

# Testing
VPN_TEST_TIMEOUT=10
VPN_TEST_CONCURRENT=10
```

## Command Line Options

### Basic Usage

```bash
# Run with default configuration
python vpn_merger_main.py

# Validate sources only
python vpn_merger_main.py --validate

# Custom configuration file
python vpn_merger_main.py --config custom_sources.yaml
```

### Advanced Options

```bash
# Performance tuning
python vpn_merger_main.py --concurrent 100 --timeout 60

# Output control
python vpn_merger_main.py --no-base64 --no-csv --output-dir custom_output

# Protocol filtering
python vpn_merger_main.py --include-protocols vmess,vless --exclude-protocols shadowsocks
```

## Configuration Validation

### YAML Schema

The configuration file follows this schema:

```yaml
sources:
  tier_name:
    - "https://source1.com"
    - "https://source2.com"

settings:
  concurrent_limit: 50
  timeout: 30
  max_retries: 3
  chunk_size: 1048576

output:
  directory: "output"
  formats:
    - raw
    - base64
    - csv
    - json
```

### Validation Commands

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/sources.unified.yaml'))"

# Validate source accessibility
python vpn_merger_main.py --validate

# Check configuration
python -c "from vpn_merger import SourceManager; sources = SourceManager(); print(f'Loaded {len(sources.get_all_sources())} sources')"
```

## Source Management

### Adding New Sources

1. **Edit** `config/sources.unified.yaml`
2. **Add** URL to appropriate tier
3. **Test** with validation command
4. **Commit** changes to version control

### Source Categories

- **Premium**: High-speed, reliable sources
- **Reliable**: Good quality with occasional issues
- **Bulk**: Large volume for comprehensive coverage
- **Specialized**: Protocol-specific sources
- **Regional**: Geographic-specific sources
- **Experimental**: New or testing sources

### Source Validation

Sources are automatically validated for:
- URL accessibility
- Content availability
- Protocol detection
- Reliability scoring

## Performance Configuration

### Concurrency Settings

```yaml
performance:
  concurrent_limit: 50        # Max concurrent requests
  semaphore_limit: 20         # Max concurrent per host
  timeout: 30                 # Request timeout (seconds)
  max_retries: 3              # Retry attempts
  chunk_size: 1048576         # Processing chunk size
```

### Memory Management

```yaml
memory:
  bloom_filter_size: 1000000  # Deduplication filter size
  cache_size: 1000            # In-memory cache size
  max_configs: 1000000        # Max configs to process
```

## Output Configuration

### File Formats

```yaml
output:
  directory: "output"
  formats:
    raw: true                 # Raw text file
    base64: true              # Base64 encoded
    csv: true                 # CSV with metrics
    json: true                # JSON report
    clash: false              # Clash configuration
    singbox: false            # Sing-box configuration
```

### Output Files

- `vpn_subscription_raw.txt` - Raw configuration list
- `vpn_subscription_base64.txt` - Base64 encoded
- `vpn_detailed.csv` - CSV with performance metrics
- `vpn_report.json` - Comprehensive JSON report

## Security Configuration

### Access Control

```yaml
security:
  allowed_protocols:
    - vmess
    - vless
    - trojan
    - shadowsocks
    - hysteria
  
  blocked_domains:
    - "malicious.com"
    - "spam.com"
  
  rate_limiting:
    requests_per_minute: 100
    burst_limit: 20
```

### Threat Detection

```yaml
threat_detection:
  enabled: true
  suspicious_patterns:
    - ".*\\.xyz$"
    - ".*\\.tk$"
  
  content_validation:
    min_length: 10
    max_length: 10000
    allowed_chars: "a-zA-Z0-9:/?=&._-"
```

## Monitoring Configuration

### Logging

```yaml
logging:
  level: INFO
  file: vpn_merger.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  handlers:
    - console
    - file
    - syslog
```

### Metrics

```yaml
metrics:
  enabled: true
  prometheus: true
  statsd: false
  
  collection:
    - source_health
    - processing_time
    - config_quality
    - error_rates
```

## Troubleshooting

### Common Issues

1. **Configuration not loading**: Check YAML syntax and file permissions
2. **Sources not accessible**: Verify network connectivity and source availability
3. **Performance issues**: Adjust concurrency and timeout settings
4. **Memory problems**: Reduce bloom filter size and cache limits

### Debug Mode

```bash
# Enable debug logging
export VPN_LOG_LEVEL=DEBUG

# Run with verbose output
python vpn_merger_main.py --verbose

# Test individual components
python -c "from vpn_merger import SourceManager; sources = SourceManager(); print(sources.get_all_sources())"
```

## Best Practices

### Configuration Management

1. **Version Control**: Always commit configuration changes
2. **Backup**: Keep backup of working configurations
3. **Testing**: Validate changes before production deployment
4. **Documentation**: Document custom configurations

### Performance Optimization

1. **Tier Organization**: Use tier system for source prioritization
2. **Concurrency Tuning**: Adjust based on system resources
3. **Timeout Settings**: Balance between reliability and speed
4. **Memory Management**: Monitor and adjust memory settings

### Security

1. **Source Validation**: Regularly validate source accessibility
2. **Protocol Filtering**: Restrict to necessary protocols
3. **Rate Limiting**: Prevent abuse and resource exhaustion
4. **Content Validation**: Filter suspicious content

## Examples

### Minimal Configuration

```yaml
sources:
  tier_1_premium:
    - "https://reliable-source.com"
  
  tier_2_reliable:
    - "https://backup-source.com"
```

### Production Configuration

```yaml
sources:
  tier_1_premium:
    - "https://premium1.com"
    - "https://premium2.com"
  
  tier_2_reliable:
    - "https://reliable1.com"
    - "https://reliable2.com"
  
  tier_3_bulk:
    - "https://bulk1.com"
    - "https://bulk2.com"

settings:
  concurrent_limit: 100
  timeout: 60
  max_retries: 5

output:
  directory: "/var/vpn/output"
  formats:
    raw: true
    base64: true
    csv: true
    json: true

logging:
  level: INFO
  file: "/var/log/vpn_merger.log"
```

This configuration guide provides comprehensive information for setting up and managing the VPN Subscription Merger. For additional help, refer to the troubleshooting guide or create an issue in the project repository.
