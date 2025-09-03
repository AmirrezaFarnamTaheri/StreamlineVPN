# AdGuard Home - Advanced DNS Filtering & Privacy Protection

AdGuard Home is a network-wide software for blocking ads and tracking. It provides a powerful DNS server with advanced filtering capabilities, privacy protection, and comprehensive monitoring.

## 🚀 Features

- **DNS Filtering**: Block ads, trackers, and malicious domains
- **Privacy Protection**: DNS-over-HTTPS, DNS-over-TLS, DNS-over-QUIC
- **Custom Rules**: Whitelist/blacklist domains and IP addresses
- **Parental Control**: Safe search and content filtering
- **Statistics**: Detailed query logs and analytics
- **Multiple Upstreams**: Load balancing and failover
- **API Access**: RESTful API for automation
- **Monitoring**: Prometheus metrics and Grafana dashboards

## 📋 Prerequisites

- Docker and Docker Compose
- Linux/Unix system (Ubuntu 20.04+ recommended)
- Port 53 available (DNS)
- Port 443 available (HTTPS)
- Domain name (for SSL certificates)

## 🛠️ Installation

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd vpn_automation/adguard
   ```

2. **Configure AdGuard Home:**
   ```bash
   # Copy and edit the configuration
   cp AdGuardHome.yaml.example AdGuardHome.yaml
   nano AdGuardHome.yaml
   ```

3. **Start the services:**
   ```bash
   docker-compose up -d
   ```

4. **Access the web interface:**
   - URL: `http://localhost:3000`
   - Default credentials: `admin` / `password`

### Advanced Installation

1. **Create necessary directories:**
   ```bash
   mkdir -p {certs,backups,custom_filters,monitoring/{grafana/{provisioning,dashboards},prometheus}}
   ```

2. **Generate SSL certificates:**
   ```bash
   # Using Let's Encrypt
   certbot certonly --standalone -d dns.yourdomain.com
   
   # Copy certificates
   cp /etc/letsencrypt/live/dns.yourdomain.com/fullchain.pem certs/cert.pem
   cp /etc/letsencrypt/live/dns.yourdomain.com/privkey.pem certs/privkey.pem
   ```

3. **Configure monitoring:**
   ```bash
   # Create Prometheus configuration
   cat > monitoring/prometheus.yml << EOF
   global:
     scrape_interval: 15s
   
   scrape_configs:
     - job_name: 'adguard-home'
       static_configs:
         - targets: ['adguard-home:3000']
       metrics_path: /control/metrics
   EOF
   ```

4. **Start with monitoring:**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

## ⚙️ Configuration

### Basic Configuration

The main configuration file is `AdGuardHome.yaml`. Key sections:

```yaml
# HTTP interface
http:
  address: 0.0.0.0:3000
  users:
    - name: admin
      password: $2y$10$hashed_password_here

# DNS settings
dns:
  bind_hosts:
    - 0.0.0.0
  port: 53
  upstream_dns:
    - 1.1.1.1
    - 8.8.8.8
    - tls://cloudflare-dns.com
  filtering_enabled: true
  filters:
    - enabled: true
      url: https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt
      name: AdGuard DNS filter
```

### Advanced Configuration

#### Custom Filter Lists

Create custom filter files in `custom_filters/`:

```bash
# Example custom filter
cat > custom_filters/custom.txt << EOF
||ads.example.com^
||tracking.example.com^
||analytics.example.com^
EOF
```

#### Upstream DNS Configuration

Configure multiple upstream DNS servers for redundancy:

```yaml
upstream_dns:
  - 1.1.1.1
  - 8.8.8.8
  - tls://cloudflare-dns.com
  - https://dns.cloudflare.com/dns-query
  - tls://dns.google
  - https://dns.google/dns-query
```

#### Rate Limiting

Configure rate limiting to prevent abuse:

```yaml
ratelimit: 20
ratelimit_whitelist: []
```

## 🔧 Management Commands

### Service Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f adguard-home

# Update AdGuard Home
docker-compose pull adguard-home
docker-compose up -d adguard-home
```

### Configuration Management

```bash
# Reload configuration
curl -X POST http://localhost:3000/control/reload_config

# Check status
curl http://localhost:3000/control/status

# Get statistics
curl http://localhost:3000/control/stats
```

### Backup and Restore

```bash
# Create backup
docker-compose run --rm backup

# Restore from backup
tar -xzf backups/adguard-backup-YYYYMMDD-HHMMSS.tar.gz -C /path/to/restore
```

## 📊 Monitoring

### Prometheus Metrics

AdGuard Home exposes metrics at `/control/metrics`:

```bash
# View metrics
curl http://localhost:3000/control/metrics
```

Key metrics:
- `adguard_dns_queries_total`: Total DNS queries
- `adguard_dns_blocked_total`: Blocked queries
- `adguard_dns_cache_hits_total`: Cache hits
- `adguard_dns_upstream_errors_total`: Upstream errors

### Grafana Dashboards

Access Grafana at `http://localhost:3001`:
- Username: `admin`
- Password: `admin123`

