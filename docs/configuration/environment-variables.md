# Environment Variables Reference

## Overview

The VPN Subscription Merger uses environment variables for configuration management, allowing flexible deployment across different environments without modifying configuration files. This page lists supported environment variables.

## Core Configuration

### VPN_SOURCES_CONFIG

**Description:** Path to the main sources configuration file  
**Type:** String (file path)  
**Default:** `config/sources.yaml`  
**Required:** No  
**Example:** `VPN_SOURCES_CONFIG=/etc/vpn-merger/sources.yaml`

```bash
# Set custom sources configuration file
export VPN_SOURCES_CONFIG="/path/to/custom/sources.yaml"
```

**Validation:**
- Must be a valid file path
- File must exist and be readable
- Must be a valid YAML file

### VPN_CONCURRENT_LIMIT

**Description:** Maximum number of concurrent source processing operations  
**Type:** Integer  
**Default:** `50`  
**Range:** 1-1000  
**Required:** No  
**Example:** `VPN_CONCURRENT_LIMIT=100`

```bash
# Increase concurrency for high-performance systems
export VPN_CONCURRENT_LIMIT=100

# Reduce concurrency for resource-constrained systems
export VPN_CONCURRENT_LIMIT=10
```

**Performance Impact:**
- Higher values: Faster processing, more memory usage
- Lower values: Slower processing, less memory usage

### VPN_TIMEOUT

**Description:** Request timeout in seconds for source fetching  
**Type:** Integer  
**Default:** `30`  
**Range:** 5-300  
**Required:** No  
**Example:** `VPN_TIMEOUT=60`

```bash
# Increase timeout for slow sources
export VPN_TIMEOUT=60

# Decrease timeout for fast processing
export VPN_TIMEOUT=15
```

### VPN_MAX_RETRIES

**Description:** Maximum number of retry attempts for failed requests  
**Type:** Integer  
**Default:** `3`  
**Range:** 0-10  
**Required:** No  
**Example:** `VPN_MAX_RETRIES=5`

```bash
# Increase retries for unreliable sources
export VPN_MAX_RETRIES=5

# Disable retries for fast failure detection
export VPN_MAX_RETRIES=0
```

## Output Configuration

### VPN_OUTPUT_DIR

**Description:** Directory for output files  
**Type:** String (directory path)  
**Default:** `output`  
**Required:** No  
**Example:** `VPN_OUTPUT_DIR=/var/lib/vpn-merger/output`

```bash
# Set custom output directory
export VPN_OUTPUT_DIR="/var/lib/vpn-merger/output"

# Use relative path
export VPN_OUTPUT_DIR="./results"
```

**Validation:**
- Must be a valid directory path
- Directory will be created if it doesn't exist
- Must be writable by the application

### VPN_WRITE_BASE64

**Description:** Enable Base64 encoded output file generation  
**Type:** Boolean  
**Default:** `true`  
**Required:** No  
**Example:** `VPN_WRITE_BASE64=false`

```bash
# Disable Base64 output
export VPN_WRITE_BASE64=false

# Enable Base64 output (default)
export VPN_WRITE_BASE64=true
```

### VPN_WRITE_CSV

**Description:** Enable CSV output file generation  
**Type:** Boolean  
**Default:** `true`  
**Required:** No  
**Example:** `VPN_WRITE_CSV=false`

```bash
# Disable CSV output
export VPN_WRITE_CSV=false
```

### VPN_WRITE_JSON

**Description:** Enable JSON output file generation  
**Type:** Boolean  
**Default:** `true`  
**Required:** No  
**Example:** `VPN_WRITE_JSON=false`

```bash
# Disable JSON output
export VPN_WRITE_JSON=false
```

### VPN_WRITE_SINGBOX

**Description:** Enable sing-box JSON output file generation  
**Type:** Boolean  
**Default:** `true`  
**Required:** No  
**Example:** `VPN_WRITE_SINGBOX=false`

