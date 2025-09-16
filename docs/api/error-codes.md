# Error Codes Reference

## Overview

This document lists error codes, HTTP status codes, and error handling patterns used in the StreamlineVPN API.

## Common Errors Matrix

| Error | HTTP | Typical Endpoint(s) | When it happens |
|-------|------|----------------------|-----------------|
| `VALIDATION_ERROR` | 400 | `POST /api/v1/pipeline/run`, `POST /api/v1/sources` | Request payload invalid or missing fields |
| `JOB_NOT_FOUND` | 404 | `GET /api/v1/pipeline/status/{job_id}` | Unknown job ID |
| `SOURCE_FETCH_FAILED` | 502 | `GET /api/v1/configurations` (internal), pipeline | Upstream fetch failed |
| `SOURCE_TIMEOUT` | 504 | Pipeline, fetchers | Upstream timeout |
| `RATE_LIMIT_EXCEEDED` | 429 | Any | Client or upstream rate limit triggered |
| `ACCESS_DENIED` | 403 | Protected endpoints (if enabled) | Missing permission |
| `INVALID_API_KEY` | 401 | Any (if auth enabled) | Bad or missing API key |
| `SERVICE_UNAVAILABLE` | 503 | `GET /api/v1/statistics` (if merger not ready) | Service not initialized |

The sections below provide detailed schemas and examples.

## HTTP Status Codes

### 2xx Success

| Code | Name | Description |
|------|------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 202 | Accepted | Request accepted for processing |

### 4xx Client Errors

| Code | Name | Description |
|------|------|-------------|
| 400 | Bad Request | Invalid request parameters or malformed request |
| 401 | Unauthorized | Authentication required or invalid credentials |
| 403 | Forbidden | Access denied, insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate source) |
| 422 | Unprocessable Entity | Valid request but semantic errors |
| 429 | Too Many Requests | Rate limit exceeded |

### 5xx Server Errors

| Code | Name | Description |
|------|------|-------------|
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | Upstream service error |
| 503 | Service Unavailable | Service temporarily unavailable |
| 504 | Gateway Timeout | Upstream service timeout |

## API Error Response Format

