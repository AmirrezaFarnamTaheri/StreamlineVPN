#!/usr/bin/env bash

# Sing-Box Installation Script
# Enhanced VPN automation with multi-protocol support

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SING_BOX_VERSION="1.8.0"
SING_BOX_DIR="/usr/local/bin"
SING_BOX_CONFIG_DIR="/etc/sing-box"
SING_BOX_LOG_DIR="/var/log/sing-box"
SING_BOX_SERVICE="sing-box"
SING_BOX_USER="nobody"
SING_BOX_GROUP="nobody"

# Logging
LOG_FILE="/tmp/sing-box-install.log"

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}" | tee -a "$LOG_FILE"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
    fi
}

# Function to detect OS
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    elif [[ -f /etc/lsb-release ]]; then
        . /etc/lsb-release
        OS=$DISTRIB_ID
        VER=$DISTRIB_RELEASE
    elif [[ -f /etc/debian_version ]]; then
        OS=Debian
        VER=$(cat /etc/debian_version)
    elif [[ -f /etc/SuSe-release ]]; then
        OS=SuSE
    elif [[ -f /etc/redhat-release ]]; then
        OS=RedHat
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    
    log "Detected OS: $OS $VER"
}

# Function to install dependencies
install_dependencies() {
    log "Installing dependencies..."
    
    case $OS in
        *Ubuntu*|*Debian*)
            apt-get update
            apt-get install -y curl wget unzip ca-certificates gnupg lsb-release
            ;;
        *CentOS*|*RedHat*|*Fedora*)
            yum update -y
            yum install -y curl wget unzip ca-certificates
            ;;
        *)
            warning "Unknown OS, attempting to install basic dependencies..."
            if command -v apt-get &> /dev/null; then
                apt-get update && apt-get install -y curl wget unzip ca-certificates
            elif command -v yum &> /dev/null; then
                yum install -y curl wget unzip ca-certificates
            fi
            ;;
    esac
}

# Function to download Sing-Box
download_sing_box() {
    log "Downloading Sing-Box v$SING_BOX_VERSION..."
    
    # Detect architecture
    ARCH=$(uname -m)
    case $ARCH in
        x86_64)
            ARCH="amd64"
            ;;
        aarch64|arm64)
            ARCH="arm64"
            ;;
        armv7l)
            ARCH="armv7"
            ;;
        *)
            error "Unsupported architecture: $ARCH"
            ;;
    esac
    
    # Download URL
    DOWNLOAD_URL="https://github.com/SagerNet/sing-box/releases/download/v${SING_BOX_VERSION}/sing-box-${SING_BOX_VERSION}-linux-${ARCH}.tar.gz"
    
    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # Download and extract
    if curl -L -o sing-box.tar.gz "$DOWNLOAD_URL"; then
        tar -xzf sing-box.tar.gz
        sudo cp sing-box "$SING_BOX_DIR/"
        sudo chmod +x "$SING_BOX_DIR/sing-box"
        log "Sing-Box downloaded and installed successfully"
    else
        error "Failed to download Sing-Box"
    fi
    
    # Cleanup
    cd /
    rm -rf "$TEMP_DIR"
}

# Function to create directories
create_directories() {
    log "Creating directories..."
    
    sudo mkdir -p "$SING_BOX_CONFIG_DIR"
    sudo mkdir -p "$SING_BOX_LOG_DIR"
    sudo mkdir -p "$SING_BOX_CONFIG_DIR/geoip"
    sudo mkdir -p "$SING_BOX_CONFIG_DIR/geosite"
    
    # Set permissions
    sudo chown -R "$SING_BOX_USER:$SING_BOX_GROUP" "$SING_BOX_CONFIG_DIR"
    sudo chown -R "$SING_BOX_USER:$SING_BOX_GROUP" "$SING_BOX_LOG_DIR"
    sudo chmod 755 "$SING_BOX_CONFIG_DIR"
    sudo chmod 755 "$SING_BOX_LOG_DIR"
}