```bash
# Disable sing-box output
export VPN_WRITE_SINGBOX=false
```

### VPN_WRITE_CLASH

**Description:** Enable Clash YAML output file generation  
**Type:** Boolean  
**Default:** `true`  
**Required:** No  
**Example:** `VPN_WRITE_CLASH=false`

```bash
# Disable Clash output
export VPN_WRITE_CLASH=false
```

## Logging Configuration

### VPN_LOG_LEVEL

**Description:** Logging level for the application  
**Type:** String (enum)  
**Default:** `INFO`  
**Options:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`  
**Required:** No  
**Example:** `VPN_LOG_LEVEL=DEBUG`

```bash
# Enable debug logging
export VPN_LOG_LEVEL=DEBUG

# Set to error level for production
export VPN_LOG_LEVEL=ERROR
```

### VPN_LOG_FILE

**Description:** Path to log file (if file logging is enabled)  
**Type:** String (file path)  
**Default:** None (console only)  
**Required:** No  
**Example:** `VPN_LOG_FILE=/var/log/vpn-merger.log`

```bash
# Enable file logging
export VPN_LOG_FILE="/var/log/vpn-merger.log"

# Use relative path
export VPN_LOG_FILE="./logs/vpn-merger.log"
```

### VPN_LOG_MAX_SIZE

**Description:** Maximum log file size in MB before rotation  
**Type:** Integer  
**Default:** `10`  
**Range:** 1-100  
**Required:** No  
**Example:** `VPN_LOG_MAX_SIZE=50`

```bash
# Increase log file size
export VPN_LOG_MAX_SIZE=50
```

### VPN_LOG_BACKUP_COUNT

**Description:** Number of backup log files to keep  
**Type:** Integer  
**Default:** `3`  
**Range:** 1-10  
**Required:** No  
**Example:** `VPN_LOG_BACKUP_COUNT=5`

```bash
# Keep more backup files
export VPN_LOG_BACKUP_COUNT=5
```

## Cache Configuration

### VPN_CACHE_ENABLED

**Description:** Enable caching system  
**Type:** Boolean  
**Default:** `true`  
**Required:** No  
**Example:** `VPN_CACHE_ENABLED=false`

```bash
# Disable caching
export VPN_CACHE_ENABLED=false
```

### VPN_REDIS_URL

**Description:** Redis connection URL for distributed caching  
**Type:** String (URL)  
**Default:** None (in-memory cache)  
**Required:** No  
**Example:** `VPN_REDIS_URL=redis://localhost:6379/0`

```bash
# Use Redis for caching
export VPN_REDIS_URL="redis://localhost:6379/0"

# Use Redis with authentication
export VPN_REDIS_URL="redis://user:password@localhost:6379/0"

# Use Redis with SSL
export VPN_REDIS_URL="rediss://user:password@redis.test-server.example:6380/0"
```

**Validation:**
- Must be a valid Redis URL
- Format: `redis://[user:password@]host:port/db`
- SSL support: `rediss://` for secure connections

### VPN_CACHE_TTL

**Description:** Cache time-to-live in seconds  
**Type:** Integer  
**Default:** `3600` (1 hour)  
**Range:** 60-86400 (1 minute to 24 hours)  
**Required:** No  
**Example:** `VPN_CACHE_TTL=7200`

```bash
# Increase cache duration
export VPN_CACHE_TTL=7200

# Decrease cache duration for real-time data
export VPN_CACHE_TTL=300
```

## Machine Learning Configuration

### VPN_ML_ENABLED

**Description:** Enable machine learning features  
**Type:** Boolean  
**Default:** `false`  
**Required:** No  
**Example:** `VPN_ML_ENABLED=true`

```bash
# Enable ML features
export VPN_ML_ENABLED=true
```

### VPN_ML_MODEL_PATH

**Description:** Path to ML model file  
**Type:** String (file path)  
**Default:** None  
**Required:** No (if ML is disabled)  
**Example:** `VPN_ML_MODEL_PATH=/models/vpn_quality_model.pkl`

