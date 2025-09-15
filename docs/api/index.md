---
layout: default
title: API Documentation
description: Comprehensive REST API reference for StreamlineVPN
---

# StreamlineVPN API Documentation

## Overview

StreamlineVPN provides a comprehensive REST API for managing VPN configuration aggregation, processing, and retrieval. The API is built with FastAPI and provides both synchronous and asynchronous endpoints.

**Base URL**: `http://localhost:8080/api/v1`  
**API Version**: v1  
**API Versioning Strategy**: [Read our versioning strategy](versioning.md)
**Content-Type**: `application/json`

## Authentication

Currently, the API supports optional token-based authentication:

```bash
# Optional API key authentication
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8080/api/v1/statistics
```

Set the `STREAMLINE_API_KEY` environment variable to enable authentication.

## Rate Limiting

- **Default**: 100 requests per minute per client
- **Burst**: 20 additional requests
- **Headers**: Rate limit info included in response headers

## Health and Status Endpoints

### GET /health

Returns the API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-14T10:30:00Z",
  "version": "2.0.0",
  "uptime": 3600.5
}
```

### GET /api/v1/statistics

Returns comprehensive system statistics.

**Response:**
```json
{
  "total_sources": 25,
  "active_sources": 23,
  "total_configurations": 1547,
  "total_configs": 1547,
  "success_rate": 0.85,
  "avg_response_time": 2.3,
  "total_processing_time": 45.2,
  "configs_per_source": 67.2,
  "start_time": "2025-01-14T10:00:00Z",
  "end_time": "2025-01-14T10:30:00Z",
  "last_update": "2025-01-14T10:30:00Z"
}
```

## Configuration Management

### GET /api/v1/configurations

Retrieve processed VPN configurations with filtering and pagination.

**Query Parameters:**
- `protocol` (string): Filter by protocol (vmess, vless, trojan, shadowsocks)
- `location` (string): Filter by server location/country
- `min_quality` (float): Minimum quality score (0.0-1.0)
- `limit` (integer): Number of results (default: 100, max: 1000)
- `offset` (integer): Results offset for pagination (default: 0)

**Example Request:**
```bash
curl "http://localhost:8080/api/v1/configurations?protocol=vmess&limit=50&min_quality=0.7"
```

**Response:**
```json
{
  "total": 1547,
  "limit": 50,
  "offset": 0,
  "configurations": [
    {
      "id": "cfg_123456",
      "protocol": "vmess",
      "server": "test-server.example",
      "port": 443,
      "user_id": "12345678-1234-1234-1234-123456789012",
      "alter_id": 0,
      "security": "aes-128-gcm",
      "network": "ws",
      "path": "/path",
      "host": "test-server.example",
      "tls": "tls",
      "quality_score": 0.85,
      "location": {
        "country": "US",
        "region": "California",
        "city": "San Francisco"
      },
      "metadata": {
        "source_url": "https://test-server.example/configs",
        "last_tested": "2025-01-14T10:25:00Z",
        "response_time": 120,
        "success_rate": 0.92
      },
      "created_at": "2025-01-14T10:00:00Z",
      "updated_at": "2025-01-14T10:25:00Z"
    }
  ]
}
```

### GET /api/v1/configurations/{config_id}

Retrieve a specific configuration by ID.

**Path Parameters:**
- `config_id` (string): Configuration identifier

**Response:**
```json
{
  "id": "cfg_123456",
  "protocol": "vmess",
  "server": "test-server.example",
  "port": 443,
  "configuration_url": "vmess://eyJ2IjoyLCJwcyI6InRlc3QiLCJhZGQiOiJleGFtcGxlLmNvbSI...",
  "quality_score": 0.85,
  "test_results": {
    "last_test": "2025-01-14T10:25:00Z",
    "response_time": 120,
    "success": true,
    "error": null
  }
}
```

## Source Management

### GET /api/v1/sources

List all configured sources with their status and performance metrics.

**Response:**
```json
{
  "sources": [
    {
      "id": "src_123",
      "url": "https://test-server.example/configs",
      "tier": "premium",
      "status": "active",
      "enabled": true,
      "configs": 67,
      "success_rate": 0.92,
      "avg_response_time": 2.1,
      "last_update": "2025-01-14T10:25:00Z",
      "last_check": "2025-01-14T10:30:00Z",
      "total_requests": 150,
      "failed_requests": 12,
      "reputation_score": 0.88,
      "metadata": {
        "country": "US",
        "provider": "Example Provider",
        "protocols": ["vmess", "vless"]
      }
    }
  ]
}
```

### POST /api/v1/sources

Add a new source to the system.

**Request Body:**
```json
{
  "url": "https://newprovider.com/configs",
  "tier": "community",
  "enabled": true,
  "timeout": 30,
  "retry_count": 3,
  "headers": {
    "User-Agent": "StreamlineVPN/2.0"
  },
  "filters": {
    "protocols": ["vmess", "vless"],
    "min_quality": 0.5
  }
}
```

**Response:**
```json
{
  "id": "src_124",
  "status": "created",
  "message": "Source added successfully",
  "source": {
    "id": "src_124",
    "url": "https://newprovider.com/configs",
    "status": "pending_validation",
    "created_at": "2025-01-14T10:35:00Z"
  }
}
```

### PUT /api/v1/sources/{source_id}

Update an existing source configuration.

**Path Parameters:**
- `source_id` (string): Source identifier

**Request Body:**
```json
{
  "enabled": false,
  "tier": "unreliable",
  "timeout": 60
}
```

### DELETE /api/v1/sources/{source_id}

Remove a source from the system.

**Response:**
```json
{
  "status": "deleted",
  "message": "Source removed successfully"
}
```

## Pipeline Management

### POST /api/v1/pipeline/run

Start a new configuration processing pipeline.

**Request Body:**
```json
{
  "config_path": "config/sources.yaml",
  "output_dir": "output",
  "formats": ["json", "clash", "singbox"],
  "max_concurrent": 50,
  "timeout": 30,
  "force_refresh": false,
  "filters": {
    "min_quality": 0.6,
    "protocols": ["vmess", "vless"],
    "exclude_countries": ["CN", "RU"]
  }
}
```

**Response:**
```json
{
  "job_id": "job_f9853fe17423",
  "status": "accepted",
  "message": "Pipeline job started successfully",
  "estimated_duration": 120,
  "created_at": "2025-01-14T10:40:00Z"
}
```

### GET /api/v1/pipeline/status/{job_id}

Get the status of a running pipeline job.

**Path Parameters:**
- `job_id` (string): Job identifier

**Response:**
```json
{
  "job_id": "job_f9853fe17423",
  "type": "pipeline",
  "status": "running",
  "progress": 75,
  "message": "Processing sources: 18/24 completed",
  "config": {
    "config_path": "config/sources.yaml",
    "output_dir": "output",
    "formats": ["json", "clash", "singbox"]
  },
  "created_at": "2025-01-14T10:40:00Z",
  "started_at": "2025-01-14T10:40:05Z",
  "updated_at": "2025-01-14T10:42:30Z",
  "estimated_completion": "2025-01-14T10:44:00Z",
  "current_stage": {
    "name": "source_processing",
    "progress": 0.75,
    "details": "Processing https://test-server.example/configs"
  },
  "statistics": {
    "sources_processed": 18,
    "sources_remaining": 6,
    "configurations_found": 1205,
    "errors": 2
  }
}
```

### GET /api/v1/pipeline/jobs

List recent pipeline jobs with their status.

**Query Parameters:**
- `limit` (integer): Number of jobs to return (default: 20, max: 100)
- `status` (string): Filter by status (pending, running, completed, failed)

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "job_f9853fe17423",
      "type": "pipeline",
      "status": "completed",
      "progress": 100,
      "created_at": "2025-01-14T10:40:00Z",
      "finished_at": "2025-01-14T10:43:45Z",
      "duration": 225.5,
      "result": {
        "success": true,
        "sources_processed": 24,
        "configurations_found": 1547,
        "output_files": [
          "output/configurations.json",
          "output/configurations_clash.yaml",
          "output/configurations_singbox.json"
        ]
      }
    }
  ]
}
```

