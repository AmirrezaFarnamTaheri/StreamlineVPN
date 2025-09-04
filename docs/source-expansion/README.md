# Source Expansion Guide

## Overview

The VPN Merger system now includes comprehensive source expansion capabilities with additional source categories and enhanced validation strategies. This guide covers the new features, configuration options, and usage examples.

## Table of Contents

- [New Source Categories](#new-source-categories)
- [Enhanced Source Validation](#enhanced-source-validation)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Quality Scoring](#quality-scoring)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)

## New Source Categories

### 1. Community Maintained Sources

Community-maintained sources are actively developed and maintained by the open-source community.

```yaml
community_maintained:
  description: Community-maintained VPN sources with active development
  reliability_score: 0.8
  urls:
    - url: https://github.com/freefq/free
      maintainer: freefq
      update_frequency: daily
      protocols: [vmess, vless, trojan, shadowsocks]
```

**Features:**
- Active community development
- Regular updates
- Multiple protocol support
- High reliability scores

### 2. Aggregator Services

Professional aggregator services that collect and merge multiple sources.

```yaml
aggregator_services:
  description: Professional aggregator services that collect and merge multiple sources
  reliability_score: 0.9
  urls:
    - url: https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt
      maintainer: mahdibland
      update_frequency: hourly
      protocols: [all]
```

**Features:**
- Professional maintenance
- High-frequency updates
- Comprehensive protocol coverage
- Highest reliability scores

### 3. Regional Specific Sources

Sources optimized for specific geographic regions.

```yaml
regional_specific:
  asia_pacific:
    description: Asia-Pacific region optimized servers
    urls:
      - url: https://raw.githubusercontent.com/Lewis-1217/FreeVPN/main/VPN.txt
        region: AS
        protocols: [vmess, vless, shadowsocks]
  
  europe:
    description: European region optimized servers
    urls:
      - url: https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/europe.txt
        region: EU
        protocols: [vmess, vless, trojan]
  
  americas:
    description: Americas region optimized servers
    urls:
      - url: https://raw.githubusercontent.com/vveg26/get_proxy/main/dist/v2ray.config.txt
        region: US
        protocols: [vmess, vless, trojan]
```

**Features:**
- Geographic optimization
- Region-specific protocols
- Latency optimization
- Local server coverage

### 4. Protocol Specific Sources

Sources dedicated to specific VPN protocols.

```yaml
protocol_specific:
  shadowsocks:
    description: Shadowsocks protocol specific sources
    urls:
      - url: https://raw.githubusercontent.com/HakurouKen/free-node/main/shadowsocks.txt
        protocols: [shadowsocks]
  
  vmess:
    description: VMess protocol specific sources
    urls:
      - url: https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray
        protocols: [vmess]
  
  vless:
    description: VLESS protocol specific sources
    urls:
      - url: https://raw.githubusercontent.com/mfuu/v2ray/master/vless
        protocols: [vless]
  
  trojan:
    description: Trojan protocol specific sources
    urls:
      - url: https://raw.githubusercontent.com/mfuu/v2ray/master/trojan
        protocols: [trojan]
  
  wireguard:
    description: WireGuard protocol specific sources
    urls:
      - url: https://raw.githubusercontent.com/mfuu/v2ray/master/wireguard
        protocols: [wireguard]
```

**Features:**
- Protocol specialization
- Optimized configurations
- Protocol-specific maintenance
- Targeted protocol support

### 5. Quality Validated Sources

Sources that have passed comprehensive quality validation.

```yaml
quality_validated:
  description: Sources that have passed comprehensive quality validation
  reliability_score: 0.95
  urls:
    - url: https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge_base64.txt
      quality_score: 0.95
      ssl_valid: true
      response_time_ms: 150
```

**Features:**
- Comprehensive quality validation
- SSL certificate verification
- Performance monitoring
- Highest quality scores

## Enhanced Source Validation

### Quality Scoring System

The enhanced source validator provides comprehensive quality assessment:

```python
from vpn_merger.core import EnhancedSourceValidator

async with EnhancedSourceValidator() as validator:
    metrics = await validator.validate_source_quality("https://example.com/sources.txt")
    print(f"Quality Score: {metrics.quality_score}")
    print(f"Historical Reliability: {metrics.historical_reliability}")
    print(f"SSL Certificate Score: {metrics.ssl_certificate_score}")
    print(f"Response Time Score: {metrics.response_time_score}")
    print(f"Content Quality Score: {metrics.content_quality_score}")
    print(f"Protocol Diversity Score: {metrics.protocol_diversity_score}")
    print(f"Uptime Consistency Score: {metrics.uptime_consistency_score}")
```

### Quality Metrics

#### 1. Historical Reliability (25% weight)
- Tracks success/failure history
- Recency-weighted scoring
- Consistency analysis

#### 2. SSL Certificate (15% weight)
- Certificate validity
- Security assessment
- HTTPS enforcement

#### 3. Response Time (15% weight)
- Latency measurement
- Performance optimization
- Speed scoring

#### 4. Content Quality (20% weight)
- Base64 encoding detection
- JSON/YAML format validation
- Configuration completeness
- Server metadata presence

#### 5. Protocol Diversity (15% weight)
- Multiple protocol support
- Protocol variety assessment
- Coverage analysis

#### 6. Uptime Consistency (10% weight)
- Availability tracking
- Consistency patterns
- Reliability assessment

## Configuration

### Basic Configuration

```python
from vpn_merger.core import SourceManager

# Enable enhanced validation
source_manager = SourceManager(
    config_path="config/sources.expanded.yaml",
    use_enhanced_validation=True
)
```

### Advanced Configuration

```yaml
# config/sources.expanded.yaml
validation:
  enabled: true
  ssl_validation: true
  content_quality_check: true
  protocol_detection: true
  response_time_monitoring: true
  historical_reliability_tracking: true
  quality_scoring:
    enabled: true
    weights:
      historical_reliability: 0.25
      ssl_certificate: 0.15
      response_time: 0.15
      content_quality: 0.20
      protocol_diversity: 0.15
      uptime_consistency: 0.10
  auto_quality_filtering: true
  min_quality_threshold: 0.4

performance:
  concurrent_validation: 10
  validation_timeout: 30
  cache_validation_results: true
  cache_ttl: 3600
  batch_processing: true
  batch_size: 50
  rate_limiting:
    enabled: true
    requests_per_minute: 60
    burst_limit: 10
```

## Usage Examples

### 1. Basic Source Management

```python
from vpn_merger.core import SourceManager

# Initialize with enhanced validation
source_manager = SourceManager(use_enhanced_validation=True)

# Get sources by category
community_sources = source_manager.get_community_maintained_sources()
aggregator_sources = source_manager.get_aggregator_sources()
regional_sources = source_manager.get_regional_sources("asia_pacific")
protocol_sources = source_manager.get_protocol_specific_sources("vmess")
quality_sources = source_manager.get_quality_validated_sources()

# Get all enhanced sources
enhanced_sources = source_manager.get_enhanced_sources()
```

### 2. Quality Validation

```python
import asyncio

async def validate_sources():
    source_manager = SourceManager(use_enhanced_validation=True)
    
    # Validate all sources
    quality_scores = await source_manager.validate_sources_quality()
    
    # Filter by quality
    high_quality_sources = source_manager.filter_sources_by_quality(min_quality=0.8)
    
    # Get top quality sources
    top_sources = source_manager.get_top_quality_sources(limit=10)
    
    # Get quality statistics
    stats = source_manager.get_source_quality_statistics()
    print(f"Average Quality Score: {stats['average_quality_score']}")
    print(f"Total Sources: {stats['total_sources']}")

# Run validation
asyncio.run(validate_sources())
```

### 3. Category-Specific Processing

```python
from vpn_merger.core import SourceManager, SourceProcessor

async def process_by_category():
    source_manager = SourceManager(use_enhanced_validation=True)
    processor = SourceProcessor()
    
    # Process community sources
    community_sources = source_manager.get_community_maintained_sources()
    community_configs = await processor.process_sources_batch(community_sources)
    
    # Process regional sources
    asia_sources = source_manager.get_regional_sources("asia_pacific")
    asia_configs = await processor.process_sources_batch(asia_sources)
    
    # Process protocol-specific sources
    vmess_sources = source_manager.get_protocol_specific_sources("vmess")
    vmess_configs = await processor.process_sources_batch(vmess_sources)
    
    return {
        "community": community_configs,
        "asia": asia_configs,
        "vmess": vmess_configs
    }
```

### 4. Quality Monitoring

```python
import asyncio
from vpn_merger.core import EnhancedSourceValidator

async def monitor_quality():
    async with EnhancedSourceValidator() as validator:
        # Validate multiple sources
        sources = [
            "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
            "https://raw.githubusercontent.com/yebekhe/ConfigCollector/main/sub/mix.txt",
            "https://raw.githubusercontent.com/freefq/free"
        ]
        
        metrics_list = await validator.validate_multiple_sources_quality(sources)
        
        # Analyze results
        for metrics in metrics_list:
            print(f"Source: {metrics.url}")
            print(f"Quality Score: {metrics.quality_score:.2f}")
            print(f"Protocols: {list(metrics.protocols_found)}")
            print(f"Response Time: {metrics.average_response_time:.2f}s")
            print("---")
        
        # Get statistics
        stats = validator.get_quality_statistics()
        print(f"Average Quality: {stats['average_quality_score']:.2f}")
        print(f"Top Sources: {len(stats['top_sources'])}")

# Run monitoring
asyncio.run(monitor_quality())
```

## Quality Scoring

### Scoring Algorithm

The quality score is calculated using weighted factors:

```python
quality_score = (
    historical_reliability * 0.25 +
    ssl_certificate_score * 0.15 +
    response_time_score * 0.15 +
    content_quality_score * 0.20 +
    protocol_diversity_score * 0.15 +
    uptime_consistency_score * 0.10
)
```

### Quality Thresholds

- **Excellent**: 0.8 - 1.0
- **Good**: 0.6 - 0.8
- **Fair**: 0.4 - 0.6
- **Poor**: 0.0 - 0.4

### Quality Indicators

#### Content Quality Indicators
- **Base64 Encoded**: 0.1 points
- **JSON Format**: 0.2 points
- **YAML Format**: 0.15 points
- **Multiple Protocols**: 0.3 points
- **Server Metadata**: 0.15 points
- **Configuration Completeness**: 0.1 points

#### Protocol Detection
- VMess, VLESS, Trojan, Shadowsocks
- HTTP, HTTPS, SOCKS, SOCKS5
- Hysteria, Hysteria2, TUIC
- WireGuard

## API Reference

### SourceManager Methods

#### Enhanced Category Methods
- `get_community_maintained_sources()` → List[str]
- `get_aggregator_sources()` → List[str]
- `get_regional_sources(region: Optional[str])` → List[str]
- `get_protocol_specific_sources(protocol: Optional[str])` → List[str]
- `get_quality_validated_sources()` → List[str]
- `get_enhanced_sources()` → Dict[str, List[str]]

#### Quality Validation Methods
- `validate_sources_quality(sources: Optional[List[str]])` → Dict[str, float]
- `get_source_quality_statistics()` → Dict[str, Any]
- `filter_sources_by_quality(min_quality: float)` → List[str]
- `get_top_quality_sources(limit: int)` → List[str]

### EnhancedSourceValidator Methods

#### Validation Methods
- `validate_source_quality(url: str)` → SourceQualityMetrics
- `validate_multiple_sources_quality(urls: List[str])` → List[SourceQualityMetrics]

#### Analysis Methods
- `get_quality_statistics()` → Dict[str, Any]
- `get_top_quality_sources(limit: int)` → List[SourceQualityMetrics]
- `filter_by_quality(min_score: float)` → List[SourceQualityMetrics]

### SourceQualityMetrics Properties

- `url: str` - Source URL
- `quality_score: float` - Overall quality score (0.0-1.0)
- `historical_reliability: float` - Historical reliability score
- `ssl_certificate_score: float` - SSL certificate score
- `response_time_score: float` - Response time score
- `content_quality_score: float` - Content quality score
- `protocol_diversity_score: float` - Protocol diversity score
- `uptime_consistency_score: float` - Uptime consistency score
- `last_checked: datetime` - Last validation timestamp
- `check_count: int` - Total validation count
- `success_count: int` - Successful validation count
- `failure_count: int` - Failed validation count
- `average_response_time: float` - Average response time
- `protocols_found: Set[str]` - Detected protocols
- `content_indicators: Dict[str, bool]` - Content quality indicators
- `ssl_info: Dict[str, Any]` - SSL certificate information

## Best Practices

### 1. Source Selection

```python
# Prioritize quality-validated sources
quality_sources = source_manager.get_quality_validated_sources()

# Use aggregator services for comprehensive coverage
aggregator_sources = source_manager.get_aggregator_sources()

# Add regional sources for geographic optimization
regional_sources = source_manager.get_regional_sources("asia_pacific")

# Include protocol-specific sources for specialized needs
vmess_sources = source_manager.get_protocol_specific_sources("vmess")
```

### 2. Quality Filtering

```python
# Filter sources by minimum quality threshold
high_quality_sources = source_manager.filter_sources_by_quality(min_quality=0.7)

# Get top performing sources
top_sources = source_manager.get_top_quality_sources(limit=20)

# Validate sources before processing
quality_scores = await source_manager.validate_sources_quality(high_quality_sources)
```

### 3. Performance Optimization

```python
# Use batch processing for multiple sources
configs = await processor.process_sources_batch(sources, batch_size=10)

# Enable caching for validation results
source_manager = SourceManager(use_enhanced_validation=True)

# Use concurrent validation
metrics_list = await validator.validate_multiple_sources_quality(
    sources, max_concurrent=10
)
```

### 4. Monitoring and Maintenance

```python
# Regular quality monitoring
async def monitor_quality():
    stats = source_manager.get_source_quality_statistics()
    if stats['average_quality_score'] < 0.6:
        logger.warning("Source quality below threshold")
    
    # Update source list based on quality
    high_quality_sources = source_manager.filter_sources_by_quality(0.7)
    return high_quality_sources

# Periodic validation
async def periodic_validation():
    while True:
        await source_manager.validate_sources_quality()
        await asyncio.sleep(3600)  # Validate every hour
```

### 5. Error Handling

```python
try:
    quality_scores = await source_manager.validate_sources_quality()
except Exception as e:
    logger.error(f"Quality validation failed: {e}")
    # Fallback to basic sources
    fallback_sources = source_manager.get_all_sources()
```

## Troubleshooting

### Common Issues

#### 1. Enhanced Validation Not Available
```python
# Check if enhanced validation is enabled
if not source_manager.use_enhanced_validation:
    logger.warning("Enhanced validation not available")
    # Use basic validation instead
```

#### 2. Quality Scores Too Low
```python
# Adjust quality thresholds
high_quality_sources = source_manager.filter_sources_by_quality(min_quality=0.3)

# Check quality statistics
stats = source_manager.get_source_quality_statistics()
print(f"Quality distribution: {stats['quality_distribution']}")
```

#### 3. Validation Timeouts
```python
# Increase timeout for slow sources
validator = EnhancedSourceValidator(timeout=60)

# Use smaller batch sizes
metrics_list = await validator.validate_multiple_sources_quality(
    sources, max_concurrent=5
)
```

### Performance Issues

#### 1. Slow Validation
- Reduce concurrent validation limit
- Increase timeout values
- Use caching for validation results
- Filter sources before validation

#### 2. Memory Usage
- Use batch processing
- Clear validation history periodically
- Limit concurrent operations
- Monitor memory usage

## Migration Guide

### From Basic to Enhanced Sources

1. **Update Configuration**
   ```yaml
   # Use expanded configuration
   config_path: "config/sources.expanded.yaml"
   ```

2. **Enable Enhanced Validation**
   ```python
   source_manager = SourceManager(use_enhanced_validation=True)
   ```

3. **Update Source Selection**
   ```python
   # Old way
   all_sources = source_manager.get_all_sources()
   
   # New way
   quality_sources = source_manager.filter_sources_by_quality(0.7)
   community_sources = source_manager.get_community_maintained_sources()
   ```

4. **Add Quality Monitoring**
   ```python
   # Monitor source quality
   stats = source_manager.get_source_quality_statistics()
   top_sources = source_manager.get_top_quality_sources(10)
   ```

## Future Enhancements

### Planned Features

1. **Machine Learning Quality Prediction**
   - ML-based quality scoring
   - Predictive reliability assessment
   - Automated source ranking

2. **Advanced Analytics**
   - Source performance trends
   - Geographic performance analysis
   - Protocol effectiveness metrics

3. **Dynamic Source Management**
   - Automatic source discovery
   - Dynamic quality adjustment
   - Self-healing source lists

4. **Enhanced Monitoring**
   - Real-time quality dashboards
   - Alert systems for quality drops
   - Performance benchmarking

### Contributing

To contribute to source expansion features:

1. Add new source categories to `config/sources.expanded.yaml`
2. Implement new validation methods in `EnhancedSourceValidator`
3. Add category-specific methods to `SourceManager`
4. Update documentation and examples
5. Add comprehensive tests

## Support

For questions and support regarding source expansion features:

- Check the troubleshooting section
- Review the API reference
- Examine the usage examples
- Create an issue for bugs or feature requests