```bash
# Set custom model path
export VPN_ML_MODEL_PATH="/models/vpn_quality_model.pkl"
```

### VPN_ML_PREDICTION_THRESHOLD

**Description:** Threshold for ML predictions (0.0-1.0)  
**Type:** Float  
**Default:** `0.7`  
**Range:** 0.0-1.0  
**Required:** No  
**Example:** `VPN_ML_PREDICTION_THRESHOLD=0.8`

```bash
# Increase prediction threshold
export VPN_ML_PREDICTION_THRESHOLD=0.8

# Decrease threshold for more predictions
export VPN_ML_PREDICTION_THRESHOLD=0.5
```

## Performance Configuration

### VPN_CHUNK_SIZE

**Description:** Chunk size for data processing in bytes  
**Type:** Integer  
**Default:** `1048576` (1MB)  
**Range:** 1024-10485760 (1KB-10MB)  
**Required:** No  
**Example:** `VPN_CHUNK_SIZE=2097152`

```bash
# Increase chunk size for better performance
export VPN_CHUNK_SIZE=2097152

# Decrease chunk size for memory-constrained systems
export VPN_CHUNK_SIZE=524288
```

### VPN_SEMAPHORE_LIMIT

**Description:** Semaphore limit for concurrent operations  
**Type:** Integer  
**Default:** `20`  
**Range:** 1-100  
**Required:** No  
**Example:** `VPN_SEMAPHORE_LIMIT=50`

```bash
# Increase semaphore limit
export VPN_SEMAPHORE_LIMIT=50
```

### VPN_BLOOM_FILTER_SIZE

**Description:** Size of Bloom filter for deduplication  
**Type:** Integer  
**Default:** `1000000`  
**Range:** 10000-10000000  
**Required:** No  
**Example:** `VPN_BLOOM_FILTER_SIZE=2000000`

```bash
# Increase Bloom filter size
export VPN_BLOOM_FILTER_SIZE=2000000
```

## Web Server Configuration

### VPN_WEB_HOST

**Description:** Host address for web server  
**Type:** String (IP address or hostname)  
**Default:** `0.0.0.0`  
**Required:** No  
**Example:** `VPN_WEB_HOST=127.0.0.1`

```bash
# Bind to localhost only
export VPN_WEB_HOST=127.0.0.1

# Bind to specific interface
export VPN_WEB_HOST=192.168.1.100
```

### VPN_WEB_PORT

**Description:** Port number for web server  
**Type:** Integer  
**Default:** `8000`  
**Range:** 1-65535  
**Required:** No  
**Example:** `VPN_WEB_PORT=9000`

```bash
# Use custom port
export VPN_WEB_PORT=9000
```

### VPN_WEB_CORS_ORIGINS

**Description:** CORS allowed origins (comma-separated)  
**Type:** String  
**Default:** `*`  
**Required:** No  
**Example:** `VPN_WEB_CORS_ORIGINS=https://test-server.example,https://app.test-server.example`

```bash
# Allow specific origins
export VPN_WEB_CORS_ORIGINS="https://test-server.example,https://app.test-server.example"

# Allow all origins (default)
export VPN_WEB_CORS_ORIGINS="*"
```

## Security Configuration

### VPN_API_KEY

**Description:** API key for authentication (if required)  
**Type:** String  
**Default:** None  
**Required:** No  
**Example:** `VPN_API_KEY=your-secret-api-key`

```bash
# Set API key for authentication
export VPN_API_KEY="your-secret-api-key"
```

### VPN_RATE_LIMIT_RPM

**Description:** Rate limit requests per minute  
**Type:** Integer  
**Default:** `100`  
**Range:** 10-10000  
**Required:** No  
**Example:** `VPN_RATE_LIMIT_RPM=200`

```bash
# Increase rate limit
export VPN_RATE_LIMIT_RPM=200

# Decrease rate limit for security
export VPN_RATE_LIMIT_RPM=50
```

