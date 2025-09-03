# Sing-Box Multi-Protocol Proxy

Universal proxy platform supporting VLESS, VMESS, Shadowsocks, Trojan, Hysteria2, and more with advanced routing and filtering capabilities.

## 🚀 Features

- **Multi-Protocol Support**: VLESS, VMESS, Shadowsocks, Trojan, Hysteria2, WireGuard
- **REALITY Protocol**: Advanced TLS fingerprinting evasion
- **Advanced Routing**: Geo-blocking, protocol filtering, ad blocking
- **Clash API**: Compatible with Clash clients and dashboards
- **Geo Databases**: Automatic GeoIP and GeoSite database management
- **Statistics & Monitoring**: Real-time connection tracking
- **Security Hardening**: Automatic firewall configuration
- **Easy Installation**: One-click setup script

## 📋 Prerequisites

- Linux server (Ubuntu 18.04+, CentOS 7+, Debian 9+)
- Root access
- Domain name (for TLS certificates)
- Basic networking knowledge

## 🛠️ Quick Installation

### Automated Installation

```bash
# Download and run installation script
curl -fsSL https://raw.githubusercontent.com/your-repo/vpn_automation/main/sing-box/install.sh | sudo bash
```

### Manual Installation

```bash
# Clone repository
git clone https://github.com/your-repo/vpn_automation.git
cd vpn_automation/sing-box

# Make script executable
chmod +x install.sh

# Run installation
sudo ./install.sh
```

## ⚙️ Configuration

### Basic Configuration

The installation script creates a default configuration at `/etc/sing-box/config.json`:

```json
{
  "log": {
    "level": "info",
    "timestamp": true,
    "output": "/var/log/sing-box/sing-box.log"
  },
  "inbounds": [
    {
      "type": "vless",
      "tag": "vless-in",
      "listen": "::",
      "listen_port": 443,
      "users": [
        {
          "name": "default-user",
          "uuid": "your-uuid-here",
          "flow": "xtls-rprx-vision"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "www.microsoft.com",
        "reality": {
          "enabled": true,
          "handshake": {
            "server": "www.microsoft.com:443",
            "server_port": 443
          },
          "private_key": "your-private-key-here",
          "short_id": ["your-short-id-here"]
        }
      }
    }
  ],
  "outbounds": [
    {
      "type": "direct",
      "tag": "direct"
    },
    {
      "type": "block",
      "tag": "block"
    }
  ]
}
```

### Advanced Configuration

#### Multi-Protocol Setup

```json
{
  "inbounds": [
    {
      "type": "vless",
      "tag": "vless-in",
      "listen": "::",
      "listen_port": 443,
      "users": [
        {
          "name": "user1",
          "uuid": "uuid-1",
          "flow": "xtls-rprx-vision"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "www.microsoft.com",
        "reality": {
          "enabled": true,
          "handshake": {
            "server": "www.microsoft.com:443",
            "server_port": 443
          },
          "private_key": "private-key-1",
          "short_id": ["short-id-1"]
        }
      }
    },
    {
      "type": "shadowsocks",
      "tag": "ss-in",
      "listen": "::",
      "listen_port": 8388,
      "method": "2022-blake3-aes-256-gcm",
      "password": "your-password-here"
    },
    {
      "type": "trojan",
      "tag": "trojan-in",
      "listen": "::",
      "listen_port": 8443,
      "users": [
        {
          "name": "user1",
          "password": "your-password-here"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "your-domain.com",
        "certificate_path": "/etc/sing-box/cert.pem",
        "key_path": "/etc/sing-box/key.pem"
      }
    },
    {
      "type": "hysteria2",
      "tag": "hysteria2-in",
      "listen": "::",
      "listen_port": 8444,
      "users": [
        {
          "name": "user1",
          "password": "your-password-here"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "your-domain.com",
        "certificate_path": "/etc/sing-box/cert.pem",
        "key_path": "/etc/sing-box/key.pem"
      }
    }
  ]
}
```

#### Advanced Routing

