# Configuration Schema Validation

## Overview

This guide describes the schema validation used to ensure configuration integrity, security, and proper operation. It outlines the key rules and error handling for configuration components.

## Configuration Files

### Main Configuration Schema

The primary configuration file `config/sources.yaml` follows this schema:

```yaml
# YAML Schema for sources.yaml
sources:
  tier_1_premium:      # Array of strings (URLs)
    - type: string
      format: uri
      minLength: 1
      maxLength: 2048
  tier_2_reliable:     # Array of strings (URLs)
    - type: string
      format: uri
      minLength: 1
      maxLength: 2048
  tier_3_bulk:         # Array of strings (URLs)
    - type: string
      format: uri
      minLength: 1
      maxLength: 2048
  specialized:         # Array of strings (URLs)
    - type: string
      format: uri
      minLength: 1
      maxLength: 2048
  regional:            # Array of strings (URLs)
    - type: string
      format: uri
      minLength: 1
      maxLength: 2048
  experimental:        # Array of strings (URLs)
    - type: string
      format: uri
      minLength: 1
      maxLength: 2048

# Optional configuration sections
processing:
  max_concurrent:      # Integer, 1-1000, default: 50
    type: integer
    minimum: 1
    maximum: 1000
  batch_size:          # Integer, 1-100, default: 10
    type: integer
    minimum: 1
    maximum: 100
  timeout:             # Integer, 5-300, default: 30
    type: integer
    minimum: 5
    maximum: 300
  max_retries:         # Integer, 0-10, default: 3
    type: integer
    minimum: 0
    maximum: 10

output:
  output_dir:          # String, valid path, default: "output"
    type: string
    pattern: "^[a-zA-Z0-9_/.-]+$"
    minLength: 1
    maxLength: 255
  write_base64:        # Boolean, default: true
    type: boolean
  write_csv:           # Boolean, default: true
    type: boolean
  write_json:          # Boolean, default: true
    type: boolean
  write_singbox:       # Boolean, default: true
    type: boolean
  write_clash:         # Boolean, default: true
    type: boolean

logging:
  level:               # String, enum, default: "INFO"
    type: string
    enum: ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
  file:                # String, valid path, optional
    type: string
    pattern: "^[a-zA-Z0-9_/.-]+$"
    maxLength: 255
  max_size:            # Integer, 1-100, default: 10 (MB)
    type: integer
    minimum: 1
    maximum: 100
  backup_count:        # Integer, 1-10, default: 3
    type: integer
    minimum: 1
    maximum: 10

cache:
  enabled:             # Boolean, default: true
    type: boolean
  redis_url:           # String, valid Redis URL, optional
    type: string
    pattern: "^redis://.*"
  ttl:                 # Integer, 60-86400, default: 3600 (seconds)
    type: integer
    minimum: 60
    maximum: 86400

ml:
  enabled:             # Boolean, default: false
    type: boolean
  model_path:          # String, valid path, optional
    type: string
    pattern: "^[a-zA-Z0-9_/.-]+$"
    maxLength: 255
  prediction_threshold: # Float, 0.0-1.0, default: 0.7
    type: number
    minimum: 0.0
    maximum: 1.0
```

## Validation Rules

### URL Validation

All source URLs must meet these criteria:

```python
import re
from urllib.parse import urlparse

def validate_url(url: str) -> bool:
    """Validate source URL format and accessibility."""
    
    # Basic format validation
    if not isinstance(url, str) or len(url) == 0:
        return False
    
    if len(url) > 2048:
        return False
    
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    
    # Check scheme
    if parsed.scheme not in ['http', 'https']:
        return False
    
    # Check hostname
    if not parsed.hostname:
        return False
    
    # Check for dangerous patterns
    dangerous_patterns = [
        r'\.\./',  # Directory traversal
        r'<script',  # XSS attempts
        r'javascript:',  # JavaScript injection
        r'data:',  # Data URLs
        r'file:',  # File URLs
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return False
    
    return True
```

### Configuration Validation

