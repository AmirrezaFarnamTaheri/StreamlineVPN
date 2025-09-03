#!/bin/bash

# Xray-core Installation Script
# Version: 2.0.0
# Author: VPN Automation Team

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
XRAY_VERSION="1.8.4"
XRAY_DIR="/usr/local/bin"
XRAY_CONFIG_DIR="/etc/xray"
XRAY_LOG_DIR="/var/log/xray"
XRAY_SERVICE_FILE="/etc/systemd/system/xray.service"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

# Function to detect OS
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        print_error "Cannot detect OS"
        exit 1
    fi
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    case $OS in
        "Ubuntu"|"Debian GNU/Linux")
            apt-get update
            apt-get install -y curl wget unzip ca-certificates
            ;;
        "CentOS Linux"|"Red Hat Enterprise Linux")
            yum update -y
            yum install -y curl wget unzip ca-certificates
            ;;
        *)
            print_warning "Unsupported OS: $OS"
            print_status "Please install curl, wget, and unzip manually"
            ;;
    esac
}

# Function to download and install Xray
install_xray() {
    print_status "Downloading Xray-core v${XRAY_VERSION}..."
    
    # Detect architecture
    ARCH=$(uname -m)
    case $ARCH in
        x86_64)
            ARCH="64"
            ;;
        aarch64|arm64)
            ARCH="arm64-v8a"
            ;;
        armv7l)
            ARCH="arm32-v7a"
            ;;
        *)
            print_error "Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac
    
    # Download Xray
    XRAY_URL="https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/Xray-linux-${ARCH}.zip"
    TEMP_DIR=$(mktemp -d)
    
    if ! curl -L -o "${TEMP_DIR}/xray.zip" "$XRAY_URL"; then
        print_error "Failed to download Xray"
        exit 1
    fi
    
    # Extract and install
    print_status "Installing Xray..."
    unzip -q "${TEMP_DIR}/xray.zip" -d "${TEMP_DIR}"
    
    # Create directories
    mkdir -p "$XRAY_DIR" "$XRAY_CONFIG_DIR" "$XRAY_LOG_DIR"
    
    # Install binary
    cp "${TEMP_DIR}/xray" "$XRAY_DIR/"
    chmod +x "$XRAY_DIR/xray"
    
    # Clean up
    rm -rf "$TEMP_DIR"
    
    print_success "Xray installed successfully"
}

# Function to create configuration
create_config() {
    print_status "Creating configuration..."
    
    # Create config directory
    mkdir -p "$XRAY_CONFIG_DIR"
    
    # Copy configuration file
    if [[ -f "config.json" ]]; then
        cp config.json "$XRAY_CONFIG_DIR/"
        chmod 644 "$XRAY_CONFIG_DIR/config.json"
        print_success "Configuration copied"
    else
        print_warning "config.json not found, creating default configuration"
        create_default_config
    fi
}

# Function to create default configuration
create_default_config() {
    cat > "$XRAY_CONFIG_DIR/config.json" << 'EOF'
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
            "id": "00000000-0000-0000-0000-000000000000",
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
          "xver": 0,
          "serverNames": ["www.microsoft.com", "microsoft.com"],
          "privateKey": "YOUR_PRIVATE_KEY_HERE",
          "shortIds": ["YOUR_SHORT_ID_HERE"]
        }
      },
      "tag": "reality-inbound"
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom",
      "tag": "direct"
    },
    {
      "protocol": "blackhole",
      "tag": "blocked"
    }
  ],
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
      }
    ]
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
  },
  "stats": {},
  "api": {
    "tag": "api",
    "services": ["StatsService"]
  }
}
EOF
}

# Function to create systemd service
create_service() {
    print_status "Creating systemd service..."
    
    cat > "$XRAY_SERVICE_FILE" << EOF
[Unit]
Description=Xray Service
Documentation=https://github.com/xtls
After=network.target nss-lookup.target

[Service]
User=nobody
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
ExecStart=$XRAY_DIR/xray run -config $XRAY_CONFIG_DIR/config.json
Restart=on-failure
RestartPreventExitStatus=23
LimitNPROC=10000
LimitNOFILE=1000000

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    print_success "Systemd service created"
}

# Function to setup firewall
setup_firewall() {
    print_status "Setting up firewall..."
    
    # Check if ufw is available
    if command -v ufw >/dev/null 2>&1; then
        ufw allow 443/tcp
        ufw allow 8443/tcp
        ufw allow 2053/tcp
        print_success "UFW rules added"
    elif command -v firewall-cmd >/dev/null 2>&1; then
        firewall-cmd --permanent --add-port=443/tcp
        firewall-cmd --permanent --add-port=8443/tcp
        firewall-cmd --permanent --add-port=2053/tcp
        firewall-cmd --reload
        print_success "Firewalld rules added"
    else
        print_warning "No supported firewall found"
    fi
}

# Function to generate keys
generate_keys() {
    print_status "Generating REALITY keys..."
    
    # Generate private key
    PRIVATE_KEY=$(openssl rand -hex 32)
    
    # Generate public key (simplified - in production use proper key derivation)
    PUBLIC_KEY=$(echo "$PRIVATE_KEY" | openssl dgst -sha256 -binary | base64)
    
    # Generate short ID
    SHORT_ID=$(openssl rand -hex 8)
    
    # Save keys to file
    cat > "$XRAY_CONFIG_DIR/keys.txt" << EOF
# Xray REALITY Keys
# Generated on: $(date)
# 
# Private Key: $PRIVATE_KEY
# Public Key: $PUBLIC_KEY
# Short ID: $SHORT_ID
# 
# IMPORTANT: Keep these keys secure and private!
EOF
    
    chmod 600 "$XRAY_CONFIG_DIR/keys.txt"
    
    print_success "Keys generated and saved to $XRAY_CONFIG_DIR/keys.txt"
    print_warning "Please update your config.json with these keys"
}

# Function to start service
start_service() {
    print_status "Starting Xray service..."
    
    # Enable and start service
    systemctl enable xray
    systemctl start xray
    
    # Check status
    if systemctl is-active --quiet xray; then
        print_success "Xray service started successfully"
    else
        print_error "Failed to start Xray service"
        systemctl status xray
        exit 1
    fi
}

# Function to show status
show_status() {
    print_status "Xray installation completed!"
    echo
    echo "Service Status:"
    systemctl status xray --no-pager -l
    echo
    echo "Configuration: $XRAY_CONFIG_DIR/config.json"
    echo "Logs: $XRAY_LOG_DIR/"
    echo "Binary: $XRAY_DIR/xray"
    echo
    print_warning "Don't forget to:"
    echo "1. Update the configuration with your REALITY keys"
    echo "2. Configure your domain and certificates"
    echo "3. Test the connection"
}

# Main installation function
main() {
    print_status "Starting Xray-core installation..."
    
    check_root
    detect_os
    install_dependencies
    install_xray
    create_config
    create_service
    setup_firewall
    generate_keys
    start_service
    show_status
}

# Run main function
main "$@"