```json
{
  "route": {
    "rules": [
      {
        "geoip": "private",
        "outbound": "block"
      },
      {
        "geosite": "category-ads-all",
        "outbound": "block"
      },
      {
        "geosite": "category-porn",
        "outbound": "block"
      },
      {
        "geosite": "category-gaming",
        "outbound": "direct"
      },
      {
        "protocol": "bittorrent",
        "outbound": "block"
      },
      {
        "domain": ["example.com", "example.org"],
        "outbound": "direct"
      },
      {
        "ip": ["1.1.1.1", "8.8.8.8"],
        "outbound": "direct"
      }
    ],
    "geoip": {
      "path": "/etc/sing-box/geoip/geoip.db",
      "download_url": "https://github.com/SagerNet/sing-geoip/releases/latest/download/geoip.db",
      "download_detour": "direct"
    },
    "geosite": {
      "path": "/etc/sing-box/geosite/geosite.db",
      "download_url": "https://github.com/SagerNet/sing-geosite/releases/latest/download/geosite.db",
      "download_detour": "direct"
    }
  }
}
```

#### Clash API Integration

```json
{
  "experimental": {
    "clash_api": {
      "external_controller": "127.0.0.1:9090",
      "external_ui": "ui",
      "secret": "your-secret-here",
      "default_mode": "rule",
      "store_selected": true,
      "cache_file": "/etc/sing-box/clash.db"
    }
  }
}
```

## 🔐 Security Configuration

### REALITY Protocol Setup

1. **Generate Keys**:
   ```bash
   # Private key
   openssl rand -hex 32
   
   # Public key (derived from private key)
   echo "private-key" | openssl dgst -sha256 -binary | base64
   
   # Short ID
   openssl rand -hex 8
   ```

2. **Update Configuration**:
   ```json
   "reality": {
     "enabled": true,
     "handshake": {
       "server": "www.microsoft.com:443",
       "server_port": 443
     },
     "private_key": "your-generated-private-key",
     "short_id": ["your-generated-short-id"]
   }
   ```

### TLS Certificate Setup

```bash
# Install certbot
sudo apt-get install certbot

# Obtain certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /etc/sing-box/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /etc/sing-box/key.pem
sudo chown nobody:nobody /etc/sing-box/cert.pem /etc/sing-box/key.pem
```

## 🚀 Management Commands

### Service Management

```bash
# Start service
sudo systemctl start sing-box

# Stop service
sudo systemctl stop sing-box

# Restart service
sudo systemctl restart sing-box

# Check status
sudo systemctl status sing-box

# Enable auto-start
sudo systemctl enable sing-box

# View logs
sudo journalctl -u sing-box -f
```

### Configuration Management

```bash
# Test configuration
sudo /usr/local/bin/sing-box check -c /etc/sing-box/config.json

# Reload configuration
sudo systemctl reload sing-box

# Backup configuration
sudo cp /etc/sing-box/config.json /etc/sing-box/config.json.backup

# Restore configuration
sudo cp /etc/sing-box/config.json.backup /etc/sing-box/config.json
```

### Management Script

The installation creates a management script at `/usr/local/bin/sing-box-manager`:

```bash
# Start service
sing-box-manager start

# Stop service
sing-box-manager stop

# Restart service
sing-box-manager restart

# Check status
sing-box-manager status

# View logs
sing-box-manager logs

# Test configuration
sing-box-manager config

# Reload configuration
sing-box-manager reload

# Backup configuration
sing-box-manager backup

# Restore configuration
sing-box-manager restore
```

## 📊 Monitoring & Statistics

### Clash API Integration

With Clash API enabled, you can use Clash clients and dashboards:

```bash
# Access Clash API
curl -H "Authorization: Bearer your-secret-here" http://127.0.0.1:9090/proxies

# Get traffic statistics
curl -H "Authorization: Bearer your-secret-here" http://127.0.0.1:9090/traffic

# Get connection information
curl -H "Authorization: Bearer your-secret-here" http://127.0.0.1:9090/connections
```

### Log Monitoring

```bash
# View real-time logs
sudo tail -f /var/log/sing-box/sing-box.log

# Search for specific events
sudo grep "error" /var/log/sing-box/sing-box.log

# Monitor connection attempts
sudo grep "accepted" /var/log/sing-box/sing-box.log
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check configuration syntax
sudo /usr/local/bin/sing-box check -c /etc/sing-box/config.json

# Check logs
sudo journalctl -u sing-box -n 50

# Check permissions
sudo chown -R nobody:nobody /etc/sing-box/
sudo chmod 644 /etc/sing-box/config.json
```