```python
import yaml
import jsonschema
from pathlib import Path

def validate_configuration(config_path: str) -> dict:
    """Validate configuration file against schema."""
    
    # Load configuration
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return {
            'valid': False,
            'error': 'YAML_PARSE_ERROR',
            'message': f'Failed to parse YAML: {e}'
        }
    except FileNotFoundError:
        return {
            'valid': False,
            'error': 'FILE_NOT_FOUND',
            'message': f'Configuration file not found: {config_path}'
        }
    
    # Validate sources
    if 'sources' not in config:
        return {
            'valid': False,
            'error': 'MISSING_SOURCES',
            'message': 'Sources section is required'
        }
    
    # Validate each source tier
    for tier_name, sources in config['sources'].items():
        if not isinstance(sources, list):
            return {
                'valid': False,
                'error': 'INVALID_SOURCES_FORMAT',
                'message': f'Sources in {tier_name} must be a list'
            }
        
        for i, source in enumerate(sources):
            if not validate_url(source):
                return {
                    'valid': False,
                    'error': 'INVALID_SOURCE_URL',
                    'message': f'Invalid URL in {tier_name}[{i}]: {source}'
                }
    
    # Validate processing settings
    if 'processing' in config:
        processing = config['processing']
        
        if 'max_concurrent' in processing:
            if not isinstance(processing['max_concurrent'], int):
                return {
                    'valid': False,
                    'error': 'INVALID_MAX_CONCURRENT',
                    'message': 'max_concurrent must be an integer'
                }
            if not (1 <= processing['max_concurrent'] <= 1000):
                return {
                    'valid': False,
                    'error': 'INVALID_MAX_CONCURRENT_RANGE',
                    'message': 'max_concurrent must be between 1 and 1000'
                }
    
    return {
        'valid': True,
        'message': 'Configuration is valid'
    }
```

## Environment Variable Validation

### Core Environment Variables

```python
import os
import re
from typing import Dict, Any

def validate_environment_variables() -> Dict[str, Any]:
    """Validate environment variables against schema."""
    
    validation_results = {}
    
    # VPN_SOURCES_CONFIG
    sources_config = os.environ.get('VPN_SOURCES_CONFIG')
    if sources_config:
        if not Path(sources_config).exists():
            validation_results['VPN_SOURCES_CONFIG'] = {
                'valid': False,
                'error': 'FILE_NOT_FOUND',
                'message': f'Configuration file not found: {sources_config}'
            }
        else:
            validation_results['VPN_SOURCES_CONFIG'] = {
                'valid': True,
                'value': sources_config
            }
    
    # VPN_CONCURRENT_LIMIT
    concurrent_limit = os.environ.get('VPN_CONCURRENT_LIMIT')
    if concurrent_limit:
        try:
            limit = int(concurrent_limit)
            if not (1 <= limit <= 1000):
                validation_results['VPN_CONCURRENT_LIMIT'] = {
                    'valid': False,
                    'error': 'INVALID_RANGE',
                    'message': 'Must be between 1 and 1000'
                }
            else:
                validation_results['VPN_CONCURRENT_LIMIT'] = {
                    'valid': True,
                    'value': limit
                }
        except ValueError:
            validation_results['VPN_CONCURRENT_LIMIT'] = {
                'valid': False,
                'error': 'INVALID_TYPE',
                'message': 'Must be an integer'
            }
    
    # VPN_TIMEOUT
    timeout = os.environ.get('VPN_TIMEOUT')
    if timeout:
        try:
            timeout_val = int(timeout)
            if not (5 <= timeout_val <= 300):
                validation_results['VPN_TIMEOUT'] = {
                    'valid': False,
                    'error': 'INVALID_RANGE',
                    'message': 'Must be between 5 and 300 seconds'
                }
            else:
                validation_results['VPN_TIMEOUT'] = {
                    'valid': True,
                    'value': timeout_val
                }
        except ValueError:
            validation_results['VPN_TIMEOUT'] = {
                'valid': False,
                'error': 'INVALID_TYPE',
                'message': 'Must be an integer'
            }
    
    # VPN_OUTPUT_DIR
    output_dir = os.environ.get('VPN_OUTPUT_DIR')
    if output_dir:
        if not re.match(r'^[a-zA-Z0-9_/.-]+$', output_dir):
            validation_results['VPN_OUTPUT_DIR'] = {
                'valid': False,
                'error': 'INVALID_PATH',
                'message': 'Invalid path characters'
            }
        else:
            validation_results['VPN_OUTPUT_DIR'] = {
                'valid': True,
                'value': output_dir
            }
    
    # VPN_LOG_LEVEL
    log_level = os.environ.get('VPN_LOG_LEVEL')
    if log_level:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level.upper() not in valid_levels:
            validation_results['VPN_LOG_LEVEL'] = {
                'valid': False,
                'error': 'INVALID_LEVEL',
                'message': f'Must be one of: {", ".join(valid_levels)}'
            }
        else:
            validation_results['VPN_LOG_LEVEL'] = {
                'valid': True,
                'value': log_level.upper()
            }
    
    return validation_results
```