All API errors follow a consistent JSON format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional error details",
    "timestamp": "2023-12-01T10:00:00Z"
  },
  "request_id": "req_123456789"
}
```

## Error Codes

### Configuration Generation Errors

#### VLESS Configuration Errors

| Code | HTTP | Description | Resolution |
|------|------|-------------|------------|
| `VLESS_INVALID_HOST` | 400 | Invalid host format | Provide valid hostname or IP |
| `VLESS_INVALID_PORT` | 400 | Port out of range (1-65535) | Use valid port number |
| `VLESS_INVALID_UUID` | 400 | Invalid UUID format | Provide valid UUID v4 |
| `VLESS_INVALID_SERVER_NAME` | 400 | Invalid server name for REALITY | Use valid domain name |
| `VLESS_INVALID_DEST` | 400 | Invalid destination format | Use format "host:port" |
| `VLESS_MISSING_REQUIRED_FIELD` | 400 | Missing required field | Provide all required fields |

**Example:**
```json
{
  "error": "VLESS_INVALID_UUID",
  "message": "Invalid UUID format. Expected UUID v4 format.",
  "details": {
    "field": "uuid",
    "provided": "invalid-uuid",
    "expected_format": "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
  }
}
```

#### WireGuard Configuration Errors

| Code | HTTP | Description | Resolution |
|------|------|-------------|------------|
| `WG_INVALID_PUBLIC_KEY` | 400 | Invalid public key format | Provide valid WireGuard public key |
| `WG_INVALID_PRIVATE_KEY` | 400 | Invalid private key format | Provide valid WireGuard private key |
| `WG_INVALID_ENDPOINT` | 400 | Invalid endpoint format | Use format "host:port" |
| `WG_INVALID_ALLOWED_IPS` | 400 | Invalid allowed IPs format | Use CIDR notation |
| `WG_KEY_GENERATION_FAILED` | 500 | Failed to generate keys | Retry request |

**Example:**
```json
{
  "error": "WG_INVALID_PUBLIC_KEY",
  "message": "Invalid WireGuard public key format",
  "details": {
    "field": "server_public_key",
    "provided": "invalid-key",
    "expected_length": 44,
    "expected_format": "Base64 encoded"
  }
}
```

#### Shadowsocks Configuration Errors

| Code | HTTP | Description | Resolution |
|------|------|-------------|------------|
| `SS_INVALID_METHOD` | 400 | Unsupported encryption method | Use supported method |
| `SS_INVALID_PASSWORD` | 400 | Password too short or invalid | Use password 8+ characters |
| `SS_INVALID_PLUGIN` | 400 | Invalid plugin configuration | Check plugin options |
| `SS_PASSWORD_TOO_WEAK` | 400 | Password doesn't meet security requirements | Use stronger password |

**Example:**
```json
{
  "error": "SS_INVALID_METHOD",
  "message": "Unsupported encryption method",
  "details": {
    "field": "method",
    "provided": "aes-128-cfb",
    "supported_methods": [
      "aes-256-gcm",
      "aes-128-gcm",
      "chacha20-ietf-poly1305",
      "xchacha20-ietf-poly1305"
    ]
  }
}
```

### Source Processing Errors

| Code | HTTP | Description | Resolution |
|------|------|-------------|------------|
| `SOURCE_FETCH_FAILED` | 502 | Failed to fetch source | Check source URL accessibility |
| `SOURCE_TIMEOUT` | 504 | Source request timeout | Increase timeout or retry |
| `SOURCE_INVALID_FORMAT` | 422 | Invalid source format | Check source content format |
| `SOURCE_EMPTY` | 422 | Source returned empty content | Verify source has content |
| `SOURCE_TOO_LARGE` | 413 | Source content too large | Source exceeds size limit |
| `SOURCE_RATE_LIMITED` | 429 | Source rate limited | Wait and retry |

**Example:**
```json
{
  "error": "SOURCE_FETCH_FAILED",
  "message": "Failed to fetch source URL",
  "details": {
    "source_url": "https://test-server.example/sources.txt",
    "status_code": 404,
    "error": "Not Found"
  }
}
```

### Job Management Errors

| Code | HTTP | Description | Resolution |
|------|------|-------------|------------|
| `JOB_NOT_FOUND` | 404 | Job ID not found | Use valid job ID |
| `JOB_ALREADY_COMPLETED` | 409 | Job already completed | Cannot modify completed job |
| `JOB_ALREADY_CANCELLED` | 409 | Job already cancelled | Cannot modify cancelled job |
| `JOB_CREATION_FAILED` | 500 | Failed to create job | Retry request |
| `JOB_CANCELLATION_FAILED` | 500 | Failed to cancel job | Retry request |

**Example:**
```json
{
  "error": "JOB_NOT_FOUND",
  "message": "Job not found",
  "details": {
    "job_id": "job_123456",
    "available_jobs": ["job_789012", "job_345678"]
  }
}
```

### Validation Errors

| Code | HTTP | Description | Resolution |
|------|------|-------------|------------|
| `VALIDATION_ERROR` | 400 | General validation error | Check request parameters |
| `MISSING_REQUIRED_FIELD` | 400 | Required field missing | Provide all required fields |
| `INVALID_FIELD_TYPE` | 400 | Invalid field type | Use correct data type |
| `FIELD_TOO_LONG` | 400 | Field value too long | Reduce field length |
| `FIELD_TOO_SHORT` | 400 | Field value too short | Increase field length |
| `INVALID_REGEX` | 400 | Invalid regex pattern | Use valid regex syntax |
| `INVALID_URL` | 400 | Invalid URL format | Use valid URL format |

**Example:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {
    "errors": [
      {
        "field": "host",
        "message": "Host is required",
        "code": "MISSING_REQUIRED_FIELD"
      },
      {
        "field": "port",
        "message": "Port must be between 1 and 65535",
        "code": "INVALID_FIELD_TYPE",
        "provided": "abc",
        "expected": "integer"
      }
    ]
  }
}
```

### Security Errors

| Code | HTTP | Description | Resolution |
|------|------|-------------|------------|
| `SECURITY_THREAT_DETECTED` | 400 | Potential security threat | Remove malicious content |
| `INPUT_TOO_LARGE` | 413 | Input data too large | Reduce input size |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded | Wait and retry |
| `INVALID_API_KEY` | 401 | Invalid API key | Use valid API key |
| `ACCESS_DENIED` | 403 | Access denied | Check permissions |

**Example:**
```json
{
  "error": "SECURITY_THREAT_DETECTED",
  "message": "Potentially malicious input detected",
  "details": {
    "threat_type": "script_injection",
    "detected_pattern": "<script",
    "field": "remark"
  }
}
```

### System Errors

| Code | HTTP | Description | Resolution |
|------|------|-------------|------------|
| `INTERNAL_ERROR` | 500 | Internal server error | Contact support |
| `DATABASE_ERROR` | 500 | Database operation failed | Retry request |
| `CACHE_ERROR` | 500 | Cache operation failed | Retry request |
| `CONFIGURATION_ERROR` | 500 | Configuration error | Check system configuration |
| `MEMORY_ERROR` | 500 | Memory allocation failed | Reduce request size |
| `NETWORK_ERROR` | 502 | Network connectivity error | Check network connection |

**Example:**
```json
{
  "error": "INTERNAL_ERROR",
  "message": "An unexpected error occurred",
  "details": {
    "error_id": "err_123456789",
    "timestamp": "2023-12-01T10:00:00Z",
    "component": "source_processor"
  }
}
```

## GraphQL Error Codes

GraphQL errors use the same error codes but with additional context:

```json
{
  "errors": [
    {
      "message": "Invalid job ID",
      "locations": [
        {
          "line": 2,
          "column": 3
        }
      ],
      "path": [
        "job"
      ],
      "extensions": {
        "code": "JOB_NOT_FOUND",
        "details": {
          "job_id": "invalid_job_id"
        }
      }
    }
  ]
}
```