## Testing Configuration

### VPN_TEST_MODE

**Description:** Enable test mode (uses mock data)  
**Type:** Boolean  
**Default:** `false`  
**Required:** No  
**Example:** `VPN_TEST_MODE=true`

```bash
# Enable test mode
export VPN_TEST_MODE=true
```

### VPN_TEST_TIMEOUT

**Description:** Timeout for test operations in seconds  
**Type:** Integer  
**Default:** `10`  
**Range:** 1-60  
**Required:** No  
**Example:** `VPN_TEST_TIMEOUT=30`

```bash
# Increase test timeout
export VPN_TEST_TIMEOUT=30
```

### VPN_TEST_CONCURRENT

**Description:** Concurrent operations for testing  
**Type:** Integer  
**Default:** `10`  
**Range:** 1-100  
**Required:** No  
**Example:** `VPN_TEST_CONCURRENT=20`

```bash
# Increase test concurrency
export VPN_TEST_CONCURRENT=20
```

## Development Configuration

### VPN_DEBUG

**Description:** Enable debug mode  
**Type:** Boolean  
**Default:** `false`  
**Required:** No  
**Example:** `VPN_DEBUG=true`

```bash
# Enable debug mode
export VPN_DEBUG=true
```

### VPN_DEVELOPMENT

**Description:** Enable development mode  
**Type:** Boolean  
**Default:** `false`  
**Required:** No  
**Example:** `VPN_DEVELOPMENT=true`

```bash
# Enable development mode
export VPN_DEVELOPMENT=true
```

### VPN_RELOAD

**Description:** Enable auto-reload for development  
**Type:** Boolean  
**Default:** `false`  
**Required:** No  
**Example:** `VPN_RELOAD=true`

```bash
# Enable auto-reload
export VPN_RELOAD=true
```

## Environment-Specific Configurations

### Development Environment

```bash
# Development configuration
export VPN_LOG_LEVEL=DEBUG
export VPN_DEBUG=true
export VPN_DEVELOPMENT=true
export VPN_RELOAD=true
export VPN_TEST_MODE=true
export VPN_CACHE_ENABLED=false
export VPN_CONCURRENT_LIMIT=10
```

### Staging Environment

```bash
# Staging configuration
export VPN_LOG_LEVEL=INFO
export VPN_DEBUG=false
export VPN_DEVELOPMENT=false
export VPN_TEST_MODE=false
export VPN_CACHE_ENABLED=true
export VPN_REDIS_URL="redis://staging-redis:6379/0"
export VPN_CONCURRENT_LIMIT=25
```

### Production Environment

```bash
# Production configuration
export VPN_LOG_LEVEL=WARNING
export VPN_DEBUG=false
export VPN_DEVELOPMENT=false
export VPN_TEST_MODE=false
export VPN_CACHE_ENABLED=true
export VPN_REDIS_URL="rediss://user:password@prod-redis:6380/0"
export VPN_CONCURRENT_LIMIT=100
export VPN_API_KEY="production-api-key"
export VPN_RATE_LIMIT_RPM=200
export VPN_OUTPUT_DIR="/var/lib/vpn-merger/output"
export VPN_LOG_FILE="/var/log/vpn-merger.log"
```

## Docker Environment Variables

### Docker Compose Example

```yaml
version: '3.8'
services:
  vpn-merger:
    image: vpn-merger:latest
    environment:
      # Core configuration
      - VPN_SOURCES_CONFIG=/app/config/sources.yaml
      - VPN_CONCURRENT_LIMIT=50
      - VPN_TIMEOUT=30
      
      # Output configuration
      - VPN_OUTPUT_DIR=/app/output
      - VPN_WRITE_BASE64=true
      - VPN_WRITE_CSV=true
      - VPN_WRITE_JSON=true
      
      # Logging configuration
      - VPN_LOG_LEVEL=INFO
      - VPN_LOG_FILE=/app/logs/vpn-merger.log
      
      # Cache configuration
      - VPN_CACHE_ENABLED=true
      - VPN_REDIS_URL=redis://redis:6379/0
      
      # Web server configuration
      - VPN_WEB_HOST=0.0.0.0
      - VPN_WEB_PORT=8000
      
      # Security configuration
      - VPN_API_KEY=${VPN_API_KEY}
      - VPN_RATE_LIMIT_RPM=100
    volumes:
      - ./config:/app/config:ro
      - ./output:/app/output:rw
      - ./logs:/app/logs:rw
    ports:
      - "8000:8000"
```

