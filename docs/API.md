# API Overview

The VPN Subscription Merger provides a comprehensive REST API for accessing merged VPN configurations and system metrics.

## REST API (v1)

### Subscription Endpoints

- `GET /api/v1/sub/raw` - Raw subscription data
- `GET /api/v1/sub/base64` - Base64 encoded subscription
- `GET /api/v1/sub/singbox` - Sing-box format configuration
- `GET /api/v1/sub/clash` - Clash format configuration
- `GET /api/v1/sub/report` - Detailed JSON report with metadata

### Health & Status

- `GET /api/v1/health` - System health check
- `GET /api/v1/ready` - Readiness probe
- `GET /api/v1/status` - System status and statistics

### Configuration

- `GET /api/v1/config/sources` - List configured sources
- `GET /api/v1/config/status` - Configuration validation status

## REST API (v2)

### Enhanced Endpoints

- `GET /api/v2/nodes` - Paginated node listing with filtering
- `GET /api/v2/health` - Enhanced health information
- `GET /api/v2/metrics` - Detailed performance metrics

### Query Parameters

- `cursor`: Pagination cursor
- `limit`: Number of results (max 1000)
- `protocol`: Filter by protocol (vmess, vless, trojan, etc.)
- `reachable`: Filter by reachability status
- `host_re`: Host regex filter
- `risk`: Risk level filter
- `anonymize`: Anonymize sensitive data

## Metrics & Monitoring

### Prometheus Metrics

- Available on `--metrics-port` (default 8001)
- Endpoint: `/metrics`
- Includes custom metrics for:
  - Source processing statistics
  - Configuration quality metrics
  - Performance timing data
  - Error rates and success rates

### OpenTelemetry

- Distributed tracing support (optional)
- Span correlation across components
- Performance profiling capabilities

## Authentication

### API Token Authentication

```bash
curl -H "X-API-Token: your-token" https://api.example.com/api/v1/sub/raw
```

### Multi-tenant Support

```bash
curl -H "X-Tenant: tenant-id" https://api.example.com/api/v1/sub/raw
```

## Rate Limiting

- Default: 100 requests per minute per IP
- Configurable via environment variables
- Rate limit headers included in responses

## Error Handling

- Standard HTTP status codes
- JSON error responses with details
- Correlation IDs for debugging
- Structured error logging
