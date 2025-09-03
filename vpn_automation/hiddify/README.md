# Hiddify Manager

Advanced VPN management platform with web interface, multi-protocol support, and comprehensive monitoring capabilities.

## 🚀 Features

- **Web-Based Management**: Intuitive web interface for VPN management
- **Multi-Protocol Support**: VLESS, VMESS, Shadowsocks, Trojan, Hysteria2
- **User Management**: Advanced user management with quotas and restrictions
- **Real-time Monitoring**: Live traffic monitoring and statistics
- **Subscription Management**: QR code generation and subscription links
- **Security Features**: Rate limiting, IP blocking, and security policies
- **Backup & Recovery**: Automated backup and restore functionality
- **Docker Deployment**: Containerized deployment with Docker Compose
- **SSL/TLS Support**: Automatic certificate management with Caddy

## 📋 Prerequisites

- Linux server (Ubuntu 18.04+, CentOS 7+, Debian 9+)
- Root access
- Domain name (for SSL certificates)
- Docker and Docker Compose
- Basic networking knowledge

## 🛠️ Quick Installation

### Automated Installation

```bash
# Download and run installation script
curl -fsSL https://raw.githubusercontent.com/your-repo/vpn_automation/main/hiddify/install.sh | sudo bash
```

### Manual Installation

```bash
# Clone repository
git clone https://github.com/your-repo/vpn_automation.git
cd vpn_automation/hiddify

# Make script executable
chmod +x install.sh

# Run installation
sudo ./install.sh
```

## ⚙️ Configuration

### Environment Variables

The installation creates a `.env` file with the following configuration:

```bash
# Hiddify Configuration
HIDDIFY_DOMAIN=your-domain.com
HIDDIFY_EMAIL=admin@your-domain.com
HIDDIFY_PORT=8443

# Database Configuration
POSTGRES_DB=hiddify
POSTGRES_USER=hiddify
POSTGRES_PASSWORD=hiddify_password

# Redis Configuration
REDIS_PASSWORD=redis_password

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Security
SECRET_KEY=your-generated-secret-key
```

### Docker Compose Configuration

The installation creates a `docker-compose.yml` file with the following services:

```yaml
version: '3.8'

services:
  hiddify:
    image: hiddify/hiddify:latest
    container_name: hiddify
    restart: unless-stopped
    ports:
      - "8443:8443"
    environment:
      - HIDDIFY_CONFIG_PATH=/opt/hiddify-config
      - HIDDIFY_DOMAIN=your-domain.com
      - HIDDIFY_EMAIL=admin@your-domain.com
      - HIDDIFY_ADMIN_USERNAME=admin
      - HIDDIFY_ADMIN_PASSWORD=admin123
      - HIDDIFY_DB_HOST=postgres
      - HIDDIFY_DB_PORT=5432
      - HIDDIFY_DB_NAME=hiddify
      - HIDDIFY_DB_USER=hiddify
      - HIDDIFY_DB_PASSWORD=hiddify_password
      - HIDDIFY_REDIS_HOST=redis
      - HIDDIFY_REDIS_PORT=6379
      - HIDDIFY_REDIS_PASSWORD=redis_password
    volumes:
      - /opt/hiddify-data/hiddify:/opt/hiddify-config
      - /opt/hiddify-data/logs:/var/log/hiddify
    depends_on:
      - postgres
      - redis
    networks:
      - hiddify-network

  postgres:
    image: postgres:15-alpine
    container_name: hiddify-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=hiddify
      - POSTGRES_USER=hiddify
      - POSTGRES_PASSWORD=hiddify_password
    volumes:
      - /opt/hiddify-data/postgres:/var/lib/postgresql/data
    networks:
      - hiddify-network

  redis:
    image: redis:7-alpine
    container_name: hiddify-redis
    restart: unless-stopped
    command: redis-server --requirepass redis_password
    volumes:
      - /opt/hiddify-data/redis:/data
    networks:
      - hiddify-network

  caddy:
    image: caddy:2-alpine
    container_name: hiddify-caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /opt/hiddify-data/caddy:/etc/caddy
      - /opt/hiddify-data/caddy/certs:/etc/caddy/certs
    depends_on:
      - hiddify
    networks:
      - hiddify-network

networks:
  hiddify-network:
    driver: bridge
```

### Caddy Configuration

The installation creates a Caddyfile for SSL/TLS termination:

```caddy
{
    email admin@your-domain.com
    admin off
}

your-domain.com {
    reverse_proxy hiddify:8443 {
        header_up Host {host}
        header_up X-Real-IP {remote}
        header_up X-Forwarded-For {remote}
        header_up X-Forwarded-Proto {scheme}
    }
    
    log {
        output file /var/log/caddy/access.log
        format json
    }
}

# HTTP to HTTPS redirect
:80 {
    redir https://your-domain.com{uri} permanent
}
```

## 🚀 Management Commands

### Service Management

```bash
# Start services
hiddify-manager start

# Stop services
hiddify-manager stop

# Restart services
hiddify-manager restart

# Check status
hiddify-manager status

# View logs
hiddify-manager logs

# Update services
hiddify-manager update
```

### Backup & Recovery

```bash
# Create backup
hiddify-manager backup

# Restore from backup
hiddify-manager restore /path/to/backup.tar.gz

# Clean installation
hiddify-manager clean
```

