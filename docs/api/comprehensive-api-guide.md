# Comprehensive API Guide

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Error Handling](#error-handling)
5. [Configuration Generation APIs](#configuration-generation-apis)
6. [Utility APIs](#utility-apis)
7. [Free Nodes Aggregator APIs](#free-nodes-aggregator-apis)
8. [GraphQL API](#graphql-api)
9. [WebSocket API](#websocket-api)
10. [Examples](#examples)
11. [Error Codes Reference](#error-codes-reference)
12. [Best Practices](#best-practices)

## Overview

The VPN Subscription Merger API provides comprehensive endpoints for:
- VPN configuration generation (VLESS, WireGuard, Shadowsocks, sing-box)
- Utility functions (UUID generation, password generation, key generation)
- Free VPN nodes aggregation and management
- Real-time monitoring and analytics
- GraphQL queries for advanced data retrieval

### Base URLs
- **Development**: `http://localhost:8000`
- **Production**: `https://api.vpnmerger.com`

### API Version
Current version: `v1`

## Authentication

Most endpoints require no authentication. Some administrative endpoints may require API tokens.

### API Key Authentication
```http
X-API-Key: your-api-key-here
```

### Bearer Token Authentication
```http
Authorization: Bearer your-token-here
```

## Rate Limiting

API calls are rate-limited to prevent abuse:

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Configuration Generation | 100 requests | 1 minute |
| Utility Functions | 200 requests | 1 minute |
| Free Nodes Aggregator | 50 requests | 1 minute |
| Resource-intensive Operations | 10 requests | 1 minute |

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Error Handling

All errors follow a consistent format:

```json
{
  "error": "validation_error",
  "message": "Invalid request parameters",
  "details": {
    "field": "host",
    "reason": "Required field is missing"
  },
  "timestamp": "2023-12-01T14:30:22Z"
}
```

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error
- `503` - Service Unavailable

## Configuration Generation APIs

### Generate VLESS REALITY Configuration

**Endpoint**: `POST /api/v1/generate/vless`

**Description**: Generate a VLESS REALITY client configuration with QR code.

**Request Body**:
```json
{
  "host": "example.com",
  "port": 443,
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "server_name": "www.microsoft.com",
  "dest": "www.microsoft.com:443",
  "path": "/vless",
  "remark": "My VLESS Server"
}
```

**Response**:
```json
{
  "config": "vless://uuid@host:port?encryption=none&security=reality&sni=server_name&type=tcp&flow=xtls-rprx-vision&pbk=public_key&sid=short_id&spx=spider_x&fp=chrome&dest=dest&path=path#remark",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "config_type": "VLESS REALITY"
}
```

**Example cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/generate/vless" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "example.com",
    "port": 443,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "server_name": "www.microsoft.com",
    "dest": "www.microsoft.com:443",
    "path": "/vless",
    "remark": "My VLESS Server"
  }'
```

### Generate sing-box JSON Configuration

**Endpoint**: `POST /api/v1/generate/singbox`

**Description**: Generate a sing-box compatible JSON configuration.

**Request Body**:
```json
{
  "host": "example.com",
  "port": 443,
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "server_name": "www.microsoft.com",
  "dest": "www.microsoft.com:443",
  "path": "/vless",
  "remark": "My VLESS Server"
}
```

**Response**:
```json
{
  "config": {
    "outbounds": [
      {
        "type": "vless",
        "tag": "proxy",
        "server": "example.com",
        "server_port": 443,
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "flow": "xtls-rprx-vision",
        "tls": {
          "enabled": true,
          "server_name": "www.microsoft.com",
          "reality": {
            "enabled": true,
            "public_key": "public_key_here",
            "short_id": "short_id_here",
            "spider_x": "spider_x_here"
          }
        }
      }
    ]
  },
  "config_type": "sing-box JSON"
}
```

### Generate WireGuard Configuration

**Endpoint**: `POST /api/v1/generate/wireguard`

**Description**: Generate a WireGuard client configuration with QR code.

**Request Body**:
```json
{
  "server_public_key": "dG3C9wL0nO4qR8sU2xY5zA0bC3dE6fG9hI2jK5lM8nO1pQ4rS7tU0vW3xY6zA9",
  "server_endpoint": "example.com:51820",
  "client_private_key": "cF2B8vK9mN3pQ7rT1wX4yZ6aB9cD2eF5gH8iJ1kL4mN7oP0qR3sT6uV9wX2yZ5",
  "allowed_ips": "0.0.0.0/0, ::/0",
  "dns": "1.1.1.1, 1.0.0.1",
  "persistent_keepalive": 25,
  "interface_name": "wg0"
}
```

**Response**:
```json
{
  "config": "[Interface]\nPrivateKey = cF2B8vK9mN3pQ7rT1wX4yZ6aB9cD2eF5gH8iJ1kL4mN7oP0qR3sT6uV9wX2yZ5\nAddress = 10.0.0.2/32\nDNS = 1.1.1.1, 1.0.0.1\n\n[Peer]\nPublicKey = dG3C9wL0nO4qR8sU2xY5zA0bC3dE6fG9hI2jK5lM8nO1pQ4rS7tU0vW3xY6zA9\nEndpoint = example.com:51820\nAllowedIPs = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "config_type": "WireGuard"
}
```

### Generate Shadowsocks Configuration

**Endpoint**: `POST /api/v1/generate/shadowsocks`

**Description**: Generate a Shadowsocks client configuration with QR code.

**Request Body**:
```json
{
  "host": "example.com",
  "port": 8388,
  "password": "mypassword123",
  "method": "aes-256-gcm",
  "remark": "My Shadowsocks Server",
  "plugin": "v2ray-plugin",
  "plugin_opts": "server;tls;host=example.com"
}
```

**Response**:
```json
{
  "config": "ss://base64(method:password)@host:port#remark",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "config_type": "Shadowsocks"
}
```

## Utility APIs

### Generate UUID

**Endpoint**: `GET /api/v1/utils/uuid`

**Description**: Generate a random UUID.

**Response**:
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Generate Short ID

**Endpoint**: `GET /api/v1/utils/shortid`

**Description**: Generate a short random identifier.

**Parameters**:
- `length` (optional): Length of the short ID (4-32, default: 8)

**Example**:
```bash
curl "http://localhost:8000/api/v1/utils/shortid?length=12"
```

**Response**:
```json
{
  "shortid": "a1b2c3d4e5f6"
}
```

### Generate Secure Password

**Endpoint**: `GET /api/v1/utils/password`

**Description**: Generate a cryptographically secure password.

**Parameters**:
- `length` (optional): Length of the password (8-128, default: 16)
- `include_symbols` (optional): Include special symbols (default: true)

**Example**:
```bash
curl "http://localhost:8000/api/v1/utils/password?length=20&include_symbols=true"
```

**Response**:
```json
{
  "password": "Kx9#mP2$vL8@nQ4!rT7&wY1"
}
```

### Generate WireGuard Key

**Endpoint**: `GET /api/v1/utils/wg-key`

**Description**: Generate a WireGuard private key.

**Response**:
```json
{
  "private_key": "cF2B8vK9mN3pQ7rT1wX4yZ6aB9cD2eF5gH8iJ1kL4mN7oP0qR3sT6uV9wX2yZ5",
  "public_key": "dG3C9wL0nO4qR8sU2xY5zA0bC3dE6fG9hI2jK5lM8nO1pQ4rS7tU0vW3xY6zA9",
  "key_type": "WireGuard",
  "key_length": 44
}
```

## Free Nodes Aggregator APIs

### Get VPN Nodes

**Endpoint**: `GET /api/nodes.json`

**Description**: Retrieve available VPN nodes with filtering and sorting.

**Parameters**:
- `limit` (optional): Maximum number of nodes to return (1-1000, default: 100)
- `sort` (optional): Sort order (score, latency, country, protocol, default: score)
- `protocol` (optional): Filter by protocol (vless, vmess, trojan, shadowsocks)
- `country` (optional): Filter by country code (e.g., US, GB, DE)

**Example**:
```bash
curl "http://localhost:8000/api/nodes.json?limit=50&sort=latency&protocol=vless&country=US"
```

**Response**:
```json
{
  "nodes": [
    {
      "id": "node_123",
      "host": "example.com",
      "port": 443,
      "protocol": "vless",
      "country": "US",
      "score": 0.85,
      "latency": 45.2,
      "last_checked": "2023-12-01T14:30:22Z",
      "config": "vless://uuid@host:port?encryption=none&security=reality&sni=server_name&type=tcp&flow=xtls-rprx-vision&pbk=public_key&sid=short_id&spx=spider_x&fp=chrome&dest=dest&path=path#remark"
    }
  ],
  "total": 150,
  "filtered": 50
}
```

### Get Raw Subscription

**Endpoint**: `GET /api/subscription.txt`

**Description**: Get raw subscription text in standard format.

**Response**:
```
vless://uuid@host:port?encryption=none&security=tls&type=ws&path=/path#name
vmess://base64(config)#name
ss://base64(method:password)@host:port#name
```

### Export sing-box Configuration

**Endpoint**: `GET /api/export/singbox.json`

**Description**: Export nodes in sing-box JSON format.

**Response**:
```json
{
  "outbounds": [
    {
      "type": "vless",
      "tag": "proxy-1",
      "server": "example.com",
      "server_port": 443,
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "flow": "xtls-rprx-vision",
      "tls": {
        "enabled": true,
        "server_name": "www.microsoft.com",
        "reality": {
          "enabled": true,
          "public_key": "public_key_here",
          "short_id": "short_id_here",
          "spider_x": "spider_x_here"
        }
      }
    }
  ]
}
```

### Add Source URLs

**Endpoint**: `POST /api/sources`

**Description**: Add new source URLs to the aggregator.

**Request Body**:
```json
{
  "urls": [
    "https://example.com/free.txt",
    "https://another.com/nodes.txt"
  ]
}
```

**Response**:
```json
{
  "added": 2,
  "skipped": 0,
  "errors": []
}
```

### Trigger Manual Refresh

**Endpoint**: `POST /api/refresh`

**Description**: Manually trigger a refresh of all sources.

**Parameters**:
- `healthcheck` (optional): Perform health checks on nodes (default: false)

**Example**:
```bash
curl -X POST "http://localhost:8000/api/refresh?healthcheck=true"
```

**Response**:
```json
{
  "message": "Refresh triggered successfully",
  "job_id": "refresh_20231201_143022"
}
```

### Health Check Specific Nodes

**Endpoint**: `POST /api/ping`

**Description**: Perform health checks on specific nodes.

**Request Body**:
```json
{
  "node_ids": ["node_123", "node_456"]
}
```

**Response**:
```json
{
  "results": [
    {
      "node_id": "node_123",
      "latency": 45.2,
      "status": "success"
    },
    {
      "node_id": "node_456",
      "latency": null,
      "status": "timeout"
    }
  ]
}
```

## GraphQL API

**Endpoint**: `POST /graphql`

**Description**: GraphQL API for advanced queries.

**Example Query**:
```graphql
query {
  nodes(limit: 10, sort: SCORE) {
    id
    host
    port
    protocol
    country
    score
    latency
    config
  }
}
```

**Example Mutation**:
```graphql
mutation {
  addSources(urls: ["https://example.com/free.txt"]) {
    added
    skipped
    errors
  }
}
```

## WebSocket API

**Endpoint**: `WS /ws`

**Description**: Real-time updates and monitoring.

**Example**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// Subscribe to node updates
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'node_updates'
}));
```

## Examples

### Python Example

```python
import requests
import json

# Generate VLESS configuration
def generate_vless_config():
    url = "http://localhost:8000/api/v1/generate/vless"
    data = {
        "host": "example.com",
        "port": 443,
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "server_name": "www.microsoft.com",
        "dest": "www.microsoft.com:443",
        "path": "/vless",
        "remark": "My VLESS Server"
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        result = response.json()
        print(f"Config: {result['config']}")
        print(f"QR Code: {result['qr_code'][:50]}...")
    else:
        print(f"Error: {response.json()}")

# Get VPN nodes
def get_vpn_nodes():
    url = "http://localhost:8000/api/nodes.json"
    params = {
        "limit": 10,
        "sort": "latency",
        "protocol": "vless"
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        result = response.json()
        print(f"Found {len(result['nodes'])} nodes")
        for node in result['nodes']:
            print(f"- {node['host']}:{node['port']} ({node['country']}) - {node['latency']}ms")
    else:
        print(f"Error: {response.json()}")

if __name__ == "__main__":
    generate_vless_config()
    get_vpn_nodes()
```

### JavaScript Example

```javascript
// Generate VLESS configuration
async function generateVlessConfig() {
  const response = await fetch('http://localhost:8000/api/v1/generate/vless', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      host: 'example.com',
      port: 443,
      uuid: '550e8400-e29b-41d4-a716-446655440000',
      server_name: 'www.microsoft.com',
      dest: 'www.microsoft.com:443',
      path: '/vless',
      remark: 'My VLESS Server'
    })
  });
  
  if (response.ok) {
    const result = await response.json();
    console.log('Config:', result.config);
    console.log('QR Code:', result.qr_code.substring(0, 50) + '...');
  } else {
    const error = await response.json();
    console.error('Error:', error);
  }
}

// Get VPN nodes
async function getVpnNodes() {
  const response = await fetch('http://localhost:8000/api/nodes.json?limit=10&sort=latency&protocol=vless');
  
  if (response.ok) {
    const result = await response.json();
    console.log(`Found ${result.nodes.length} nodes`);
    result.nodes.forEach(node => {
      console.log(`- ${node.host}:${node.port} (${node.country}) - ${node.latency}ms`);
    });
  } else {
    const error = await response.json();
    console.error('Error:', error);
  }
}

// Call functions
generateVlessConfig();
getVpnNodes();
```

### cURL Examples

```bash
# Generate VLESS configuration
curl -X POST "http://localhost:8000/api/v1/generate/vless" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "example.com",
    "port": 443,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "server_name": "www.microsoft.com",
    "dest": "www.microsoft.com:443",
    "path": "/vless",
    "remark": "My VLESS Server"
  }'

# Generate WireGuard key
curl "http://localhost:8000/api/v1/utils/wg-key"

# Get VPN nodes
curl "http://localhost:8000/api/nodes.json?limit=10&sort=latency"

# Add source URLs
curl -X POST "http://localhost:8000/api/sources" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com/free.txt",
      "https://another.com/nodes.txt"
    ]
  }'

# Trigger manual refresh
curl -X POST "http://localhost:8000/api/refresh?healthcheck=true"
```

## Error Codes Reference

### Validation Errors (400)

| Error Code | Description | Example |
|------------|-------------|---------|
| `validation_error` | Invalid request parameters | Missing required field |
| `invalid_uuid` | Invalid UUID format | UUID must be valid format |
| `invalid_port` | Invalid port number | Port must be 1-65535 |
| `invalid_host` | Invalid hostname | Hostname format invalid |
| `invalid_protocol` | Invalid protocol | Protocol not supported |

### Authentication Errors (401)

| Error Code | Description | Example |
|------------|-------------|---------|
| `unauthorized` | Missing or invalid authentication | API key required |
| `invalid_token` | Invalid authentication token | Token expired or invalid |
| `insufficient_permissions` | Insufficient permissions | Admin access required |

### Rate Limiting Errors (429)

| Error Code | Description | Example |
|------------|-------------|---------|
| `rate_limit_exceeded` | Rate limit exceeded | Too many requests |
| `quota_exceeded` | Quota exceeded | Daily limit reached |

### Server Errors (500)

| Error Code | Description | Example |
|------------|-------------|---------|
| `internal_error` | Internal server error | Unexpected error occurred |
| `service_unavailable` | Service temporarily unavailable | Maintenance mode |
| `database_error` | Database connection error | Database unavailable |
| `external_service_error` | External service error | Third-party service down |

### Configuration Generation Errors

| Error Code | Description | Example |
|------------|-------------|---------|
| `config_generation_failed` | Configuration generation failed | Invalid parameters |
| `qr_code_generation_failed` | QR code generation failed | Image generation error |
| `key_generation_failed` | Key generation failed | Cryptographic error |

### Node Aggregation Errors

| Error Code | Description | Example |
|------------|-------------|---------|
| `source_fetch_failed` | Source fetch failed | Network error |
| `source_parse_failed` | Source parse failed | Invalid format |
| `node_validation_failed` | Node validation failed | Invalid configuration |
| `health_check_failed` | Health check failed | Node unreachable |

## Best Practices

### 1. Error Handling
- Always check HTTP status codes
- Handle rate limiting gracefully
- Implement retry logic for transient errors
- Log errors for debugging

### 2. Performance
- Use appropriate batch sizes
- Cache responses when possible
- Implement connection pooling
- Monitor rate limits

### 3. Security
- Validate all input parameters
- Use HTTPS in production
- Implement proper authentication
- Sanitize user inputs

### 4. Monitoring
- Monitor API response times
- Track error rates
- Set up alerts for failures
- Monitor rate limit usage

### 5. Development
- Use environment variables for configuration
- Implement proper logging
- Write comprehensive tests
- Follow RESTful conventions

### 6. Integration
- Use WebSocket for real-time updates
- Implement GraphQL for complex queries
- Cache frequently accessed data
- Use appropriate HTTP methods

### 7. Documentation
- Keep API documentation up to date
- Provide comprehensive examples
- Document all error codes
- Include troubleshooting guides

### 8. Testing
- Test all endpoints thoroughly
- Test error scenarios
- Test rate limiting
- Test authentication

### 9. Deployment
- Use proper environment configuration
- Implement health checks
- Set up monitoring
- Use proper logging

### 10. Maintenance
- Regular security updates
- Monitor performance metrics
- Update documentation
- Handle deprecations gracefully