### Docker Run Example

```bash
docker run -d \
  --name vpn-merger \
  -p 8000:8000 \
  -e VPN_SOURCES_CONFIG=/app/config/sources.yaml \
  -e VPN_CONCURRENT_LIMIT=50 \
  -e VPN_CACHE_ENABLED=true \
  -e VPN_REDIS_URL=redis://redis:6379/0 \
  -e VPN_LOG_LEVEL=INFO \
  -v ./config:/app/config:ro \
  -v ./output:/app/output:rw \
  vpn-merger:latest
```

## Kubernetes Environment Variables

### ConfigMap Example

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vpn-merger-config
data:
  VPN_SOURCES_CONFIG: "/app/config/sources.yaml"
  VPN_CONCURRENT_LIMIT: "50"
  VPN_TIMEOUT: "30"
  VPN_OUTPUT_DIR: "/app/output"
  VPN_LOG_LEVEL: "INFO"
  VPN_CACHE_ENABLED: "true"
  VPN_WEB_HOST: "0.0.0.0"
  VPN_WEB_PORT: "8000"
```

### Secret Example

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: vpn-merger-secrets
type: Opaque
data:
  VPN_API_KEY: <base64-encoded-api-key>
  VPN_REDIS_URL: <base64-encoded-redis-url>
```

### Deployment Example

```yaml
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
        envFrom:
        - configMapRef:
            name: vpn-merger-config
        - secretRef:
            name: vpn-merger-secrets
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
        - name: output-volume
          mountPath: /app/output
      volumes:
      - name: config-volume
        configMap:
          name: vpn-merger-config
      - name: output-volume
        persistentVolumeClaim:
          claimName: vpn-merger-output-pvc
```

## Validation and Error Handling

### Environment Variable Validation

```python
import os
from typing import Dict, Any, Optional

def validate_environment_variables() -> Dict[str, Any]:
    """Validate all environment variables."""
    
    validation_results = {}
    
    # Validate VPN_CONCURRENT_LIMIT
    concurrent_limit = os.environ.get('VPN_CONCURRENT_LIMIT')
    if concurrent_limit:
        try:
            limit = int(concurrent_limit)
            if not (1 <= limit <= 1000):
                validation_results['VPN_CONCURRENT_LIMIT'] = {
                    'valid': False,
                    'error': 'Value must be between 1 and 1000'
                }
            else:
                validation_results['VPN_CONCURRENT_LIMIT'] = {
                    'valid': True,
                    'value': limit
                }
        except ValueError:
            validation_results['VPN_CONCURRENT_LIMIT'] = {
                'valid': False,
                'error': 'Value must be an integer'
            }
    
    # Validate VPN_LOG_LEVEL
    log_level = os.environ.get('VPN_LOG_LEVEL')
    if log_level:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level.upper() not in valid_levels:
            validation_results['VPN_LOG_LEVEL'] = {
                'valid': False,
                'error': f'Value must be one of: {", ".join(valid_levels)}'
            }
        else:
            validation_results['VPN_LOG_LEVEL'] = {
                'valid': True,
                'value': log_level.upper()
            }
    
    return validation_results
```

### Configuration Loading