#### 2. Connection Issues

```bash
# Check firewall
sudo ufw status
sudo firewall-cmd --list-all

# Check port availability
sudo netstat -tlnp | grep :443
sudo ss -tlnp | grep :443

# Test connectivity
curl -I https://your-domain.com
```

#### 3. Certificate Issues

```bash
# Check certificate validity
openssl x509 -in /etc/sing-box/cert.pem -text -noout

# Renew certificate
sudo certbot renew

# Update certificate paths
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /etc/sing-box/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /etc/sing-box/key.pem
```

#### 4. Geo Database Issues

```bash
# Manually download geo databases
cd /etc/sing-box/geoip
curl -L -o geoip.db "https://github.com/SagerNet/sing-geoip/releases/latest/download/geoip.db"

cd /etc/sing-box/geosite
curl -L -o geosite.db "https://github.com/SagerNet/sing-geosite/releases/latest/download/geosite.db"

# Set permissions
sudo chown nobody:nobody /etc/sing-box/geoip/geoip.db
sudo chown nobody:nobody /etc/sing-box/geosite/geosite.db
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

## 📚 Advanced Features

### Load Balancing

```json
{
  "inbounds": [
    {
      "type": "vless",
      "tag": "vless-in",
      "listen": "::",
      "listen_port": 443,
      "users": [
        {
          "name": "user1",
          "uuid": "uuid-1",
          "flow": "xtls-rprx-vision",
          "level": 0
        },
        {
          "name": "user2",
          "uuid": "uuid-2",
          "flow": "xtls-rprx-vision",
          "level": 1
        }
      ]
    }
  ]
}
```

### Traffic Shaping

```json
{
  "policy": {
    "levels": {
      "0": {
        "handshake": 4,
        "connIdle": 300,
        "uplinkOnly": 2,
        "downlinkOnly": 5,
        "bufferSize": 10240
      },
      "1": {
        "handshake": 4,
        "connIdle": 300,
        "uplinkOnly": 2,
        "downlinkOnly": 5,
        "bufferSize": 20480
      }
    }
  }
}
```

### DNS Configuration

```json
{
  "dns": {
    "servers": [
      {
        "tag": "google",
        "address": "8.8.8.8",
        "detour": "direct"
      },
      {
        "tag": "cloudflare",
        "address": "1.1.1.1",
        "detour": "direct"
      }
    ],
    "rules": [
      {
        "domain": ["geosite:category-ads-all"],
        "server": "block"
      },
      {
        "domain": ["geosite:category-gaming"],
        "server": "direct"
      }
    ],
    "final": "google"
  }
}
```

## 🔄 Updates

### Update Sing-Box

```bash
# Stop service
sudo systemctl stop sing-box

# Backup configuration
sudo cp /etc/sing-box/config.json /etc/sing-box/config.json.backup

# Download new version
curl -L -o sing-box.tar.gz "https://github.com/SagerNet/sing-box/releases/download/v1.8.0/sing-box-1.8.0-linux-amd64.tar.gz"
tar -xzf sing-box.tar.gz

# Install new binary
sudo cp sing-box /usr/local/bin/
sudo chmod +x /usr/local/bin/sing-box

# Start service
sudo systemctl start sing-box

# Verify installation
sudo systemctl status sing-box
```

### Update Geo Databases

```bash
# Update GeoIP database
cd /etc/sing-box/geoip
curl -L -o geoip.db "https://github.com/SagerNet/sing-geoip/releases/latest/download/geoip.db"
sudo chown nobody:nobody geoip.db

# Update GeoSite database
cd /etc/sing-box/geosite
curl -L -o geosite.db "https://github.com/SagerNet/sing-geosite/releases/latest/download/geosite.db"
sudo chown nobody:nobody geosite.db

# Reload service
sudo systemctl reload sing-box
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

- **Documentation**: [Sing-Box Documentation](https://sing-box.sagernet.org/)
- **Issues**: [GitHub Issues](https://github.com/SagerNet/sing-box/issues)
- **Discussions**: [GitHub Discussions](https://github.com/SagerNet/sing-box/discussions)

---

**Built with ❤️ by the VPN Automation Team**