Import the provided dashboard configuration from `monitoring/grafana/dashboards/`.

## 🔐 Security

### SSL/TLS Configuration

```yaml
tls:
  enabled: true
  server_name: dns.yourdomain.com
  force_https: true
  port_https: 443
  port_dns_over_tls: 853
  port_dns_over_quic: 784
  certificate_chain: /opt/adguardhome/certs/cert.pem
  private_key: /opt/adguardhome/certs/privkey.pem
```

### Access Control

```yaml
# Restrict access to specific IPs
allowed_clients:
  - 192.168.1.0/24
  - 10.0.0.0/8

# Block specific clients
disallowed_clients:
  - 192.168.1.100
```

### Authentication

```yaml
http:
  users:
    - name: admin
      password: $2y$10$hashed_password_here
  auth_attempts: 5
  block_auth_min: 15
```

## 🌐 Network Integration

### Router Configuration

Configure your router to use AdGuard Home as DNS:

1. **Access router admin panel**
2. **Navigate to DHCP/DNS settings**
3. **Set DNS server to AdGuard Home IP**
4. **Restart DHCP service**

### Client Configuration

#### Linux
```bash
# Edit resolv.conf
echo "nameserver 192.168.1.100" | sudo tee /etc/resolv.conf
```

#### Windows
1. **Network Settings** → **Change adapter options**
2. **Right-click network adapter** → **Properties**
3. **Internet Protocol Version 4** → **Properties**
4. **Use the following DNS server addresses**: `192.168.1.100`

#### macOS
1. **System Preferences** → **Network**
2. **Select network connection** → **Advanced**
3. **DNS tab** → **Add DNS server**: `192.168.1.100`

## 🔍 Troubleshooting

### Common Issues

#### Port 53 Already in Use
```bash
# Check what's using port 53
sudo netstat -tulpn | grep :53

# Stop systemd-resolved (Ubuntu)
sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved
```

#### SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in certs/cert.pem -text -noout

# Renew Let's Encrypt certificate
certbot renew
```

#### DNS Not Working
```bash
# Test DNS resolution
nslookup google.com 192.168.1.100

# Check AdGuard Home logs
docker-compose logs adguard-home

# Verify configuration
curl http://localhost:3000/control/status
```

### Log Analysis

```bash
# View real-time logs
docker-compose logs -f adguard-home

# Search for errors
docker-compose logs adguard-home | grep ERROR

# Check query logs
curl http://localhost:3000/control/querylog
```

## 📈 Performance Optimization

### Cache Configuration

```yaml
cache_size: 4194304  # 4MB cache
cache_ttl_min: 0
cache_ttl_max: 0
cache_optimistic: false
```

### Upstream Optimization

```yaml
# Use fastest DNS servers
fastest_addr: true
fastest_timeout: 1s

# Enable parallel queries
all_servers: true
```

### Resource Limits

```yaml
# Limit concurrent connections
max_goroutines: 300

# Set upstream timeout
upstream_timeout: 10s
```

## 🔄 Updates and Maintenance

### Regular Maintenance

```bash
# Weekly backup
0 2 * * 0 docker-compose run --rm backup

# Monthly certificate renewal
0 3 1 * * certbot renew && docker-compose restart adguard-home

# Quarterly updates
0 4 1 */3 * docker-compose pull && docker-compose up -d
```

### Monitoring Alerts

Set up alerts for:
- High query volume
- Upstream DNS failures
- Certificate expiration
- Disk space usage

## 📚 API Reference

### REST API Endpoints

```bash
# Get status
GET /control/status

# Reload configuration
POST /control/reload_config

# Get statistics
GET /control/stats

# Get query log
GET /control/querylog

# Add filter
POST /control/filtering/add_url
```

### Example API Usage

```bash
# Add custom filter
curl -X POST http://localhost:3000/control/filtering/add_url \
  -H "Content-Type: application/json" \
  -d '{"name": "Custom Filter", "url": "https://example.com/filter.txt"}'

# Get blocked domains
curl http://localhost:3000/control/querylog | jq '.data[] | select(.result.reason == "blocked")'
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: [AdGuard Home Wiki](https://github.com/AdguardTeam/AdGuardHome/wiki)
- **Issues**: [GitHub Issues](https://github.com/AdguardTeam/AdGuardHome/issues)
- **Community**: [AdGuard Forum](https://forum.adguard.com/)

## 🔗 Related Projects

- [AdGuard DNS](https://adguard-dns.io/)
- [AdGuard Browser Extension](https://adguard.com/en/adguard-browser-extension/overview.html)
- [AdGuard for Windows](https://adguard.com/en/adguard-windows/overview.html)
