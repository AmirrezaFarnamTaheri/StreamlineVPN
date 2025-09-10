---
layout: default
title: API Documentation
description: Complete REST API reference for StreamlineVPN
---

# API Documentation

## Overview

StreamlineVPN provides a comprehensive REST API for managing VPN configurations, sources, and processing pipelines.

- **Base URL**: `http://localhost:8080`
- **Format**: JSON
- **Authentication**: Optional (configure via environment)

## Core Endpoints

### Health & Status

#### GET /health
Check API server health status.

**Response**:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime": 3600,
  "timestamp": "2025-01-10T12:00:00Z"
}
```

#### GET /api/v1/statistics
Get processing statistics and metrics.

**Response**:
```json
{
  "total_sources": 523,
  "active_sources": 486,
  "total_configs": 15234,
  "success_rate": 0.93,
  "last_update": "2025-01-10T11:45:00Z",
  "processing_time_avg": 12.5,
  "cache_hit_rate": 0.78
}
```

### Pipeline Management

#### POST /api/v1/pipeline/run
Start a new processing pipeline.

**Request Body**:
```json
{
  "config_path": "config/sources.yaml",
  "output_dir": "output",
  "formats": ["json", "clash", "singbox"],
  "options": {
    "deduplicate": true,
    "validate": true,
    "cache": true
  }
}
```

**Response** (202 Accepted):
```json
{
  "status": "accepted",
  "job_id": "job_20250110_120000_abc123",
  "message": "Pipeline started",
  "estimated_time": 30
}
```

#### GET /api/v1/pipeline/status/{job_id}
Check pipeline job status.

**Response**:
```json
{
  "job_id": "job_20250110_120000_abc123",
  "status": "running",
  "progress": 0.65,
  "current_step": "Processing sources",
  "sources_processed": 312,
  "configs_found": 8456,
  "errors": [],
  "started_at": "2025-01-10T12:00:00Z"
}
```

### Configuration Management

#### GET /api/v1/configurations
List processed VPN configurations.

**Query Parameters**:
- `limit` (int): Maximum results (default: 100, max: 1000)
- `offset` (int): Pagination offset (default: 0)
- `protocol` (string): Filter by protocol (vmess, vless, trojan, ss)
- `quality_min` (float): Minimum quality score (0.0-1.0)
- `country` (string): Filter by country code

**Response**:
```json
{
  "total": 15234,
  "limit": 100,
  "offset": 0,
  "configurations": [
    {
      "id": "cfg_abc123",
      "protocol": "vless",
      "server": "example.com",
      "port": 443,
      "user_id": "uuid-here",
      "quality_score": 0.92,
      "location": {
        "country": "US",
        "city": "New York",
        "lat": 40.7128,
        "lon": -74.0060
      },
      "metadata": {
        "source": "tier_1_premium",
        "last_check": "2025-01-10T11:30:00Z",
        "response_time": 125
      }
    }
  ]
}
```

### Source Management

#### GET /api/v1/sources
List all configured sources.

**Response**:
```json
{
  "total": 523,
  "sources": [
    {
      "id": "src_001",
      "url": "https://example.com/configs.txt",
      "tier": "premium",
      "status": "active",
      "last_check": "2025-01-10T11:00:00Z",
      "success_rate": 0.98,
      "avg_configs": 150,
      "avg_response_time": 450
    }
  ]
}
```

#### POST /api/v1/sources
Add a new configuration source.

**Request Body**:
```json
{
  "url": "https://newsource.com/vpn.txt",
  "tier": "community",
  "weight": 0.7,
  "protocols": ["vmess", "vless"]
}
```

**Response** (201 Created):
```json
{
  "status": "success",
  "source_id": "src_524",
  "message": "Source added successfully"
}
```

## WebSocket API

### WS /ws
Real-time updates via WebSocket.

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

**Message Format**:
```json
{
  "type": "statistics",
  "data": {
    "active_sources": 486,
    "total_configs": 15234,
    "processing": false
  },
  "timestamp": "2025-01-10T12:00:00Z"
}
```

## Error Responses

All endpoints use consistent error formatting:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid configuration path",
    "details": {
      "field": "config_path",
      "value": "invalid/path.yaml"
    }
  },
  "timestamp": "2025-01-10T12:00:00Z"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## Rate Limiting

- Default: 100 requests per minute
- Configurable via `RATE_LIMIT_RPM` environment variable
- Headers included: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## Examples

### cURL Examples

```bash
# Get statistics
curl http://localhost:8080/api/v1/statistics

# Start pipeline
curl -X POST http://localhost:8080/api/v1/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"formats": ["json", "clash"]}'

# Get configurations with filters
curl "http://localhost:8080/api/v1/configurations?protocol=vless&quality_min=0.8&limit=50"

# Add new source
curl -X POST http://localhost:8080/api/v1/sources \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/vpn.txt", "tier": "community"}'
```

### Python Examples

```python
import requests

API_BASE = "http://localhost:8080"

# Get statistics
response = requests.get(f"{API_BASE}/api/v1/statistics")
stats = response.json()
print(f"Total configs: {stats['total_configs']}")

# Start pipeline
response = requests.post(
    f"{API_BASE}/api/v1/pipeline/run",
    json={"formats": ["json", "clash", "singbox"]}
)
job = response.json()
print(f"Job started: {job['job_id']}")

# Monitor job status
import time
while True:
    response = requests.get(f"{API_BASE}/api/v1/pipeline/status/{job['job_id']}")
    status = response.json()
    if status['status'] in ['completed', 'failed']:
        break
    print(f"Progress: {status['progress']*100:.1f}%")
    time.sleep(2)
```

## OpenAPI Specification

Interactive API documentation available at:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`
- OpenAPI JSON: `http://localhost:8080/openapi.json`