# Function to create configuration
create_config() {
    log "Creating Sing-Box configuration..."
    
    # Check if config already exists
    if [[ -f "$SING_BOX_CONFIG_DIR/config.json" ]]; then
        warning "Configuration file already exists. Creating backup..."
        sudo cp "$SING_BOX_CONFIG_DIR/config.json" "$SING_BOX_CONFIG_DIR/config.json.backup"
    fi
    
    # Create default configuration
    cat > /tmp/sing-box-config.json << 'EOF'
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
          "uuid": "00000000-0000-0000-0000-000000000000",
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
          "private_key": "YOUR_PRIVATE_KEY_HERE",
          "short_id": ["YOUR_SHORT_ID_HERE"]
        }
      }
    },
    {
      "type": "shadowsocks",
      "tag": "ss-in",
      "listen": "::",
      "listen_port": 8388,
      "method": "2022-blake3-aes-256-gcm",
      "password": "YOUR_PASSWORD_HERE"
    },
    {
      "type": "trojan",
      "tag": "trojan-in",
      "listen": "::",
      "listen_port": 8443,
      "users": [
        {
          "name": "default-user",
          "password": "YOUR_PASSWORD_HERE"
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
          "name": "default-user",
          "password": "YOUR_PASSWORD_HERE"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "your-domain.com",
        "certificate_path": "/etc/sing-box/cert.pem",
        "key_path": "/etc/sing-box/key.pem"
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
  ],
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
  },
  "experimental": {
    "clash_api": {
      "external_controller": "127.0.0.1:9090",
      "external_ui": "ui",
      "secret": "YOUR_SECRET_HERE",
      "default_mode": "rule"
    }
  }
}
EOF
    
    sudo cp /tmp/sing-box-config.json "$SING_BOX_CONFIG_DIR/config.json"
    sudo chown "$SING_BOX_USER:$SING_BOX_GROUP" "$SING_BOX_CONFIG_DIR/config.json"
    sudo chmod 644 "$SING_BOX_CONFIG_DIR/config.json"
    
    log "Configuration created at $SING_BOX_CONFIG_DIR/config.json"
    info "Please update the configuration with your actual values:"
    info "- UUID for VLESS"
    info "- Password for Shadowsocks/Trojan/Hysteria2"
    info "- Private key and short ID for REALITY"
    info "- Domain name and certificates for TLS"
    info "- Secret for Clash API"
}

# Function to create systemd service
create_service() {
    log "Creating systemd service..."
    
    cat > /tmp/sing-box.service << EOF
[Unit]
Description=Sing-Box Proxy Service
Documentation=https://sing-box.sagernet.org/
After=network.target nss-lookup.target

[Service]
Type=simple
User=$SING_BOX_USER
Group=$SING_BOX_GROUP
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
ExecStart=$SING_BOX_DIR/sing-box run -c $SING_BOX_CONFIG_DIR/config.json
Restart=on-failure
RestartSec=10
LimitNOFILE=infinity

[Install]
WantedBy=multi-user.target
EOF
    
    sudo cp /tmp/sing-box.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable "$SING_BOX_SERVICE"
    
    log "Systemd service created and enabled"
}

# Function to configure firewall
configure_firewall() {
    log "Configuring firewall..."
    
    # Detect firewall type
    if command -v ufw &> /dev/null; then
        # UFW (Ubuntu)
        sudo ufw allow 443/tcp
        sudo ufw allow 8388/tcp
        sudo ufw allow 8443/tcp
        sudo ufw allow 8444/tcp
        sudo ufw allow 9090/tcp
        log "UFW rules added"
    elif command -v firewall-cmd &> /dev/null; then
        # Firewalld (CentOS/RHEL)
        sudo firewall-cmd --permanent --add-port=443/tcp
        sudo firewall-cmd --permanent --add-port=8388/tcp
        sudo firewall-cmd --permanent --add-port=8443/tcp
        sudo firewall-cmd --permanent --add-port=8444/tcp
        sudo firewall-cmd --permanent --add-port=9090/tcp
        sudo firewall-cmd --reload
        log "Firewalld rules added"
    else
        warning "No supported firewall detected. Please manually configure your firewall."
    fi
}

# Function to generate REALITY keys
generate_reality_keys() {
    log "Generating REALITY keys..."
    
    # Generate private key
    PRIVATE_KEY=$(openssl rand -hex 32)
    
    # Generate public key
    PUBLIC_KEY=$(echo "$PRIVATE_KEY" | openssl dgst -sha256 -binary | base64)
    
    # Generate short ID
    SHORT_ID=$(openssl rand -hex 8)
    
    # Save keys to file
    cat > /tmp/reality-keys.txt << EOF
# REALITY Keys Generated on $(date)
# Keep these keys secure and private!

Private Key: $PRIVATE_KEY
Public Key: $PUBLIC_KEY
Short ID: $SHORT_ID

# Add these to your configuration:
# "private_key": "$PRIVATE_KEY"
# "short_ids": ["$SHORT_ID"]
EOF
    
    sudo cp /tmp/reality-keys.txt "$SING_BOX_CONFIG_DIR/"
    sudo chown "$SING_BOX_USER:$SING_BOX_GROUP" "$SING_BOX_CONFIG_DIR/reality-keys.txt"
    sudo chmod 600 "$SING_BOX_CONFIG_DIR/reality-keys.txt"
    
    log "REALITY keys generated and saved to $SING_BOX_CONFIG_DIR/reality-keys.txt"
    warning "Please keep the keys file secure and update your configuration!"
}

# Function to download geo databases
download_geo_databases() {
    log "Downloading geo databases..."
    
    cd "$SING_BOX_CONFIG_DIR/geoip"
    if curl -L -o geoip.db "https://github.com/SagerNet/sing-geoip/releases/latest/download/geoip.db"; then
        sudo chown "$SING_BOX_USER:$SING_BOX_GROUP" geoip.db
        log "GeoIP database downloaded"
    else
        warning "Failed to download GeoIP database"
    fi
    
    cd "$SING_BOX_CONFIG_DIR/geosite"
    if curl -L -o geosite.db "https://github.com/SagerNet/sing-geosite/releases/latest/download/geosite.db"; then
        sudo chown "$SING_BOX_USER:$SING_BOX_GROUP" geosite.db
        log "GeoSite database downloaded"
    else
        warning "Failed to download GeoSite database"
    fi
}

