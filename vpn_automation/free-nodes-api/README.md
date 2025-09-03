# Free Nodes Aggregator API

A FastAPI-based service that aggregates, normalizes, and serves VPN proxy nodes from various sources with health checking and scoring capabilities.

## 🚀 Features

- **Multi-Protocol Support**: VLESS, VMESS, Trojan, Shadowsocks
- **Link Parsing**: Automatic parsing of proxy share links
- **Health Checking**: TCP latency measurement and node validation
- **Scoring System**: Intelligent node scoring based on protocol, port, and latency
- **De-duplication**: Automatic removal of duplicate nodes
- **Export Formats**: Sing-box JSON, subscription text, and raw links
- **Rate Limiting**: Built-in rate limiting for API protection
- **CORS Support**: Cross-origin resource sharing enabled
- **Docker Ready**: Containerized deployment with Docker Compose

## 📋 Prerequisites

- Python 3.8+
- Docker (optional, for containerized deployment)
- Basic networking knowledge

## 🛠️ Quick Installation

### Local Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/vpn_automation.git
cd vpn_automation/free-nodes-api

# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn free_nodes_api:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Installation

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t free-nodes-api .
docker run -p 8000:8000 free-nodes-api
```

## 📖 API Documentation

### Health Check

```bash
GET /health
```

Returns service status:
```json
{
  "ok": true,
  "service": "free-nodes-api"
}
```

### Ingest Nodes

```bash
POST /api/ingest
Content-Type: application/json

{
  "links": [
    "vless://uuid@host:port?security=reality&pbk=key&sid=id#name",
    "vmess://base64-encoded-config",
    "trojan://password@host:port#name",
    "ss://method:password@host:port#name"
  ]
}
```

Response:
```json
{
  "ingested": 4,
  "total": 150
}
```

### Add Sources

```bash
POST /api/sources
Content-Type: application/json

{
  "urls": [
    "https://example.com/nodes.txt",
    "https://another-site.com/proxies.txt"
  ]
}
```

Response:
```json
{
  "sources": 2
}
```

### Refresh Sources

```bash
POST /api/refresh?healthcheck=true
```

Fetches and processes all configured sources:
```json
{
  "fetched": 25,
  "total": 175
}
```

### Get Nodes

```bash
GET /api/nodes.json?limit=200&proto=vless&sort=score
```

Parameters:
- `limit`: Number of nodes to return (default: 200, max: 1000)
- `proto`: Filter by protocol (vless, vmess, trojan, ss)
- `sort`: Sort order (score, latency, random)

Response:
```json
[
  {
    "proto": "vless",
    "host": "example.com",
    "port": 443,
    "name": "Sample-REALITY",
    "link": "vless://uuid@example.com:443?security=reality#Sample-REALITY",
    "uuid": "11111111-2222-3333-4444-555555555555",
    "password": null,
    "params": {
      "security": "reality",
      "pbk": "PUBKEY",
      "sid": "abcdef",
      "sni": "www.microsoft.com",
      "type": "tcp"
    },
    "latency_ms": 45,
    "healthy": true,
    "score": 2.145,
    "last_checked": 1703123456.789
  }
]
```

### Export Subscription

```bash
GET /api/subscription.txt?limit=200&base64out=true
```

Returns subscription links in text format:
```json
{
  "base64": "dmxlc3M6Ly91dWlkQGV4YW1wbGUuY29tOjQ0MyNzYW1wbGUtcmVhbGl0eQ=="
}
```

### Export Sing-box Configuration

```bash
GET /api/export/singbox.json?limit=200
```

Returns Sing-box compatible configuration:
```json
{
  "log": {
    "level": "info"
  },
  "outbounds": [
    {
      "type": "vless",
      "tag": "sample-reality",
      "server": "example.com",
      "server_port": 443,
      "uuid": "11111111-2222-3333-4444-555555555555",
      "flow": "xtls-rprx-vision",
      "tls": {
        "enabled": true,
        "server_name": "www.microsoft.com",
        "reality": {
          "enabled": true,
          "public_key": "PUBKEY",
          "short_id": "abcdef"
        }
      },
      "transport": {
        "type": "tcp"
      }
    }
  ]
}
```

### Ping Nodes

```bash
POST /api/ping
Content-Type: application/json

{
  "links": [
    "vless://uuid@host:port#name",
    "vmess://base64-config"
  ]
}
```

Returns latency information for provided nodes:
```json
[
  {
    "proto": "vless",
    "host": "host",
    "port": 443,
    "name": "name",
    "link": "vless://uuid@host:443#name",
    "uuid": "uuid",
    "latency_ms": 67,
    "healthy": true,
    "score": 1.933
  }
]
```

## 🔧 Configuration

### Environment Variables

```bash
# Rate limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=120

