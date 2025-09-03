# 3X-UI Panel

Advanced Xray panel with web interface, multi-protocol support, and comprehensive management capabilities.

## 🚀 Features

- **Web-Based Management**: Intuitive web interface for Xray management
- **Multi-Protocol Support**: VLESS, VMESS, Shadowsocks, Trojan, Hysteria2
- **User Management**: Advanced user management with quotas and restrictions
- **Real-time Monitoring**: Live traffic monitoring and statistics
- **Subscription Management**: QR code generation and subscription links
- **Security Features**: Rate limiting, IP blocking, and security policies
- **Backup & Recovery**: Automated backup and restore functionality
- **SSL/TLS Support**: Automatic certificate management with Nginx
- **Systemd Integration**: Native systemd service management

## 📋 Prerequisites

- Linux server (Ubuntu 18.04+, CentOS 7+, Debian 9+)
- Root access
- Domain name (for SSL certificates)
- Node.js and npm
- Basic networking knowledge

## 🛠️ Quick Installation

### Automated Installation

```bash
# Download and run installation script
curl -fsSL https://raw.githubusercontent.com/your-repo/vpn_automation/main/3x-ui/install.sh | sudo bash
```

### Manual Installation

```bash
# Clone repository
git clone https://github.com/your-repo/vpn_automation.git
cd vpn_automation/3x-ui

# Make script executable
chmod +x install.sh

# Run installation
sudo ./install.sh
```

## ⚙️ Configuration

### Main Configuration

The installation creates a configuration file at `/usr/local/x-ui/config/config.json`:

```json
{
  "panel": {
    "type": "tcp",
    "host": "0.0.0.0",
    "port": 54321,
    "assetPath": "",
    "execPath": "",
    "debug": false
  },
  "web": {
    "type": "tcp",
    "host": "0.0.0.0",
    "port": 54321,
    "ssl": {
      "enabled": false,
      "serverName": "",
      "provider": "file",
      "certificateFile": "",
      "keyFile": ""
    }
  },
  "db": {
    "type": "sqlite",
    "path": "/usr/local/x-ui/config/x-ui.db"
  },
  "log": {
    "level": "info",
    "output": "/usr/local/x-ui/logs/x-ui.log"
  }
}
```

### Nginx Configuration

The installation creates an Nginx configuration for SSL/TLS termination:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL configuration
    ssl_certificate /usr/local/x-ui/ssl/certificate.crt;
    ssl_certificate_key /usr/local/x-ui/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Proxy to 3X-UI
    location / {
        proxy_pass http://127.0.0.1:54321;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
    
    # Logs
    access_log /var/log/nginx/x-ui-access.log;
    error_log /var/log/nginx/x-ui-error.log;
}
```

## 🚀 Management Commands

### Service Management

```bash
# Start service
x-ui-manager start

# Stop service
x-ui-manager stop

# Restart service
x-ui-manager restart

# Check status
x-ui-manager status

# View logs
x-ui-manager logs

# Update service
x-ui-manager update
```

### Backup & Recovery

```bash
# Create backup
x-ui-manager backup

# Restore from backup
x-ui-manager restore /path/to/backup.tar.gz

# Test configuration
x-ui-manager config
```

### Systemd Commands

```bash
# Start service
sudo systemctl start x-ui

# Stop service
sudo systemctl stop x-ui

# Restart service
sudo systemctl restart x-ui

# Check status
sudo systemctl status x-ui

# View logs
sudo journalctl -u x-ui -f

# Enable auto-start
sudo systemctl enable x-ui
```

## 📊 Web Interface

### Access Information

- **HTTP URL**: http://your-domain.com:54321
- **HTTPS URL**: https://your-domain.com
- **Default Username**: admin
- **Default Password**: admin

### Dashboard Features

1. **Overview**: System status, active users, and traffic statistics
2. **Inbounds**: Xray inbound configuration management
3. **Users**: User management with quotas and restrictions
4. **Subscriptions**: Generate QR codes and subscription links
5. **Settings**: System configuration and security settings
6. **Logs**: Real-time system logs and user activity

### Inbound Configuration

#### VLESS REALITY Setup

1. Navigate to Inbounds section
2. Click "Add Inbound"
3. Select "VLESS" protocol
4. Configure settings:
   - Port: 443
   - Network: tcp
   - Security: reality
   - Server Name: www.microsoft.com
   - Private Key: Your generated private key
   - Short ID: Your generated short ID

#### VMESS WS+TLS Setup

1. Navigate to Inbounds section
2. Click "Add Inbound"
3. Select "VMESS" protocol
4. Configure settings:
   - Port: 8443
   - Network: ws
   - Security: tls
   - Path: /vmess
   - Server Name: your-domain.com

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

# Update certificate paths
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /usr/local/x-ui/ssl/certificate.crt
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /usr/local/x-ui/ssl/private.key
sudo chown nobody:nobody /usr/local/x-ui/ssl/certificate.crt /usr/local/x-ui/ssl/private.key
```