### DELETE /api/v1/pipeline/jobs/{job_id}

Cancel a running job or remove a completed job.

**Response:**
```json
{
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

## Export and Download

### GET /api/v1/export/{format}

Export configurations in various formats.

**Path Parameters:**
- `format` (string): Export format (json, yaml, csv, base64, clash, singbox, url)

**Query Parameters:**
- `protocol` (string): Filter by protocol
- `min_quality` (float): Minimum quality score
- `limit` (integer): Maximum number of configurations
- `download` (boolean): Force download as attachment

**Response:**
```json
{
  "format": "json",
  "count": 1547,
  "generated_at": "2025-01-14T10:45:00Z",
  "configurations": [
    // Configuration objects...
  ]
}
```

### GET /api/v1/export/subscription

Generate subscription URLs for various clients.

**Query Parameters:**
- `format` (string): Subscription format (clash, singbox, v2ray, quantumult)
- `protocol` (string): Filter by protocol
- `min_quality` (float): Minimum quality score
- `base64` (boolean): Return base64 encoded content

**Response:**
```text
# For base64=true
dHJvamFuOi8vcGFzc3dvcmRAZXhhbXBsZS5jb206NDQzP3NuaT1leGFtcGxlLmNvbSMlRTklQTYlOTk=

# For base64=false (raw URLs)
trojan://password@test-server.example:443?sni=test-server.example#%E9%A6%99
vmess://eyJ2IjoyLCJwcyI6InRlc3QiLCJhZGQiOiJleGFtcGxlLmNvbSJ9
```

## Testing and Validation

### POST /api/v1/test/configuration

Test a specific configuration for connectivity.

**Request Body:**
```json
{
  "configuration_url": "vmess://eyJ2IjoyLCJwcyI6InRlc3QiLCJhZGQiOiJleGFtcGxlLmNvbSJ9",
  "timeout": 10,
  "test_endpoints": ["https://www.google.com", "https://httpbin.org/ip"]
}
```

**Response:**
```json
{
  "test_id": "test_123456",
  "configuration_url": "vmess://...",
  "status": "completed",
  "results": {
    "connectivity": true,
    "response_time": 1250,
    "success_rate": 1.0,
    "endpoints_tested": 2,
    "endpoints_successful": 2,
    "ip_address": "203.0.113.1",
    "location": {
      "country": "US",
      "region": "California"
    }
  },
  "tested_at": "2025-01-14T10:50:00Z"
}
```

### POST /api/v1/test/source

Test a source URL for accessibility and configuration extraction.

**Request Body:**
```json
{
  "source_url": "https://test-server.example/configs",
  "timeout": 30,
  "validate_configs": true
}
```

**Response:**
```json
{
  "source_url": "https://test-server.example/configs",
  "status": "accessible",
  "response_time": 2.1,
  "configurations_found": 67,
  "configurations_valid": 65,
  "protocols": ["vmess", "vless", "trojan"],
  "test_results": {
    "http_status": 200,
    "content_length": 45678,
    "content_type": "text/plain",
    "ssl_valid": true,
    "parse_errors": 2
  },
  "tested_at": "2025-01-14T10:55:00Z"
}
```

## WebSocket Endpoints

### WS /api/v1/ws

Real-time updates for job progress, statistics, and system events.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8080/api/v1/ws');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

**Message Types:**

**Job Updates:**
```json
{
  "type": "job_update",
  "data": {
    "job_id": "job_f9853fe17423",
    "status": "running",
    "progress": 45,
    "message": "Processing source 12/24"
  }
}
```

**Statistics Updates:**
```json
{
  "type": "statistics_update",
  "data": {
    "total_configurations": 1547,
    "active_sources": 23,
    "success_rate": 0.85
  }
}
```

**Source Updates:**
```json
{
  "type": "source_update",
  "data": {
    "source_id": "src_123",
    "url": "https://test-server.example/configs",
    "status": "updated",
    "new_configs": 5
  }
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "validation_error",
  "message": "Invalid protocol specified",
  "details": {
    "field": "protocol",
    "value": "invalid_protocol",
    "allowed": ["vmess", "vless", "trojan", "shadowsocks"]
  },
  "timestamp": "2025-01-14T10:30:00Z",
  "path": "/api/v1/configurations",
  "request_id": "req_123456"
}
```

### HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created
- `202 Accepted` - Request accepted for processing
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable

### Error Types

- `validation_error` - Request validation failed
- `authentication_error` - Authentication failed
- `authorization_error` - Insufficient permissions
- `not_found_error` - Resource not found
- `rate_limit_error` - Rate limit exceeded
- `internal_error` - Internal server error
- `service_unavailable` - Service temporarily unavailable

## SDKs and Client Libraries

### Python SDK

```python
from streamline_vpn_sdk import StreamlineVPNClient