## API Request Validation

### VLESS Configuration Request

```python
from pydantic import BaseModel, validator, Field
from typing import Optional
import re
import uuid

class VLESSRequest(BaseModel):
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., ge=1, le=65535)
    uuid: str = Field(..., min_length=36, max_length=36)
    server_name: str = Field(..., min_length=1, max_length=255)
    dest: str = Field(..., min_length=1, max_length=255)
    path: Optional[str] = Field("/", min_length=1, max_length=255)
    remark: Optional[str] = Field(None, max_length=100)
    
    @validator('host')
    def validate_host(cls, v):
        # Check for valid hostname or IP
        if not re.match(r'^[a-zA-Z0-9.-]+$', v):
            raise ValueError('Invalid host format')
        return v
    
    @validator('uuid')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid UUID format')
        return v
    
    @validator('server_name')
    def validate_server_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9.-]+$', v):
            raise ValueError('Invalid server name format')
        return v
    
    @validator('dest')
    def validate_dest(cls, v):
        if not re.match(r'^[a-zA-Z0-9.-]+:\d+$', v):
            raise ValueError('Invalid destination format (host:port)')
        return v
    
    @validator('path')
    def validate_path(cls, v):
        if v and not v.startswith('/'):
            raise ValueError('Path must start with /')
        return v
```

### WireGuard Configuration Request

```python
class WireGuardRequest(BaseModel):
    server_public_key: str = Field(..., min_length=44, max_length=44)
    server_endpoint: str = Field(..., min_length=1, max_length=255)
    client_private_key: str = Field(..., min_length=44, max_length=44)
    allowed_ips: Optional[str] = Field("0.0.0.0/0", max_length=255)
    dns: Optional[str] = Field("1.1.1.1", max_length=255)
    persistent_keepalive: Optional[int] = Field(25, ge=0, le=65535)
    interface_name: Optional[str] = Field("wg0", max_length=15)
    
    @validator('server_public_key', 'client_private_key')
    def validate_wg_key(cls, v):
        # WireGuard keys are base64 encoded and 44 characters long
        if not re.match(r'^[A-Za-z0-9+/]{42}[A-Za-z0-9+/=]{2}$', v):
            raise ValueError('Invalid WireGuard key format')
        return v
    
    @validator('server_endpoint')
    def validate_endpoint(cls, v):
        if not re.match(r'^[a-zA-Z0-9.-]+:\d+$', v):
            raise ValueError('Invalid endpoint format (host:port)')
        return v
    
    @validator('allowed_ips')
    def validate_allowed_ips(cls, v):
        # Validate CIDR notation
        cidr_pattern = r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'
        if not re.match(cidr_pattern, v):
            raise ValueError('Invalid CIDR format')
        return v
```

### Shadowsocks Configuration Request