```python
import os
from typing import Dict, Any

def load_configuration() -> Dict[str, Any]:
    """Load configuration from environment variables with defaults."""
    
    config = {
        # Core configuration
        'sources_config': os.environ.get('VPN_SOURCES_CONFIG', 'config/sources.yaml'),
        'concurrent_limit': int(os.environ.get('VPN_CONCURRENT_LIMIT', '50')),
        'timeout': int(os.environ.get('VPN_TIMEOUT', '30')),
        'max_retries': int(os.environ.get('VPN_MAX_RETRIES', '3')),
        
        # Output configuration
        'output_dir': os.environ.get('VPN_OUTPUT_DIR', 'output'),
        'write_base64': os.environ.get('VPN_WRITE_BASE64', 'true').lower() == 'true',
        'write_csv': os.environ.get('VPN_WRITE_CSV', 'true').lower() == 'true',
        'write_json': os.environ.get('VPN_WRITE_JSON', 'true').lower() == 'true',
        'write_singbox': os.environ.get('VPN_WRITE_SINGBOX', 'true').lower() == 'true',
        'write_clash': os.environ.get('VPN_WRITE_CLASH', 'true').lower() == 'true',
        
        # Logging configuration
        'log_level': os.environ.get('VPN_LOG_LEVEL', 'INFO').upper(),
        'log_file': os.environ.get('VPN_LOG_FILE'),
        'log_max_size': int(os.environ.get('VPN_LOG_MAX_SIZE', '10')),
        'log_backup_count': int(os.environ.get('VPN_LOG_BACKUP_COUNT', '3')),
        
        # Cache configuration
        'cache_enabled': os.environ.get('VPN_CACHE_ENABLED', 'true').lower() == 'true',
        'redis_url': os.environ.get('VPN_REDIS_URL'),
        'cache_ttl': int(os.environ.get('VPN_CACHE_TTL', '3600')),
        
        # Web server configuration
        'web_host': os.environ.get('VPN_WEB_HOST', '0.0.0.0'),
        'web_port': int(os.environ.get('VPN_WEB_PORT', '8000')),
        'cors_origins': os.environ.get('VPN_WEB_CORS_ORIGINS', '*'),
        
        # Security configuration
        'api_key': os.environ.get('VPN_API_KEY'),
        'rate_limit_rpm': int(os.environ.get('VPN_RATE_LIMIT_RPM', '100')),
        
        # Development configuration
        'debug': os.environ.get('VPN_DEBUG', 'false').lower() == 'true',
        'development': os.environ.get('VPN_DEVELOPMENT', 'false').lower() == 'true',
        'test_mode': os.environ.get('VPN_TEST_MODE', 'false').lower() == 'true',
    }
    
    return config
```

## Web UI Integration

### API_BASE_URL

Points the Web UI to the API server.

- Type: URL
- Default: `http://localhost:8080`

Examples:

```bash
export API_BASE_URL="https://api.test-server.example"
python run_web.py
```

### WEB_CONNECT_SRC_EXTRA

Optional extra CSP `connect-src` origins for the Web UI (space or comma separated). If a token omits a scheme, both http(s) and ws(s) variants are added.

Examples:

```bash
export WEB_CONNECT_SRC_EXTRA="https://api.test-server.example wss://ws.test-server.example"
# or
export WEB_CONNECT_SRC_EXTRA="api.test-server.example:8443, ws.test-server.example:8443"
python run_web.py
```

See also: Web Interface security and CSP details in
`docs/web-interface.md#security-headers--csp`.

## Best Practices

### 1. Use Environment-Specific Files

Create separate environment files for different deployments:

```bash
# .env.development
VPN_LOG_LEVEL=DEBUG
VPN_DEBUG=true
VPN_TEST_MODE=true
VPN_CACHE_ENABLED=false

# .env.staging
VPN_LOG_LEVEL=INFO
VPN_CACHE_ENABLED=true
VPN_REDIS_URL=redis://staging-redis:6379/0

# .env.production
VPN_LOG_LEVEL=WARNING
VPN_CACHE_ENABLED=true
VPN_REDIS_URL=rediss://user:password@prod-redis:6380/0
VPN_API_KEY=production-api-key
```

### 2. Validate Configuration on Startup