### Docker Commands

```bash
# View service status
cd /opt/hiddify
docker-compose ps

# View logs
docker-compose logs -f

# Update images
docker-compose pull

# Restart specific service
docker-compose restart hiddify
```

## 📊 Web Interface

### Access Information

- **URL**: https://your-domain.com
- **Admin Username**: admin
- **Admin Password**: admin123

### Dashboard Features

1. **Overview**: System status, active users, and traffic statistics
2. **Users**: User management with quotas, restrictions, and status
3. **Servers**: VPN server configuration and management
4. **Subscriptions**: Generate QR codes and subscription links
5. **Settings**: System configuration and security settings
6. **Logs**: Real-time system logs and user activity

### User Management

#### Creating Users

1. Navigate to the Users section
2. Click "Add User"
3. Fill in user details:
   - Username
   - Email
   - Password
   - Data limit
   - Expiration date
   - Protocol preferences

#### User Restrictions

- **Data Limits**: Set monthly data usage limits
- **Time Limits**: Set account expiration dates
- **Protocol Restrictions**: Limit which protocols users can use
- **IP Restrictions**: Restrict access to specific IP ranges

## 🔐 Security Configuration

### SSL/TLS Setup

#### Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt-get install certbot

# Obtain certificate
sudo certbot certonly --standalone -d your-domain.com

# Update Caddy configuration
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/hiddify-data/caddy/certs/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/hiddify-data/caddy/certs/
```

#### Self-Signed Certificate (Testing)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /opt/hiddify-data/caddy/certs/private.key \
    -out /opt/hiddify-data/caddy/certs/certificate.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"
```

### Security Policies

#### Rate Limiting

Configure rate limiting in the web interface:

1. Navigate to Settings > Security
2. Set rate limits for:
   - Login attempts
   - API requests
   - Connection attempts

#### IP Blocking

```bash
# Block specific IP addresses
echo "192.168.1.100" >> /opt/hiddify-data/blocked_ips.txt

# Block IP ranges
echo "10.0.0.0/8" >> /opt/hiddify-data/blocked_ranges.txt
```

## 📈 Monitoring & Analytics

### Traffic Monitoring

#### Real-time Statistics

- Active connections
- Bandwidth usage
- Protocol distribution
- User activity

#### Historical Data

- Daily/weekly/monthly usage reports
- User activity logs
- System performance metrics

### Alert System

Configure alerts for:

- High bandwidth usage
- Failed login attempts
- System errors
- User quota exceeded

## 🔧 Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check Docker status
sudo systemctl status docker

# Check container logs
docker-compose logs hiddify

# Check configuration
docker-compose config
```

#### 2. Database Issues

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Connect to database
docker exec -it hiddify-postgres psql -U hiddify -d hiddify

# Reset database (if needed)
docker-compose down -v
docker-compose up -d
```

#### 3. SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in /opt/hiddify-data/caddy/certs/certificate.crt -text -noout

# Renew Let's Encrypt certificate
sudo certbot renew

# Restart Caddy
docker-compose restart caddy
```

#### 4. Performance Issues

```bash
# Check resource usage
docker stats

# Check system resources
htop
df -h
free -h
```

### Log Analysis

#### Hiddify Logs

```bash
# View Hiddify logs
docker-compose logs -f hiddify

# Search for errors
docker-compose logs hiddify | grep ERROR

# Search for specific user
docker-compose logs hiddify | grep "username"
```

#### Caddy Logs

```bash
# View Caddy logs
docker-compose logs -f caddy

# Check access logs
tail -f /opt/hiddify-data/caddy/access.log
```

## 🔄 Updates

### Update Hiddify

```bash
# Update to latest version
hiddify-manager update

# Or manually
cd /opt/hiddify
docker-compose pull
docker-compose up -d
```

### Backup Before Update

```bash
# Create backup
hiddify-manager backup

# Update
hiddify-manager update

# Verify installation
hiddify-manager status
```

## 📚 Advanced Configuration

### Custom Themes

```bash
# Create custom theme directory
mkdir -p /opt/hiddify-data/themes

# Add custom CSS
cat > /opt/hiddify-data/themes/custom.css << 'EOF'
/* Custom styles */
.dashboard-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}
EOF
```

### Custom Scripts

```bash
# Create custom scripts directory
mkdir -p /opt/hiddify-data/scripts

# Add custom scripts
cat > /opt/hiddify-data/scripts/custom.sh << 'EOF'
#!/bin/bash
# Custom maintenance script
echo "Running custom maintenance..."
# Add your custom logic here
EOF

chmod +x /opt/hiddify-data/scripts/custom.sh
```

### Integration with External Services

#### Prometheus Monitoring

```yaml
# Add to docker-compose.yml
  prometheus:
    image: prom/prometheus:latest
    container_name: hiddify-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - hiddify-network
```

#### Grafana Dashboard

```yaml
# Add to docker-compose.yml
  grafana:
    image: grafana/grafana:latest
    container_name: hiddify-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - hiddify-network
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 🆘 Support

- **Documentation**: [Hiddify Documentation](https://github.com/hiddify/hiddify)
- **Issues**: [GitHub Issues](https://github.com/hiddify/hiddify/issues)
- **Discussions**: [GitHub Discussions](https://github.com/hiddify/hiddify/discussions)

---

**Built with ❤️ by the VPN Automation Team**
