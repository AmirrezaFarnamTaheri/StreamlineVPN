# Source Expansion API Reference

## Overview

This document provides comprehensive API reference for the source expansion features, including enhanced source validation, new source categories, and quality scoring systems.

## Table of Contents

- [SourceManager API](#sourcemanager-api)
- [EnhancedSourceValidator API](#enhancedsourcevalidator-api)
- [SourceQualityMetrics API](#sourcequalitymetrics-api)
- [Configuration API](#configuration-api)
- [Error Handling](#error-handling)
- [Examples](#examples)

## SourceManager API

### Constructor

```python
SourceManager(config_path: str | Path = "config/sources.unified.yaml", use_enhanced_validation: bool = False)
```

**Parameters:**
- `config_path`: Path to the configuration file
- `use_enhanced_validation`: Whether to enable enhanced source validation

**Example:**
```python
from vpn_merger.core import SourceManager

# Basic initialization
source_manager = SourceManager()

# With enhanced validation
source_manager = SourceManager(
    config_path="config/sources.expanded.yaml",
    use_enhanced_validation=True
)
```

### Enhanced Category Methods

#### get_community_maintained_sources()

```python
def get_community_maintained_sources(self) -> List[str]
```

**Returns:** List of community-maintained source URLs

**Example:**
```python
community_sources = source_manager.get_community_maintained_sources()
print(f"Found {len(community_sources)} community sources")
```

#### get_aggregator_sources()

```python
def get_aggregator_sources(self) -> List[str]
```

**Returns:** List of aggregator service source URLs

**Example:**
```python
aggregator_sources = source_manager.get_aggregator_sources()
print(f"Found {len(aggregator_sources)} aggregator sources")
```

#### get_regional_sources()

```python
def get_regional_sources(self, region: Optional[str] = None) -> List[str]
```

**Parameters:**
- `region`: Specific region ("asia_pacific", "europe", "americas") or None for all

**Returns:** List of regional source URLs

**Example:**
```python
# Get all regional sources
all_regional = source_manager.get_regional_sources()

# Get specific region
asia_sources = source_manager.get_regional_sources("asia_pacific")
europe_sources = source_manager.get_regional_sources("europe")
americas_sources = source_manager.get_regional_sources("americas")
```

#### get_protocol_specific_sources()

```python
def get_protocol_specific_sources(self, protocol: Optional[str] = None) -> List[str]
```

**Parameters:**
- `protocol`: Specific protocol ("shadowsocks", "vmess", "vless", "trojan", "wireguard") or None for all

**Returns:** List of protocol-specific source URLs

**Example:**
```python
# Get all protocol-specific sources
all_protocol = source_manager.get_protocol_specific_sources()

# Get specific protocol
vmess_sources = source_manager.get_protocol_specific_sources("vmess")
shadowsocks_sources = source_manager.get_protocol_specific_sources("shadowsocks")
```

#### get_quality_validated_sources()

```python
def get_quality_validated_sources(self) -> List[str]
```

**Returns:** List of quality-validated source URLs

**Example:**
```python
quality_sources = source_manager.get_quality_validated_sources()
print(f"Found {len(quality_sources)} quality-validated sources")
```

#### get_enhanced_sources()

```python
def get_enhanced_sources(self) -> Dict[str, List[str]]
```

**Returns:** Dictionary mapping enhanced categories to source URLs

**Example:**
```python
enhanced_sources = source_manager.get_enhanced_sources()
for category, sources in enhanced_sources.items():
    print(f"{category}: {len(sources)} sources")
```

### Quality Validation Methods

#### validate_sources_quality()

```python
async def validate_sources_quality(self, sources: Optional[List[str]] = None) -> Dict[str, float]
```

**Parameters:**
- `sources`: List of sources to validate, or None to validate all sources

**Returns:** Dictionary mapping source URLs to quality scores

**Example:**
```python
import asyncio

async def validate_sources():
    source_manager = SourceManager(use_enhanced_validation=True)
    
    # Validate all sources
    quality_scores = await source_manager.validate_sources_quality()
    
    # Validate specific sources
    specific_sources = ["https://example1.com", "https://example2.com"]
    scores = await source_manager.validate_sources_quality(specific_sources)
    
    for url, score in scores.items():
        print(f"{url}: {score:.2f}")

asyncio.run(validate_sources())
```

#### get_source_quality_statistics()

```python
def get_source_quality_statistics(self) -> Dict[str, Any]
```

**Returns:** Dictionary with quality statistics

**Example:**
```python
stats = source_manager.get_source_quality_statistics()
print(f"Total sources: {stats['total_sources']}")
print(f"Average quality: {stats['average_quality_score']:.2f}")
print(f"Quality distribution: {stats['quality_distribution']}")
```

#### filter_sources_by_quality()

```python
def filter_sources_by_quality(self, min_quality: float = 0.5) -> List[str]
```

**Parameters:**
- `min_quality`: Minimum quality score threshold

**Returns:** List of high-quality source URLs

**Example:**
```python
# Get high-quality sources
high_quality = source_manager.filter_sources_by_quality(min_quality=0.8)

# Get medium-quality sources
medium_quality = source_manager.filter_sources_by_quality(min_quality=0.6)
```

#### get_top_quality_sources()

```python
def get_top_quality_sources(self, limit: int = 10) -> List[str]
```

**Parameters:**
- `limit`: Maximum number of sources to return

**Returns:** List of top quality source URLs

**Example:**
```python
# Get top 10 sources
top_sources = source_manager.get_top_quality_sources(limit=10)

# Get top 5 sources
top_5 = source_manager.get_top_quality_sources(limit=5)
```

### Standard Methods (Enhanced)

#### get_statistics()

```python
def get_statistics(self) -> Dict[str, Any]
```

**Returns:** Enhanced statistics including source categories and validation status

**Example:**
```python
stats = source_manager.get_statistics()
print(f"Total sources: {stats['total_sources']}")
print(f"Categories: {stats['source_categories']}")
print(f"Enhanced validation: {stats['enhanced_validation_enabled']}")
```

## EnhancedSourceValidator API

### Constructor

```python
EnhancedSourceValidator(timeout: int = 30, max_redirects: int = 5)
```

**Parameters:**
- `timeout`: Request timeout in seconds
- `max_redirects`: Maximum number of redirects to follow

**Example:**
```python
from vpn_merger.core import EnhancedSourceValidator

# Basic initialization
validator = EnhancedSourceValidator()

# With custom timeout
validator = EnhancedSourceValidator(timeout=60, max_redirects=3)
```

### Context Manager

```python
async with EnhancedSourceValidator() as validator:
    # Use validator
    pass
```

**Example:**
```python
async def validate_source():
    async with EnhancedSourceValidator() as validator:
        metrics = await validator.validate_source_quality("https://example.com")
        return metrics
```

### Validation Methods

#### validate_source_quality()

```python
async def validate_source_quality(self, url: str) -> SourceQualityMetrics
```

**Parameters:**
- `url`: Source URL to validate

**Returns:** SourceQualityMetrics object with comprehensive quality data

**Example:**
```python
async def validate_single_source():
    async with EnhancedSourceValidator() as validator:
        metrics = await validator.validate_source_quality("https://example.com/sources.txt")
        
        print(f"URL: {metrics.url}")
        print(f"Quality Score: {metrics.quality_score:.2f}")
        print(f"Historical Reliability: {metrics.historical_reliability:.2f}")
        print(f"SSL Score: {metrics.ssl_certificate_score:.2f}")
        print(f"Response Time: {metrics.average_response_time:.2f}s")
        print(f"Protocols: {list(metrics.protocols_found)}")
        
        return metrics
```

#### validate_multiple_sources_quality()

```python
async def validate_multiple_sources_quality(self, urls: List[str], max_concurrent: int = 10) -> List[SourceQualityMetrics]
```

**Parameters:**
- `urls`: List of source URLs to validate
- `max_concurrent`: Maximum number of concurrent validations

**Returns:** List of SourceQualityMetrics objects

**Example:**
```python
async def validate_multiple_sources():
    urls = [
        "https://example1.com/sources.txt",
        "https://example2.com/sources.txt",
        "https://example3.com/sources.txt"
    ]
    
    async with EnhancedSourceValidator() as validator:
        metrics_list = await validator.validate_multiple_sources_quality(
            urls, max_concurrent=5
        )
        
        for metrics in metrics_list:
            print(f"{metrics.url}: {metrics.quality_score:.2f}")
        
        return metrics_list
```

### Analysis Methods

#### get_quality_statistics()

```python
def get_quality_statistics(self) -> Dict[str, Any]
```

**Returns:** Dictionary with comprehensive quality statistics

**Example:**
```python
async def get_stats():
    async with EnhancedSourceValidator() as validator:
        # Validate some sources first
        urls = ["https://example1.com", "https://example2.com"]
        await validator.validate_multiple_sources_quality(urls)
        
        # Get statistics
        stats = validator.get_quality_statistics()
        
        print(f"Total validations: {stats['total_sources']}")
        print(f"Average quality: {stats['average_quality_score']:.2f}")
        print(f"Quality distribution: {stats['quality_distribution']}")
        print(f"Protocol distribution: {stats['protocol_distribution']}")
        
        return stats
```

#### get_top_quality_sources()

```python
def get_top_quality_sources(self, limit: int = 10) -> List[SourceQualityMetrics]
```

**Parameters:**
- `limit`: Maximum number of sources to return

**Returns:** List of top SourceQualityMetrics objects

**Example:**
```python
async def get_top_sources():
    async with EnhancedSourceValidator() as validator:
        # Validate sources first
        urls = ["https://example1.com", "https://example2.com", "https://example3.com"]
        await validator.validate_multiple_sources_quality(urls)
        
        # Get top sources
        top_sources = validator.get_top_quality_sources(limit=5)
        
        for metrics in top_sources:
            print(f"{metrics.url}: {metrics.quality_score:.2f}")
        
        return top_sources
```

#### filter_by_quality()

```python
def filter_by_quality(self, min_score: float = 0.5) -> List[SourceQualityMetrics]
```

**Parameters:**
- `min_score`: Minimum quality score threshold

**Returns:** List of SourceQualityMetrics objects meeting the threshold

**Example:**
```python
async def filter_high_quality():
    async with EnhancedSourceValidator() as validator:
        # Validate sources first
        urls = ["https://example1.com", "https://example2.com", "https://example3.com"]
        await validator.validate_multiple_sources_quality(urls)
        
        # Filter by quality
        high_quality = validator.filter_by_quality(min_score=0.8)
        
        print(f"Found {len(high_quality)} high-quality sources")
        for metrics in high_quality:
            print(f"{metrics.url}: {metrics.quality_score:.2f}")
        
        return high_quality
```

## SourceQualityMetrics API

### Properties

#### Basic Information
- `url: str` - Source URL
- `quality_score: float` - Overall quality score (0.0-1.0)
- `last_checked: datetime` - Last validation timestamp

#### Quality Scores
- `historical_reliability: float` - Historical reliability score (0.0-1.0)
- `ssl_certificate_score: float` - SSL certificate score (0.0-1.0)
- `response_time_score: float` - Response time score (0.0-1.0)
- `content_quality_score: float` - Content quality score (0.0-1.0)
- `protocol_diversity_score: float` - Protocol diversity score (0.0-1.0)
- `uptime_consistency_score: float` - Uptime consistency score (0.0-1.0)

#### Statistics
- `check_count: int` - Total validation count
- `success_count: int` - Successful validation count
- `failure_count: int` - Failed validation count
- `average_response_time: float` - Average response time in seconds

#### Analysis Data
- `protocols_found: Set[str]` - Detected protocols
- `content_indicators: Dict[str, bool]` - Content quality indicators
- `ssl_info: Dict[str, Any]` - SSL certificate information

### Methods

#### to_dict()

```python
def to_dict(self) -> Dict[str, Any]
```

**Returns:** Dictionary representation of the metrics

**Example:**
```python
async def get_metrics_dict():
    async with EnhancedSourceValidator() as validator:
        metrics = await validator.validate_source_quality("https://example.com")
        
        # Convert to dictionary
        metrics_dict = metrics.to_dict()
        
        # Serialize to JSON
        import json
        json_data = json.dumps(metrics_dict, indent=2)
        print(json_data)
        
        return metrics_dict
```

## Configuration API

### Source Configuration

```yaml
# config/sources.expanded.yaml
sources:
  community_maintained:
    description: Community-maintained VPN sources
    reliability_score: 0.8
    urls:
      - url: https://github.com/freefq/free
        maintainer: freefq
        update_frequency: daily
        protocols: [vmess, vless, trojan, shadowsocks]
        weight: 0.9
        source_type: github_repository
```

### Validation Configuration

```yaml
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
```

### Performance Configuration

```yaml
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

## Error Handling

### Common Exceptions

#### RuntimeError
```python
try:
    async with EnhancedSourceValidator() as validator:
        metrics = await validator.validate_source_quality("https://example.com")
except RuntimeError as e:
    print(f"Validation error: {e}")
```

#### ImportError
```python
try:
    from vpn_merger.core import EnhancedSourceValidator
except ImportError as e:
    print(f"Enhanced validation not available: {e}")
    # Fallback to basic validation
```

#### Validation Errors
```python
async def safe_validation():
    async with EnhancedSourceValidator() as validator:
        try:
            metrics = await validator.validate_source_quality("https://example.com")
            return metrics
        except Exception as e:
            print(f"Validation failed: {e}")
            return None
```

### Error Recovery

```python
async def robust_validation():
    source_manager = SourceManager(use_enhanced_validation=True)
    
    try:
        # Try enhanced validation
        quality_scores = await source_manager.validate_sources_quality()
        return quality_scores
    except Exception as e:
        logger.warning(f"Enhanced validation failed: {e}")
        
        # Fallback to basic sources
        fallback_sources = source_manager.get_all_sources()
        return {url: 0.5 for url in fallback_sources}  # Default quality score
```

## Examples

### Complete Source Management Example

```python
import asyncio
from vpn_merger.core import SourceManager, SourceProcessor

async def complete_source_management():
    # Initialize with enhanced validation
    source_manager = SourceManager(
        config_path="config/sources.expanded.yaml",
        use_enhanced_validation=True
    )
    
    # Get sources by category
    community_sources = source_manager.get_community_maintained_sources()
    aggregator_sources = source_manager.get_aggregator_sources()
    regional_sources = source_manager.get_regional_sources("asia_pacific")
    protocol_sources = source_manager.get_protocol_specific_sources("vmess")
    
    # Validate quality
    all_sources = source_manager.get_all_sources()
    quality_scores = await source_manager.validate_sources_quality(all_sources)
    
    # Filter by quality
    high_quality_sources = source_manager.filter_sources_by_quality(min_quality=0.7)
    
    # Get top sources
    top_sources = source_manager.get_top_quality_sources(limit=20)
    
    # Process sources
    processor = SourceProcessor()
    configs = await processor.process_sources_batch(high_quality_sources)
    
    # Get statistics
    stats = source_manager.get_source_quality_statistics()
    
    return {
        "sources": {
            "community": community_sources,
            "aggregator": aggregator_sources,
            "regional": regional_sources,
            "protocol": protocol_sources,
            "high_quality": high_quality_sources,
            "top": top_sources
        },
        "quality_scores": quality_scores,
        "configs": configs,
        "statistics": stats
    }

# Run example
result = asyncio.run(complete_source_management())
```

### Quality Monitoring Example

```python
import asyncio
import time
from vpn_merger.core import EnhancedSourceValidator

async def quality_monitoring():
    sources = [
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
        "https://raw.githubusercontent.com/yebekhe/ConfigCollector/main/sub/mix.txt",
        "https://raw.githubusercontent.com/freefq/free"
    ]
    
    async with EnhancedSourceValidator() as validator:
        while True:
            print(f"Monitoring quality at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Validate sources
            metrics_list = await validator.validate_multiple_sources_quality(sources)
            
            # Analyze results
            for metrics in metrics_list:
                status = "✓" if metrics.quality_score >= 0.7 else "⚠" if metrics.quality_score >= 0.4 else "✗"
                print(f"{status} {metrics.url}: {metrics.quality_score:.2f} "
                      f"({metrics.average_response_time:.2f}s)")
            
            # Get statistics
            stats = validator.get_quality_statistics()
            print(f"Average quality: {stats['average_quality_score']:.2f}")
            print("---")
            
            # Wait before next check
            await asyncio.sleep(300)  # 5 minutes

# Run monitoring
asyncio.run(quality_monitoring())
```

### Batch Processing Example

```python
import asyncio
from vpn_merger.core import SourceManager, SourceProcessor

async def batch_processing_example():
    source_manager = SourceManager(use_enhanced_validation=True)
    processor = SourceProcessor()
    
    # Get sources by category
    categories = {
        "community": source_manager.get_community_maintained_sources(),
        "aggregator": source_manager.get_aggregator_sources(),
        "regional": source_manager.get_regional_sources(),
        "protocol": source_manager.get_protocol_specific_sources(),
        "quality": source_manager.get_quality_validated_sources()
    }
    
    results = {}
    
    # Process each category
    for category, sources in categories.items():
        if sources:
            print(f"Processing {len(sources)} {category} sources...")
            
            # Validate quality
            quality_scores = await source_manager.validate_sources_quality(sources)
            
            # Filter high-quality sources
            high_quality = [url for url, score in quality_scores.items() if score >= 0.6]
            
            # Process sources
            configs = await processor.process_sources_batch(high_quality)
            
            results[category] = {
                "total_sources": len(sources),
                "high_quality_sources": len(high_quality),
                "configs": configs,
                "quality_scores": quality_scores
            }
            
            print(f"  Processed {len(configs)} configurations from {len(high_quality)} sources")
    
    return results

# Run batch processing
results = asyncio.run(batch_processing_example())
```

This API reference provides comprehensive documentation for all source expansion features. For additional examples and use cases, refer to the main documentation and example files.