```python
def validate_startup_configuration():
    """Validate configuration on application startup."""
    
    validation_results = validate_environment_variables()
    
    errors = []
    for var, result in validation_results.items():
        if not result['valid']:
            errors.append(f"{var}: {result['error']}")
    
    if errors:
        raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))
    
    print("Configuration validation passed")
```

### 3. Use Configuration Classes

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class VPNMergerConfig:
    """Configuration class for VPN Merger."""
    
    # Core configuration
    sources_config: str = 'config/sources.yaml'
    concurrent_limit: int = 50
    timeout: int = 30
    max_retries: int = 3
    
    # Output configuration
    output_dir: str = 'output'
    write_base64: bool = True
    write_csv: bool = True
    write_json: bool = True
    write_singbox: bool = True
    write_clash: bool = True
    
    # Logging configuration
    log_level: str = 'INFO'
    log_file: Optional[str] = None
    log_max_size: int = 10
    log_backup_count: int = 3
    
    # Cache configuration
    cache_enabled: bool = True
    redis_url: Optional[str] = None
    cache_ttl: int = 3600
    
    # Web server configuration
    web_host: str = '0.0.0.0'
    web_port: int = 8000
    cors_origins: str = '*'
    
    # Security configuration
    api_key: Optional[str] = None
    rate_limit_rpm: int = 100
    
    # Development configuration
    debug: bool = False
    development: bool = False
    test_mode: bool = False
    
    @classmethod
    def from_environment(cls) -> 'VPNMergerConfig':
        """Create configuration from environment variables."""
        return cls(
            sources_config=os.environ.get('VPN_SOURCES_CONFIG', 'config/sources.yaml'),
            concurrent_limit=int(os.environ.get('VPN_CONCURRENT_LIMIT', '50')),
            timeout=int(os.environ.get('VPN_TIMEOUT', '30')),
            max_retries=int(os.environ.get('VPN_MAX_RETRIES', '3')),
            output_dir=os.environ.get('VPN_OUTPUT_DIR', 'output'),
            write_base64=os.environ.get('VPN_WRITE_BASE64', 'true').lower() == 'true',
            write_csv=os.environ.get('VPN_WRITE_CSV', 'true').lower() == 'true',
            write_json=os.environ.get('VPN_WRITE_JSON', 'true').lower() == 'true',
            write_singbox=os.environ.get('VPN_WRITE_SINGBOX', 'true').lower() == 'true',
            write_clash=os.environ.get('VPN_WRITE_CLASH', 'true').lower() == 'true',
            log_level=os.environ.get('VPN_LOG_LEVEL', 'INFO').upper(),
            log_file=os.environ.get('VPN_LOG_FILE'),
            log_max_size=int(os.environ.get('VPN_LOG_MAX_SIZE', '10')),
            log_backup_count=int(os.environ.get('VPN_LOG_BACKUP_COUNT', '3')),
            cache_enabled=os.environ.get('VPN_CACHE_ENABLED', 'true').lower() == 'true',
            redis_url=os.environ.get('VPN_REDIS_URL'),
            cache_ttl=int(os.environ.get('VPN_CACHE_TTL', '3600')),
            web_host=os.environ.get('VPN_WEB_HOST', '0.0.0.0'),
            web_port=int(os.environ.get('VPN_WEB_PORT', '8000')),
            cors_origins=os.environ.get('VPN_WEB_CORS_ORIGINS', '*'),
            api_key=os.environ.get('VPN_API_KEY'),
            rate_limit_rpm=int(os.environ.get('VPN_RATE_LIMIT_RPM', '100')),
            debug=os.environ.get('VPN_DEBUG', 'false').lower() == 'true',
            development=os.environ.get('VPN_DEVELOPMENT', 'false').lower() == 'true',
            test_mode=os.environ.get('VPN_TEST_MODE', 'false').lower() == 'true',
        )
```

This page summarizes the environment variables needed to configure the VPN Subscription Merger across different environments.
