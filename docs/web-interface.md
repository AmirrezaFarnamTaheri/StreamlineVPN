# Web Interface Documentation

The VPN Merger includes a web interface that combines VPN subscription merging, configuration generation, and analytics.

## Overview

The web interface consists of three main components:

1. **Main Dashboard** - Landing page with navigation to all services
2. **Configuration Generator** - Web-based VPN client configuration generator
3. **Analytics Dashboard** - Real-time metrics and performance monitoring

## Quick Start

### Starting the Web Server

```bash
# Start the Web interface (respects WEB_HOST, WEB_PORT)
python run_web.py

# Start the API server (respects API_HOST, API_PORT)
python run_api.py
```

### Accessing the Interface

Once started, the web interface will be available at:

- **Main Dashboard**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8080/docs`

### API and Template

The web interface exposes additional JSON APIs for orchestration and configuration:

- `GET /api/status` – basic runtime info
- `GET /api/health` – health summary for main, generator, analytics, static
- `GET /api/sources` – prioritized source URLs
- `GET /api/configs` – sample configs from a quick merge
- `GET /api/v1/statistics` - processing stats and health summary
- `POST /api/merge` – run merge; accepts `{ "max_concurrent": number }`
- `POST /api/export` – export results; accepts `{ "format": "all"|format, "output_dir": "output" }`
- `GET /api/config` – current configuration snapshot
- `POST /api/config` – update configuration sections (JSON)
- `POST /api/validate` – validate config; accepts `{ "config_path": "..." }` or `{ "config": { ... } }`

Template path for the landing page:

- `src/vpn_merger/web/static/enhanced_interface.html`

If this template is missing, a compact, built-in fallback UI is served by `StaticHandler`.

## Configuration Generator

The configuration generator is based on the ProxyForge project and provides a user-friendly interface for creating VPN client configurations.

### Supported Protocols

#### VLESS REALITY
- **Purpose**: Generate VLESS client links with REALITY protocol support
- **Features**: 
  - Real-time input validation
  - QR code generation for mobile clients
  - Support for custom short IDs
  - Integration with Xray server configurations

#### sing-box JSON
- **Purpose**: Create sing-box compatible configuration files
- **Features**:
  - JSON format output
  - VLESS REALITY support
  - Copy/download functionality
  - Syntax validation

#### WireGuard
- **Purpose**: Generate WireGuard client configurations
- **Features**:
  - QR code generation for mobile clients
  - Customizable network settings
  - Key generation utilities
  - Configuration file download

#### Shadowsocks
- **Purpose**: Create Shadowsocks client links
- **Features**:
  - Multiple encryption methods
  - Secure password generation
  - QR code support
  - Base64 encoded links

### API Endpoints

The configuration generator exposes REST API endpoints for programmatic access:

#### Configuration Generation

```bash
# Generate VLESS REALITY configuration
POST /api/v1/generate/vless
Content-Type: application/json

{
  "host": "example.com",
  "port": 443,
  "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "sni": "www.microsoft.com",
  "pbk": "base64url_public_key",
  "sid": "optional_short_id"
}

# Generate sing-box JSON configuration
POST /api/v1/generate/singbox
Content-Type: application/json

{
  "host": "example.com",
  "port": 443,
  "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "sni": "www.microsoft.com",
  "pbk": "base64url_public_key",
  "sid": "optional_short_id"
}

# Generate WireGuard configuration
POST /api/v1/generate/wireguard
Content-Type: application/json

{
  "endpoint": "vpn.example.com:51820",
  "server_public_key": "server_public_key_base64",
  "client_private_key": "client_private_key_base64",
  "address": "10.0.0.2/32",
  "dns": "1.1.1.1, 1.0.0.1",
  "allowed_ips": "0.0.0.0/0, ::/0",
  "keepalive": "25"
}

# Generate Shadowsocks configuration
POST /api/v1/generate/shadowsocks
Content-Type: application/json

{
  "host": "example.com",
  "port": 8388,
  "method": "chacha20-ietf-poly1305",
  "password": "secure_password"
}
```

#### Utility Functions

```bash
# Generate UUID
GET /api/v1/utils/uuid

# Generate short ID for REALITY
GET /api/v1/utils/shortid?length=8