## Error Handling Best Practices

### Client-Side Error Handling

```javascript
async function handleApiRequest(url, options) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      
      switch (error.error) {
        case 'RATE_LIMIT_EXCEEDED':
          // Wait and retry
          await new Promise(resolve => setTimeout(resolve, 1000));
          return handleApiRequest(url, options);
          
        case 'VALIDATION_ERROR':
          // Show validation errors to user
          showValidationErrors(error.details.errors);
          break;
          
        case 'JOB_NOT_FOUND':
          // Handle missing job
          showError('Job not found');
          break;
          
        default:
          // Generic error handling
          showError(error.message);
      }
      
      throw new Error(error.message);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}
```

### Retry Logic

```javascript
async function retryRequest(requestFn, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      if (attempt === maxRetries) {
        throw error;
      }
      
      // Only retry on specific errors
      if (error.error === 'RATE_LIMIT_EXCEEDED' || 
          error.error === 'SOURCE_TIMEOUT' ||
          error.error === 'NETWORK_ERROR') {
        const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      
      throw error;
    }
  }
}
```

### Error Monitoring

```javascript
function logError(error, context = {}) {
  const errorData = {
    error: error.error || 'UNKNOWN_ERROR',
    message: error.message,
    details: error.details,
    context,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    url: window.location.href
  };
  
  // Send to error monitoring service
  fetch('/api/v1/errors', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(errorData)
  }).catch(console.error);
}
```

## Troubleshooting Common Errors

### 1. Rate Limit Exceeded

**Symptoms:** 429 status code with `RATE_LIMIT_EXCEEDED` error

**Solutions:**
- Implement exponential backoff
- Reduce request frequency
- Use batch operations when possible
- Consider upgrading rate limits

### 2. Source Fetch Failures

**Symptoms:** 502/504 status codes with `SOURCE_FETCH_FAILED` or `SOURCE_TIMEOUT`

**Solutions:**
- Verify source URLs are accessible
- Check network connectivity
- Increase timeout values
- Use alternative sources

### 3. Validation Errors

**Symptoms:** 400 status code with `VALIDATION_ERROR`

**Solutions:**
- Check request parameters
- Validate input data before sending
- Use proper data types
- Follow API documentation

### 4. Job Not Found

**Symptoms:** 404 status code with `JOB_NOT_FOUND`

**Solutions:**
- Use valid job IDs
- Check job status before operations
- Implement proper job lifecycle management

## Error Code Constants

For programmatic use, here are the error code constants:

```python
class ErrorCodes:
    # Configuration Generation
    VLESS_INVALID_HOST = "VLESS_INVALID_HOST"
    VLESS_INVALID_PORT = "VLESS_INVALID_PORT"
    VLESS_INVALID_UUID = "VLESS_INVALID_UUID"
    WG_INVALID_PUBLIC_KEY = "WG_INVALID_PUBLIC_KEY"
    WG_INVALID_PRIVATE_KEY = "WG_INVALID_PRIVATE_KEY"
    SS_INVALID_METHOD = "SS_INVALID_METHOD"
    
    # Source Processing
    SOURCE_FETCH_FAILED = "SOURCE_FETCH_FAILED"
    SOURCE_TIMEOUT = "SOURCE_TIMEOUT"
    SOURCE_INVALID_FORMAT = "SOURCE_INVALID_FORMAT"
    
    # Job Management
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    JOB_ALREADY_COMPLETED = "JOB_ALREADY_COMPLETED"
    
    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    
    # Security
    SECURITY_THREAT_DETECTED = "SECURITY_THREAT_DETECTED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # System
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
```

```javascript
const ErrorCodes = {
  // Configuration Generation
  VLESS_INVALID_HOST: 'VLESS_INVALID_HOST',
  VLESS_INVALID_PORT: 'VLESS_INVALID_PORT',
  VLESS_INVALID_UUID: 'VLESS_INVALID_UUID',
  WG_INVALID_PUBLIC_KEY: 'WG_INVALID_PUBLIC_KEY',
  WG_INVALID_PRIVATE_KEY: 'WG_INVALID_PRIVATE_KEY',
  SS_INVALID_METHOD: 'SS_INVALID_METHOD',
  
  // Source Processing
  SOURCE_FETCH_FAILED: 'SOURCE_FETCH_FAILED',
  SOURCE_TIMEOUT: 'SOURCE_TIMEOUT',
  SOURCE_INVALID_FORMAT: 'SOURCE_INVALID_FORMAT',
  
  // Job Management
  JOB_NOT_FOUND: 'JOB_NOT_FOUND',
  JOB_ALREADY_COMPLETED: 'JOB_ALREADY_COMPLETED',
  
  // Validation
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  MISSING_REQUIRED_FIELD: 'MISSING_REQUIRED_FIELD',
  
  // Security
  SECURITY_THREAT_DETECTED: 'SECURITY_THREAT_DETECTED',
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',
  
  // System
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  DATABASE_ERROR: 'DATABASE_ERROR'
};
```