client = StreamlineVPNClient(
    base_url='http://localhost:8080',
    api_key='your-api-key'  # Optional
)

# Get statistics
stats = client.get_statistics()

# List configurations
configs = client.get_configurations(
    protocol='vmess',
    min_quality=0.7,
    limit=100
)

# Start pipeline
job = client.start_pipeline(
    output_formats=['json', 'clash'],
    filters={'min_quality': 0.6}
)

# Monitor job progress
for update in client.monitor_job(job['job_id']):
    print(f"Progress: {update['progress']}%")
```

### JavaScript/Node.js SDK

```javascript
const StreamlineVPN = require('streamline-vpn-sdk');

const client = new StreamlineVPN({
  baseUrl: 'http://localhost:8080',
  apiKey: 'your-api-key'  // Optional
});

// Get statistics
const stats = await client.getStatistics();

// List configurations
const configs = await client.getConfigurations({
  protocol: 'vmess',
  minQuality: 0.7,
  limit: 100
});

// Start pipeline
const job = await client.startPipeline({
  outputFormats: ['json', 'clash'],
  filters: { minQuality: 0.6 }
});
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Per-client limit**: 100 requests per minute
- **Burst allowance**: 20 additional requests
- **Rate limit headers**:
  - `X-RateLimit-Limit`: Total requests allowed per window
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Unix timestamp when window resets
  - `X-RateLimit-Retry-After`: Seconds to wait before retrying (when limited)

## Pagination

Large result sets use cursor-based pagination:

```json
{
  "total": 5000,
  "limit": 100,
  "offset": 200,
  "has_more": true,
  "next_offset": 300,
  "data": [...]
}
```

## Filtering and Sorting

Many endpoints support filtering and sorting:

**Query Parameters:**
- `sort` (string): Field to sort by
- `order` (string): Sort order (asc, desc)
- `filter[field]` (string): Filter by field value

**Example:**
```bash
curl "http://localhost:8080/api/v1/configurations?sort=quality_score&order=desc&filter[protocol]=vmess"
```

## Changelog

### v1.0.0 (2025-01-14)
- Initial API release
- Basic CRUD operations for configurations and sources
- Pipeline management
- Export functionality
- WebSocket support
- Rate limiting and authentication