# Generate secure password
GET /api/v1/utils/password?length=20

# Generate WireGuard key (example)
GET /api/v1/utils/wg-key
```

### Response Format

All API endpoints return JSON responses in the following format:

```json
{
  "success": true,
  "config": {
    "uri": "vless://...",
    "type": "vless",
    "protocol": "reality"
  }
}
```

Error responses:

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

## Analytics Dashboard

The analytics dashboard provides real-time monitoring and metrics for the VPN merger operations.

### Features

- **Real-time Metrics**: Live configuration counts and performance data
- **Protocol Distribution**: Visual breakdown of VPN protocols
- **Geographic Distribution**: Server location analysis
- **Performance Trends**: Historical performance data
- **Cache Performance**: Cache hit rates and efficiency metrics
- **Error Monitoring**: Error rates and failure analysis

### API Endpoints

```bash
# Get current metrics
GET /api/metrics

# Get chart data
GET /api/charts?chart_id=protocol_breakdown

# Get performance data
GET /api/performance
```

## Security Considerations

### Input Validation

All user inputs are validated on both client and server side:

- **Hostname/IP Validation**: Ensures valid server addresses
- **Port Range Validation**: Ports must be between 1-65535
- **UUID Format Validation**: Ensures proper UUID format
- **Public Key Validation**: Validates base64url format for keys
- **Short ID Validation**: Ensures hex format and proper length

### Security Best Practices

1. **Never expose private keys**: Only public keys should be shared
2. **Use secure passwords**: Generated passwords use cryptographically secure random generation
3. **Validate all inputs**: Server-side validation prevents injection attacks
4. **Rate limiting**: API endpoints include rate limiting to prevent abuse
5. **HTTPS in production**: Always use HTTPS in production environments

### Security Headers & CSP

The Web interface adds security headers by default:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (when applicable)
- `Content-Security-Policy` with a strict `connect-src`

API base and CSP are configurable:

- `API_BASE_URL`: Points the Web UI to your API server (defaults to `http://localhost:8080`).
- `WEB_CONNECT_SRC_EXTRA`: Optional extra connect-src origins for CSP (space or comma separated).

Examples:

```bash
# Point UI to a hosted API and allow WebSocket connections
API_BASE_URL=https://api.example.com \
WEB_CONNECT_SRC_EXTRA="https://api.example.com wss://ws.example.com" \
python run_web.py
```

The frontend also includes `docs/api-base.js` which sets `window.__API_BASE__` based on `API_BASE_URL` and current host.

## Deployment

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start development server
python -m vpn_merger --web
```

### Production

```bash
# Using Docker
docker-compose up -d

# Using systemd service
sudo systemctl start vpn-merger-web

# Using Kubernetes
kubectl apply -f k8s/deployment.yaml
```

### Environment Variables

```bash
# Web server configuration
WEB_HOST=0.0.0.0
WEB_PORT=8000
# API base for the Web UI
API_BASE_URL=http://localhost:8080
# Optional extra CSP connect-src origins (space/comma separated)
WEB_CONNECT_SRC_EXTRA="https://api.example.com wss://ws.example.com"

# Security
DASHBOARD_TOKEN=your_secure_token
VPN_MERGER_ENVIRONMENT=production
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8000, 8080, 8081, and 8082 are available
2. **Missing dependencies**: Install required packages with `pip install -r requirements.txt`
3. **Permission errors**: Ensure the application has write access to output directories
4. **Firewall issues**: Configure firewall to allow access to web ports

### Logs

Check application logs for detailed error information:

```bash
# View logs
tail -f vpn_merger.log

# Check system logs
journalctl -u vpn-merger-web -f
```

### Health Checks

```bash
# Check main server health
curl http://localhost:8000/health

# Check configuration generator
curl http://localhost:8080/health

# Check analytics dashboard
curl http://localhost:8081/health
```

## Contributing

To contribute to the web interface:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/CleanConfigs-SubMerger.git
cd CleanConfigs-SubMerger

# Install development dependencies
pip install -r requirements-enhanced.txt

# Start development server
python -m vpn_merger --web --verbose
```

## License

This project is licensed under the GPL-3.0-or-later License — see the [LICENSE](LICENSE) file for details.
 