```python
class ShadowsocksRequest(BaseModel):
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., ge=1, le=65535)
    password: str = Field(..., min_length=8, max_length=100)
    method: str = Field(..., max_length=50)
    remark: Optional[str] = Field(None, max_length=100)
    plugin: Optional[str] = Field(None, max_length=50)
    plugin_opts: Optional[str] = Field(None, max_length=255)
    
    @validator('method')
    def validate_method(cls, v):
        valid_methods = [
            'aes-256-gcm',
            'aes-128-gcm',
            'chacha20-ietf-poly1305',
            'xchacha20-ietf-poly1305'
        ]
        if v not in valid_methods:
            raise ValueError(f'Invalid method. Must be one of: {", ".join(valid_methods)}')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        # Check password strength
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain letters')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain numbers')
        return v
```

## Validation Error Handling

### Error Response Format

```python
class ValidationError(Exception):
    def __init__(self, field: str, message: str, code: str = None):
        self.field = field
        self.message = message
        self.code = code or 'VALIDATION_ERROR'
        super().__init__(self.message)

def format_validation_error(error: ValidationError) -> dict:
    """Format validation error for API response."""
    return {
        'error': error.code,
        'message': error.message,
        'details': {
            'field': error.field,
            'type': 'validation_error'
        }
    }
```

### Validation

```python
def validate_complete_request(data: dict, request_type: str) -> dict:
    """Validate complete API request."""
    
    validation_result = {
        'valid': True,
        'errors': []
    }
    
    try:
        if request_type == 'vless':
            VLESSRequest(**data)
        elif request_type == 'wireguard':
            WireGuardRequest(**data)
        elif request_type == 'shadowsocks':
            ShadowsocksRequest(**data)
        else:
            validation_result['valid'] = False
            validation_result['errors'].append({
                'field': 'request_type',
                'message': f'Unknown request type: {request_type}',
                'code': 'INVALID_REQUEST_TYPE'
            })
    
    except ValidationError as e:
        validation_result['valid'] = False
        validation_result['errors'].append({
            'field': e.field,
            'message': e.message,
            'code': e.code
        })
    
    except Exception as e:
        validation_result['valid'] = False
        validation_result['errors'].append({
            'field': 'general',
            'message': str(e),
            'code': 'VALIDATION_ERROR'
        })
    
    return validation_result
```

## Security Validation

### Input Sanitization

```python
import html
import re

def sanitize_input(input_data: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    
    # HTML escape
    sanitized = html.escape(input_data)
    
    # Remove dangerous patterns
    dangerous_patterns = [
        r'<script.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe.*?</iframe>',
        r'<object.*?</object>',
        r'<embed.*?</embed>',
        r'<link.*?>',
        r'<meta.*?>',
        r'<style.*?</style>',
    ]
    
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Limit length
    if len(sanitized) > 10000:
        sanitized = sanitized[:10000]
    
    return sanitized

def validate_security_threats(data: dict) -> list:
    """Check for potential security threats in input data."""
    
    threats = []
    
    for key, value in data.items():
        if isinstance(value, str):
            # Check for script injection
            if re.search(r'<script|javascript:|on\w+\s*=', value, re.IGNORECASE):
                threats.append({
                    'type': 'script_injection',
                    'field': key,
                    'pattern': 'script_injection'
                })
            
            # Check for SQL injection patterns
            if re.search(r'(union|select|insert|update|delete|drop|create|alter)\s+', value, re.IGNORECASE):
                threats.append({
                    'type': 'sql_injection',
                    'field': key,
                    'pattern': 'sql_injection'
                })
            
            # Check for path traversal
            if re.search(r'\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c', value, re.IGNORECASE):
                threats.append({
                    'type': 'path_traversal',
                    'field': key,
                    'pattern': 'path_traversal'
                })
    
    return threats
```

## Configuration Testing

### Unit Tests for Validation