#### Self-Signed Certificate (Testing)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /usr/local/x-ui/ssl/private.key \
    -out /usr/local/x-ui/ssl/certificate.crt \
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
echo "192.168.1.100" >> /usr/local/x-ui/blocked_ips.txt

# Block IP ranges
echo "10.0.0.0/8" >> /usr/local/x-ui/blocked_ranges.txt
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
# Check service status
sudo systemctl status x-ui

# Check logs
sudo journalctl -u x-ui -n 50

# Check configuration
x-ui-manager config

# Check permissions
sudo chown -R nobody:nobody /usr/local/x-ui/
sudo chmod 644 /usr/local/x-ui/config/config.json
```

#### 2. Web Interface Not Accessible

```bash
# Check if service is running
sudo systemctl status x-ui

# Check port availability
sudo netstat -tlnp | grep :54321
sudo ss -tlnp | grep :54321

# Check firewall
sudo ufw status
sudo firewall-cmd --list-all

# Check nginx
sudo systemctl status nginx
sudo nginx -t
```

#### 3. SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in /usr/local/x-ui/ssl/certificate.crt -text -noout

# Renew Let's Encrypt certificate
sudo certbot renew

# Update certificate paths
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /usr/local/x-ui/ssl/certificate.crt
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /usr/local/x-ui/ssl/private.key
sudo systemctl reload nginx
```

#### 4. Database Issues

```bash
# Check database file
ls -la /usr/local/x-ui/config/x-ui.db

# Backup database
sudo cp /usr/local/x-ui/config/x-ui.db /usr/local/x-ui/config/x-ui.db.backup

# Reset database (if needed)
sudo rm /usr/local/x-ui/config/x-ui.db
sudo systemctl restart x-ui
```

### Performance Optimization

#### System Tuning

```bash
# Optimize network settings
echo "net.core.rmem_max=16777216" >> /etc/sysctl.conf
echo "net.core.wmem_max=16777216" >> /etc/sysctl.conf
echo "net.ipv4.tcp_rmem=4096 87380 16777216" >> /etc/sysctl.conf
echo "net.ipv4.tcp_wmem=4096 65536 16777216" >> /etc/sysctl.conf
sudo sysctl -p

# Enable BBR congestion control
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sudo sysctl -p
```

#### Memory Optimization

```bash
# Adjust memory settings
echo "vm.swappiness=10" >> /etc/sysctl.conf
echo "vm.vfs_cache_pressure=50" >> /etc/sysctl.conf
sudo sysctl -p
```

## 🔄 Updates

### Update 3X-UI

```bash
# Update to latest version
x-ui-manager update

# Or manually
sudo systemctl stop x-ui
sudo curl -L -o /tmp/x-ui.tar.gz "https://github.com/alireza0/x-ui/releases/latest/download/x-ui-linux-amd64.tar.gz"
sudo tar -xzf /tmp/x-ui.tar.gz -C /usr/local/x-ui
sudo chmod +x /usr/local/x-ui/x-ui
sudo systemctl start x-ui
sudo rm /tmp/x-ui.tar.gz
```

### Backup Before Update

```bash
# Create backup
x-ui-manager backup

# Update
x-ui-manager update

# Verify installation
x-ui-manager status
```

## 📚 Advanced Configuration

### Custom Themes

```bash
# Create custom theme directory
mkdir -p /usr/local/x-ui/themes

# Add custom CSS
cat > /usr/local/x-ui/themes/custom.css << 'EOF'
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
mkdir -p /usr/local/x-ui/scripts

# Add custom scripts
cat > /usr/local/x-ui/scripts/custom.sh << 'EOF'
#!/bin/bash
# Custom maintenance script
echo "Running custom maintenance..."
# Add your custom logic here
EOF

chmod +x /usr/local/x-ui/scripts/custom.sh
```

### Integration with External Services

#### Prometheus Monitoring

```bash
# Install Prometheus
sudo apt-get install prometheus

# Create Prometheus configuration
cat > /etc/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'x-ui'
    static_configs:
      - targets: ['localhost:54321']
EOF

# Start Prometheus
sudo systemctl start prometheus
sudo systemctl enable prometheus
```

#### Grafana Dashboard

```bash
# Install Grafana
sudo apt-get install grafana

# Start Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# Access Grafana at http://your-domain.com:3000
# Default credentials: admin/admin
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

- **Documentation**: [3X-UI Documentation](https://github.com/alireza0/x-ui)
- **Issues**: [GitHub Issues](https://github.com/alireza0/x-ui/issues)
- **Discussions**: [GitHub Discussions](https://github.com/alireza0/x-ui/discussions)

---

**Built with ❤️ by the VPN Automation Team**