# Function to test configuration
test_configuration() {
    log "Testing Sing-Box configuration..."
    
    if sudo "$SING_BOX_DIR/sing-box" check -c "$SING_BOX_CONFIG_DIR/config.json"; then
        log "Configuration test passed"
    else
        error "Configuration test failed. Please check your configuration."
    fi
}

# Function to start service
start_service() {
    log "Starting Sing-Box service..."
    
    if sudo systemctl start "$SING_BOX_SERVICE"; then
        log "Sing-Box service started successfully"
    else
        error "Failed to start Sing-Box service"
    fi
    
    # Check status
    if sudo systemctl is-active --quiet "$SING_BOX_SERVICE"; then
        log "Sing-Box is running"
        sudo systemctl status "$SING_BOX_SERVICE" --no-pager
    else
        error "Sing-Box failed to start"
    fi
}

# Function to create management script
create_management_script() {
    log "Creating management script..."
    
    cat > /tmp/sing-box-manager.sh << 'EOF'
#!/bin/bash

# Sing-Box Management Script

SING_BOX_SERVICE="sing-box"
SING_BOX_CONFIG="/etc/sing-box/config.json"

case "$1" in
    start)
        echo "Starting Sing-Box..."
        sudo systemctl start $SING_BOX_SERVICE
        ;;
    stop)
        echo "Stopping Sing-Box..."
        sudo systemctl stop $SING_BOX_SERVICE
        ;;
    restart)
        echo "Restarting Sing-Box..."
        sudo systemctl restart $SING_BOX_SERVICE
        ;;
    status)
        echo "Sing-Box Status:"
        sudo systemctl status $SING_BOX_SERVICE --no-pager
        ;;
    logs)
        echo "Sing-Box Logs:"
        sudo journalctl -u $SING_BOX_SERVICE -f
        ;;
    config)
        echo "Testing configuration..."
        sudo /usr/local/bin/sing-box check -c $SING_BOX_CONFIG
        ;;
    reload)
        echo "Reloading configuration..."
        sudo systemctl reload $SING_BOX_SERVICE
        ;;
    backup)
        echo "Backing up configuration..."
        sudo cp $SING_BOX_CONFIG $SING_BOX_CONFIG.backup.$(date +%Y%m%d_%H%M%S)
        ;;
    restore)
        if [ -f "$SING_BOX_CONFIG.backup" ]; then
            echo "Restoring configuration..."
            sudo cp $SING_BOX_CONFIG.backup $SING_BOX_CONFIG
            sudo systemctl restart $SING_BOX_SERVICE
        else
            echo "No backup file found"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|config|reload|backup|restore}"
        exit 1
        ;;
esac
EOF
    
    sudo cp /tmp/sing-box-manager.sh /usr/local/bin/sing-box-manager
    sudo chmod +x /usr/local/bin/sing-box-manager
    
    log "Management script created at /usr/local/bin/sing-box-manager"
}

# Function to display installation summary
display_summary() {
    log "Installation completed successfully!"
    echo
    echo "=========================================="
    echo "           Sing-Box Installation          "
    echo "=========================================="
    echo
    echo "Service: $SING_BOX_SERVICE"
    echo "Configuration: $SING_BOX_CONFIG_DIR/config.json"
    echo "Logs: $SING_BOX_LOG_DIR/"
    echo "Binary: $SING_BOX_DIR/sing-box"
    echo
    echo "Management Commands:"
    echo "  Start:   sudo systemctl start $SING_BOX_SERVICE"
    echo "  Stop:    sudo systemctl stop $SING_BOX_SERVICE"
    echo "  Restart: sudo systemctl restart $SING_BOX_SERVICE"
    echo "  Status:  sudo systemctl status $SING_BOX_SERVICE"
    echo "  Logs:    sudo journalctl -u $SING_BOX_SERVICE -f"
    echo
    echo "Or use the management script:"
    echo "  /usr/local/bin/sing-box-manager {start|stop|restart|status|logs}"
    echo
    echo "Next Steps:"
    echo "1. Update configuration with your actual values"
    echo "2. Generate and configure TLS certificates"
    echo "3. Update REALITY keys in configuration"
    echo "4. Test your configuration"
    echo "5. Configure your clients"
    echo
    echo "Configuration files:"
    echo "- Main config: $SING_BOX_CONFIG_DIR/config.json"
    echo "- REALITY keys: $SING_BOX_CONFIG_DIR/reality-keys.txt"
    echo
    echo "For more information, visit: https://sing-box.sagernet.org/"
    echo
}

# Main installation function
main() {
    log "Starting Sing-Box installation..."
    
    # Check prerequisites
    check_root
    detect_os
    
    # Installation steps
    install_dependencies
    download_sing_box
    create_directories
    create_config
    create_service
    configure_firewall
    generate_reality_keys
    download_geo_databases
    test_configuration
    create_management_script
    start_service
    
    # Display summary
    display_summary
    
    log "Installation log saved to: $LOG_FILE"
}

# Run main function
main "$@"