```python
import pytest
from unittest.mock import patch, mock_open

class TestConfigurationValidation:
    
    def test_valid_configuration(self):
        """Test valid configuration passes validation."""
        config = {
            'sources': {
                'tier_1_premium': ['https://test-server.example/sources.txt'],
                'tier_2_reliable': ['https://example2.com/sources.txt']
            },
            'processing': {
                'max_concurrent': 50,
                'timeout': 30
            }
        }
        
        result = validate_configuration(config)
        assert result['valid'] is True
    
    def test_invalid_url(self):
        """Test invalid URL fails validation."""
        config = {
            'sources': {
                'tier_1_premium': ['invalid-url']
            }
        }
        
        result = validate_configuration(config)
        assert result['valid'] is False
        assert 'INVALID_SOURCE_URL' in result['error']
    
    def test_missing_sources(self):
        """Test missing sources section fails validation."""
        config = {
            'processing': {
                'max_concurrent': 50
            }
        }
        
        result = validate_configuration(config)
        assert result['valid'] is False
        assert 'MISSING_SOURCES' in result['error']
    
    def test_invalid_max_concurrent(self):
        """Test invalid max_concurrent value fails validation."""
        config = {
            'sources': {
                'tier_1_premium': ['https://test-server.example/sources.txt']
            },
            'processing': {
                'max_concurrent': 2000  # Too high
            }
        }
        
        result = validate_configuration(config)
        assert result['valid'] is False
        assert 'INVALID_MAX_CONCURRENT_RANGE' in result['error']

class TestAPIValidation:
    
    def test_valid_vless_request(self):
        """Test valid VLESS request passes validation."""
        request_data = {
            'host': 'test-server.example',
            'port': 443,
            'uuid': '550e8400-e29b-41d4-a716-446655440000',
            'server_name': 'www.microsoft.com',
            'dest': 'www.microsoft.com:443',
            'path': '/vless',
            'remark': 'Test Server'
        }
        
        result = validate_complete_request(request_data, 'vless')
        assert result['valid'] is True
    
    def test_invalid_uuid(self):
        """Test invalid UUID fails validation."""
        request_data = {
            'host': 'test-server.example',
            'port': 443,
            'uuid': 'invalid-uuid',
            'server_name': 'www.microsoft.com',
            'dest': 'www.microsoft.com:443'
        }
        
        result = validate_complete_request(request_data, 'vless')
        assert result['valid'] is False
        assert any(error['field'] == 'uuid' for error in result['errors'])
```

## Best Practices

### 1. Validate Early and Often

```python
def process_request(data: dict) -> dict:
    """Process API request with comprehensive validation."""
    
    # 1. Security validation
    threats = validate_security_threats(data)
    if threats:
        return {
            'error': 'SECURITY_THREAT_DETECTED',
            'message': 'Potential security threat detected',
            'details': {'threats': threats}
        }
    
    # 2. Schema validation
    validation_result = validate_complete_request(data, data.get('type'))
    if not validation_result['valid']:
        return {
            'error': 'VALIDATION_ERROR',
            'message': 'Request validation failed',
            'details': {'errors': validation_result['errors']}
        }
    
    # 3. Business logic validation
    # ... additional validation logic
    
    return {'success': True}
```

### 2. Provide Clear Error Messages

```python
def get_validation_error_message(field: str, error_type: str) -> str:
    """Get user-friendly validation error message."""
    
    messages = {
        'host': {
            'required': 'Host is required',
            'invalid_format': 'Host must be a valid hostname or IP address',
            'too_long': 'Host name is too long (max 255 characters)'
        },
        'port': {
            'required': 'Port is required',
            'invalid_range': 'Port must be between 1 and 65535',
            'invalid_type': 'Port must be a number'
        },
        'uuid': {
            'required': 'UUID is required',
            'invalid_format': 'UUID must be in valid UUID v4 format',
            'too_short': 'UUID is too short'
        }
    }
    
    return messages.get(field, {}).get(error_type, 'Invalid value')
```

### 3. Log Validation Failures

```python
import logging

logger = logging.getLogger(__name__)

def log_validation_failure(field: str, value: str, error: str):
    """Log validation failures for monitoring."""
    
    logger.warning(
        f"Validation failed: field={field}, value={value[:50]}..., error={error}",
        extra={
            'field': field,
            'error': error,
            'validation_type': 'schema_validation'
        }
    )
```

This comprehensive schema validation system ensures that all configuration data is properly validated, sanitized, and secure before being processed by the VPN Subscription Merger system.
