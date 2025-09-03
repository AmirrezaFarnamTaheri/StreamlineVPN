# Xray-core with REALITY Protocol

Enhanced Xray-core implementation with REALITY protocol support, multi-protocol inbound, and advanced routing capabilities.

## 🚀 Features

- **REALITY Protocol**: Advanced TLS fingerprinting evasion
- **Multi-Protocol Support**: VLESS, VMESS, Trojan, Shadowsocks
- **Advanced Routing**: Geo-blocking, protocol filtering, ad blocking
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
curl -fsSL https://raw.githubusercontent.com/your-repo/vpn_automation/main/xray-core/install.sh | sudo bash
```

### Manual Installation

```bash
# Clone repository
git clone https://github.com/your-repo/vpn_automation.git
cd vpn_automation/xray-core

# Make script executable
chmod +x install.sh

# Run installation
sudo ./install.sh
```

## ⚙️ Configuration

### Basic Configuration

The installation script creates a default configuration at `/etc/xray/config.json`:

```json
{
  "log": {
    "loglevel": "warning",
    "access": "/var/log/xray/access.log",
    "error": "/var/log/xray/error.log"
  },
  "inbounds": [
    {
      "port": 443,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "your-uuid-here",
            "flow": "xtls-rprx-vision"
          }
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "show": false,
          "dest": "www.microsoft.com:443",
          "serverNames": ["www.microsoft.com", "microsoft.com"],
          "privateKey": "your-private-key-here",
          "shortIds": ["your-short-id-here"]
        }
      }
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
      "port": 443,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "uuid-1",
            "flow": "xtls-rprx-vision"
          }
        ]
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "show": false,
          "dest": "www.microsoft.com:443",
          "serverNames": ["www.microsoft.com"],
          "privateKey": "private-key-1",
          "shortIds": ["short-id-1"]
        }
      }
    },
    {
      "port": 8443,
      "protocol": "vmess",
      "settings": {
        "clients": [
          {
            "id": "uuid-2",
            "alterId": 0
          }
        ]
      },
      "streamSettings": {
        "network": "ws",
        "security": "tls",
        "wsSettings": {
          "path": "/vmess",
          "headers": {
            "Host": "your-domain.com"
          }
        },
        "tlsSettings": {
          "serverName": "your-domain.com",
          "certificates": [
            {
              "certificateFile": "/etc/xray/cert.pem",
              "keyFile": "/etc/xray/key.pem"
            }
          ]
        }
      }
    }
  ]
}
```

#### Advanced Routing

```json
{
  "routing": {
    "rules": [
      {
        "type": "field",
        "ip": ["geoip:private"],
        "outboundTag": "blocked"
      },
      {
        "type": "field",
        "protocol": ["bittorrent"],
        "outboundTag": "blocked"
      },
      {
        "type": "field",
        "domain": ["geosite:category-ads-all"],
        "outboundTag": "blocked"
      },
      {
        "type": "field",
        "domain": ["geosite:category-porn"],
        "outboundTag": "blocked"
      },
      {
        "type": "field",
        "domain": ["geosite:category-gaming"],
        "outboundTag": "direct"
      }
    ]
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
   "realitySettings": {
     "show": false,
     "dest": "www.microsoft.com:443",
     "serverNames": ["www.microsoft.com", "microsoft.com"],
     "privateKey": "your-generated-private-key",
     "shortIds": ["your-generated-short-id"]
   }
   ```

### TLS Certificate Setup

```bash
# Install certbot
sudo apt-get install certbot

# Obtain certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /etc/xray/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /etc/xray/key.pem
sudo chown nobody:nobody /etc/xray/cert.pem /etc/xray/key.pem
```

## 🚀 Management Commands

### Service Management

```bash
# Start service
sudo systemctl start xray

# Stop service
sudo systemctl stop xray

# Restart service
sudo systemctl restart xray

# Check status
sudo systemctl status xray

# Enable auto-start
sudo systemctl enable xray

# View logs
sudo journalctl -u xray -f
```

### Configuration Management

```bash
# Reload configuration
sudo systemctl reload xray

# Test configuration
sudo /usr/local/bin/xray test -config /etc/xray/config.json

# Backup configuration
sudo cp /etc/xray/config.json /etc/xray/config.json.backup

# Restore configuration
sudo cp /etc/xray/config.json.backup /etc/xray/config.json
```

## 📊 Monitoring & Statistics

### Enable Statistics

```json
{
  "stats": {},
  "api": {
    "tag": "api",
    "services": ["StatsService"]
  },
  "policy": {
    "levels": {
      "0": {
        "statsUserUplink": true,
        "statsUserDownlink": true
      }
    },
    "system": {
      "statsInboundUplink": true,
      "statsInboundDownlink": true
    }
  }
}
```

### View Statistics

```bash
# Check connection statistics
curl -H "Content-Type: application/json" -X POST -d '{"cmd":"getStats","tag":"api"}' http://127.0.0.1:10085/api/stats

# Get user statistics
curl -H "Content-Type: application/json" -X POST -d '{"cmd":"getStats","tag":"api","name":"user-uuid"}' http://127.0.0.1:10085/api/stats
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check configuration syntax
sudo /usr/local/bin/xray test -config /etc/xray/config.json

# Check logs
sudo journalctl -u xray -n 50

# Check permissions
sudo chown -R nobody:nobody /etc/xray/
sudo chmod 644 /etc/xray/config.json
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
openssl x509 -in /etc/xray/cert.pem -text -noout

# Renew certificate
sudo certbot renew

# Update certificate paths
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /etc/xray/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /etc/xray/key.pem
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
      "port": 443,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "uuid-1",
            "flow": "xtls-rprx-vision",
            "level": 0
          },
          {
            "id": "uuid-2",
            "flow": "xtls-rprx-vision",
            "level": 1
          }
        ]
      }
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
        "statsUserUplink": true,
        "statsUserDownlink": true,
        "handshake": 4,
        "connIdle": 300,
        "uplinkOnly": 2,
        "downlinkOnly": 5,
        "bufferSize": 10240
      },
      "1": {
        "statsUserUplink": true,
        "statsUserDownlink": true,
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

## 🔄 Updates

### Update Xray-core

```bash
# Stop service
sudo systemctl stop xray

# Backup configuration
sudo cp /etc/xray/config.json /etc/xray/config.json.backup

# Download new version
curl -L -o xray.zip "https://github.com/XTLS/Xray-core/releases/download/v1.8.4/Xray-linux-64.zip"
unzip -q xray.zip

# Install new binary
sudo cp xray /usr/local/bin/
sudo chmod +x /usr/local/bin/xray

# Start service
sudo systemctl start xray

# Verify installation
sudo systemctl status xray
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

- **Documentation**: [Xray-core Wiki](https://github.com/XTLS/Xray-core/wiki)
- **Issues**: [GitHub Issues](https://github.com/XTLS/Xray-core/issues)
- **Discussions**: [GitHub Discussions](https://github.com/XTLS/Xray-core/discussions)

---

**Built with ❤️ by the VPN Automation Team**