# Health checking
HEALTHCHECK_CONCURRENCY=50
CONNECT_TIMEOUT=2.5

# Storage
STORE_CAP=5000
```

### Rate Limiting

The API implements rate limiting to prevent abuse:
- **Default**: 120 requests per minute per IP
- **Response**: 429 Too Many Requests when exceeded
- **Reset**: Automatically resets every minute

## 📊 Node Scoring

Nodes are scored based on multiple factors:

1. **Port Bonus**: Ports 443 and 8443 get +1.2 points
2. **TLS Bonus**: TLS-enabled protocols get +1.0 points
3. **Latency Bonus**: Lower latency gets higher scores (0-1.0 points)
4. **REALITY Bonus**: VLESS REALITY gets additional scoring

### Scoring Formula

```python
score = 0.0
if port in (443, 8443):
    score += 1.2
if tls_enabled:
    score += 1.0
if latency_ms is not None:
    score += max(0.0, 1.0 - min(1000, latency_ms) / 1000.0)
```

## 🔍 Health Checking

### TCP Latency Measurement

- **Concurrency**: 50 simultaneous connections
- **Timeout**: 2.5 seconds per connection
- **Metrics**: Connection time in milliseconds
- **Health Status**: True if connection successful

### Health Check Process

1. Attempt TCP connection to node host:port
2. Measure connection time
3. Mark as healthy if successful
4. Update latency and score
5. Store timestamp of last check

## 🚀 Deployment

### Production Deployment

```bash
# Using Docker Compose
docker-compose up -d

# Using systemd service
sudo cp free-nodes-api.service /etc/systemd/system/
sudo systemctl enable free-nodes-api
sudo systemctl start free-nodes-api
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/TLS Setup

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check logs
docker-compose logs free-nodes-api

# Check port availability
netstat -tlnp | grep :8000

# Check dependencies
pip list | grep fastapi
```

#### 2. Health Checks Failing

```bash
# Check network connectivity
curl -I http://localhost:8000/health

# Check firewall
sudo ufw status
sudo firewall-cmd --list-all

# Test specific node
curl -X POST http://localhost:8000/api/ping \
  -H "Content-Type: application/json" \
  -d '{"links": ["vless://test@example.com:443#test"]}'
```

#### 3. Rate Limiting Issues

```bash
# Check rate limit status
curl -I http://localhost:8000/api/nodes.json

# Response headers show remaining requests
# X-RateLimit-Remaining: 119
# X-RateLimit-Reset: 1703123456
```

### Performance Optimization

#### System Tuning

```bash
# Increase file descriptors
echo "fs.file-max = 65536" >> /etc/sysctl.conf
echo "net.core.somaxconn = 65536" >> /etc/sysctl.conf
sudo sysctl -p

# Optimize network settings
echo "net.core.rmem_max = 16777216" >> /etc/sysctl.conf
echo "net.core.wmem_max = 16777216" >> /etc/sysctl.conf
sudo sysctl -p
```

#### Docker Optimization

```yaml
# docker-compose.yml
services:
  free-nodes-api:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
```

## 📈 Monitoring

### Health Monitoring

```bash
# Health check endpoint
curl http://localhost:8000/health

# Docker health check
docker ps --format "table {{.Names}}\t{{.Status}}"

# System resource usage
docker stats free-nodes-api
```

### Log Monitoring

```bash
# View logs
docker-compose logs -f free-nodes-api

# Filter errors
docker-compose logs free-nodes-api | grep ERROR

# Monitor rate limiting
docker-compose logs free-nodes-api | grep "Too many requests"
```

### Metrics Collection

```bash
# Node count
curl -s http://localhost:8000/api/nodes.json | jq length

# Health status
curl -s http://localhost:8000/api/nodes.json | jq '[.[] | select(.healthy == true)] | length'

# Average latency
curl -s http://localhost:8000/api/nodes.json | jq '[.[] | select(.latency_ms != null)] | map(.latency_ms) | add / length'
```

## 🔄 Updates

### Updating the Service

```bash
# Pull latest changes
git pull origin main

# Rebuild Docker image
docker-compose build --no-cache

# Restart service
docker-compose up -d

# Verify update
curl http://localhost:8000/health
```

### Backup and Restore

```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Restore from backup
tar -xzf backup-20231201.tar.gz
docker-compose restart free-nodes-api
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [API Documentation](http://localhost:8000/docs)
- **Issues**: [GitHub Issues](https://github.com/your-repo/vpn_automation/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/vpn_automation/discussions)

---

**Built with ❤️ by the VPN Automation Team**
