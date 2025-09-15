# Configuration Guide

## Table of Contents
1. [Overview](#overview)
2. [Configuration Files](#configuration-files)
3. [Environment Variables](#environment-variables)
4. [Source Configuration](#source-configuration)
5. [Processing Settings](#processing-settings)
6. [Quality Controls](#quality-controls)
7. [Monitoring Configuration](#monitoring-configuration)
8. [Security Settings](#security-settings)
9. [Output Configuration](#output-configuration)
10. [Examples](#examples)

## Overview

The VPN Subscription Merger supports multiple configuration formats and provides extensive customization options for all aspects of the system.

## Configuration Files

### Primary Configuration
- `config/sources.yaml` - Main source configuration
- `config/sources.yaml` - Configuration with supported features
- `config/sources.expanded.yaml` - Expanded source categories

### Environment Configuration
- `.env` - Environment variables
- `.env.local` - Local environment overrides
- `.env.production` - Production environment settings

## Environment Variables

### Core Settings
```bash
# Application
STREAMLINE_HOST=0.0.0.0
STREAMLINE_PORT=8000
STREAMLINE_DEBUG=false
STREAMLINE_LOG_LEVEL=INFO

# Database
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///data/streamline_vpn.db

# Security
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here
JWT_SECRET=your-jwt-secret-here

# Performance
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=30
BATCH_SIZE=10
CACHE_TTL=3600

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=60
```

## Source Configuration

### Basic Source Configuration
```yaml
sources:
  primary:
    - "https://test-server.example/free.txt"
    - "https://another.com/nodes.txt"
  
  secondary:
    - "https://backup.com/sources.txt"
```

### Source Configuration
```yaml
sources:
  community_maintained:
    - url: "https://test-server.example/free.txt"
      priority: 1
      reliability: 0.9
      last_updated: "2023-12-01T14:30:22Z"
  
  aggregator_services:
    - url: "https://aggregator.com/nodes.json"
      priority: 2
      reliability: 0.8
      api_key: "optional-api-key"
  
  regional_specific:
    us:
      - url: "https://us.test-server.example/nodes.txt"
        priority: 1
        reliability: 0.85
    
    eu:
      - url: "https://eu.test-server.example/nodes.txt"
        priority: 1
        reliability: 0.85
  
  protocol_specific:
    vless:
      - url: "https://vless.test-server.example/configs.txt"
        priority: 1
        reliability: 0.9
    
    wireguard:
      - url: "https://wg.test-server.example/configs.txt"
        priority: 1
        reliability: 0.8
```

## Processing Settings

### Basic Processing
```yaml
settings:
  processing:
    max_concurrent: 100
    timeout: 30
    retry_attempts: 3
    retry_delay: 5
    batch_size: 10
    cache_ttl: 3600
```

### Processing
```yaml
settings:
  processing:
    max_concurrent: 100
    timeout: 30
    retry_attempts: 3
    retry_delay: 5
    batch_size: 10
    cache_ttl: 3600
    
    # Features
    enable_ml_quality_prediction: true
    enable_source_validation: true
    enable_duplicate_detection: true
    enable_geo_location: true
    
    # Performance optimization
    connection_pooling: true
    keep_alive: true
    compression: true
    rate_limiting: true
```

## Quality Controls

### Basic Quality Controls
```yaml
settings:
  quality:
    min_score: 0.5
    max_latency: 1000
    min_uptime: 0.8
    enable_health_checks: true
    health_check_interval: 300
```

### Quality Controls
```yaml
settings:
  quality:
    min_score: 0.5
    max_latency: 1000
    min_uptime: 0.8
    enable_health_checks: true
    health_check_interval: 300
    
    # ML-based quality prediction
    ml_quality_prediction:
      enabled: true
      model_path: "models/quality_predictor.pkl"
      confidence_threshold: 0.7
      update_interval: 3600
    
    # Source validation
    source_validation:
      enabled: true
      ssl_verification: true
      content_validation: true
      format_validation: true
    
    # Duplicate detection
    duplicate_detection:
      enabled: true
      algorithm: "bloom_filter"
      false_positive_rate: 0.01
      max_elements: 100000
```

## Monitoring Configuration

### Basic Monitoring
```yaml
settings:
  monitoring:
    enable_metrics: true
    metrics_port: 9090
    health_check_interval: 60
    log_level: INFO
```

### Monitoring
```yaml
settings:
  monitoring:
    enable_metrics: true
    metrics_port: 9090
    health_check_interval: 60
    log_level: INFO
    
    # Performance monitoring
    performance_monitoring:
      enabled: true
      memory_threshold: 0.8
      cpu_threshold: 0.8
      disk_threshold: 0.9
    
    # Alerting
    alerting:
      enabled: true
      webhook_url: "https://hooks.slack.com/your-webhook"
      email_notifications: true
      sms_notifications: false
    
    # Logging
    logging:
      level: INFO
      format: "json"
      rotation: "daily"
      retention: "30d"
      compression: true
```

## Security Settings

### Basic Security
```yaml
settings:
  security:
    enable_authentication: false
    enable_rate_limiting: true
    enable_cors: true
    enable_https: false
```

### Security
```yaml
settings:
  security:
    enable_authentication: false
    enable_rate_limiting: true
    enable_cors: true
    enable_https: false
    
    # Rate limiting
    rate_limiting:
      enabled: true
      requests_per_minute: 100
      burst_size: 20
      window_size: 60
    
    # CORS
    cors:
      enabled: true
      allowed_origins: ["*"]
      allowed_methods: ["GET", "POST", "PUT", "DELETE"]
      allowed_headers: ["*"]
    
    # Input validation
    input_validation:
      enabled: true
      max_request_size: 1048576  # 1MB
      max_url_length: 2048
      sanitize_inputs: true
    
    # Path traversal protection
    path_traversal_protection:
      enabled: true
      allowed_paths: ["/output", "/temp", "/cache"]
      blocked_patterns: ["../", "..\\", "%2e%2e", "%2f"]
```

## Output Configuration

### Basic Output
```yaml
settings:
  output:
    directory: "output"
    formats: ["raw", "base64", "csv"]
    compression: false
    encryption: false
```

### Output
```yaml
settings:
  output:
    directory: "output"
    formats: ["raw", "base64", "csv", "json", "yaml"]
    compression: true
    encryption: false
    
    # File management
    file_management:
      max_file_size: 104857600  # 100MB
      max_files: 1000
      cleanup_interval: 3600
      retention_period: 86400  # 24 hours
    
    # Format-specific settings
    format_settings:
      raw:
        encoding: "utf-8"
        line_ending: "unix"
      
      base64:
        encoding: "utf-8"
        line_length: 76
      
      csv:
        delimiter: ","
        quote_char: "\""
        escape_char: "\\"
      
      json:
        indent: 2
        sort_keys: true
      
      yaml:
        indent: 2
        sort_keys: true
```

## Examples

### Complete Configuration Example
```yaml
# Complete configuration example
sources:
  community_maintained:
    - url: "https://test-server.example/free.txt"
      priority: 1
      reliability: 0.9
      last_updated: "2023-12-01T14:30:22Z"
  
  aggregator_services:
    - url: "https://aggregator.com/nodes.json"
      priority: 2
      reliability: 0.8
      api_key: "optional-api-key"

settings:
  processing:
    max_concurrent: 100
    timeout: 30
    retry_attempts: 3
    retry_delay: 5
    batch_size: 10
    cache_ttl: 3600
    enable_ml_quality_prediction: true
    enable_source_validation: true
    enable_duplicate_detection: true
    enable_geo_location: true
    connection_pooling: true
    keep_alive: true
    compression: true
    rate_limiting: true
  
  quality:
    min_score: 0.5
    max_latency: 1000
    min_uptime: 0.8
    enable_health_checks: true
    health_check_interval: 300
    ml_quality_prediction:
      enabled: true
      model_path: "models/quality_predictor.pkl"
      confidence_threshold: 0.7
      update_interval: 3600
    source_validation:
      enabled: true
      ssl_verification: true
      content_validation: true
      format_validation: true
    duplicate_detection:
      enabled: true
      algorithm: "bloom_filter"
      false_positive_rate: 0.01
      max_elements: 100000
  
  monitoring:
    enable_metrics: true
    metrics_port: 9090
    health_check_interval: 60
    log_level: INFO
    performance_monitoring:
      enabled: true
      memory_threshold: 0.8
      cpu_threshold: 0.8
      disk_threshold: 0.9
    alerting:
      enabled: true
      webhook_url: "https://hooks.slack.com/your-webhook"
      email_notifications: true
      sms_notifications: false
    logging:
      level: INFO
      format: "json"
      rotation: "daily"
      retention: "30d"
      compression: true
  
  security:
    enable_authentication: false
    enable_rate_limiting: true
    enable_cors: true
    enable_https: false
    rate_limiting:
      enabled: true
      requests_per_minute: 100
      burst_size: 20
      window_size: 60
    cors:
      enabled: true
      allowed_origins: ["*"]
      allowed_methods: ["GET", "POST", "PUT", "DELETE"]
      allowed_headers: ["*"]
    input_validation:
      enabled: true
      max_request_size: 1048576
      max_url_length: 2048
      sanitize_inputs: true
    path_traversal_protection:
      enabled: true
      allowed_paths: ["/output", "/temp", "/cache"]
      blocked_patterns: ["../", "..\\", "%2e%2e", "%2f"]
  
  output:
    directory: "output"
    formats: ["raw", "base64", "csv", "json", "yaml"]
    compression: true
    encryption: false
    file_management:
      max_file_size: 104857600
      max_files: 1000
      cleanup_interval: 3600
      retention_period: 86400
    format_settings:
      raw:
        encoding: "utf-8"
        line_ending: "unix"
      base64:
        encoding: "utf-8"
        line_length: 76
      csv:
        delimiter: ","
        quote_char: "\""
        escape_char: "\\"
      json:
        indent: 2
        sort_keys: true
      yaml:
        indent: 2
        sort_keys: true
```

### Environment Variables Example
```bash
# .env file
STREAMLINE_HOST=0.0.0.0
STREAMLINE_PORT=8000
STREAMLINE_DEBUG=false
STREAMLINE_LOG_LEVEL=INFO

REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///data/streamline_vpn.db

SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here
JWT_SECRET=your-jwt-secret-here

MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=30
BATCH_SIZE=10
CACHE_TTL=3600

ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=60
```

### Docker Configuration Example
```yaml
# docker-compose.yml
version: '3.8'

services:
  vpn-merger:
    build: .
    ports:
      - "8000:8000"
    environment:
      - STREAMLINE_HOST=0.0.0.0
      - STREAMLINE_PORT=8000
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=sqlite:///data/streamline_vpn.db
    volumes:
      - ./config:/app/config
      - ./output:/app/output
      - ./data:/app/data
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### Kubernetes Configuration Example
```yaml
# k8s-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vpn-merger-config
data:
  sources.yaml: |
    sources:
      community_maintained:
        - url: "https://test-server.example/free.txt"
          priority: 1
          reliability: 0.9
  
  settings.yaml: |
    settings:
      processing:
        max_concurrent: 100
        timeout: 30
      quality:
        min_score: 0.5
        max_latency: 1000
      monitoring:
        enable_metrics: true
        metrics_port: 9090
      security:
        enable_rate_limiting: true
      output:
        directory: "output"
        formats: ["raw", "base64", "csv"]

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vpn-merger
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vpn-merger
  template:
    metadata:
      labels:
        app: vpn-merger
    spec:
      containers:
      - name: vpn-merger
        image: vpn-merger:latest
        ports:
        - containerPort: 8000
        env:
        - name: STREAMLINE_HOST
          value: "0.0.0.0"
        - name: STREAMLINE_PORT
          value: "8000"
        - name: REDIS_URL
          value: "redis://redis:6379/0"
        - name: DATABASE_URL
          value: "sqlite:///data/streamline_vpn.db"
        volumeMounts:
        - name: config
          mountPath: /app/config
        - name: output
          mountPath: /app/output
        - name: data
          mountPath: /app/data
      volumes:
      - name: config
        configMap:
          name: vpn-merger-config
      - name: output
        persistentVolumeClaim:
          claimName: vpn-merger-output
      - name: data
        persistentVolumeClaim:
          claimName: vpn-merger-data
```

This configuration guide summarizes key settings for the VPN Subscription Merger system across common deployment scenarios.
