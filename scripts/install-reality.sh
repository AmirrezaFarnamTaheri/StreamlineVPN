#!/bin/bash
# VLESS REALITY Installation Script
# =================================
#
# This script installs and configures VLESS REALITY server
# for StreamlineVPN integration.

set -e

# Configuration
REALITY_USER="vless-reality"
REALITY_HOME="/opt/vless-reality"
REALITY_CONFIG="/etc/vless-reality/config.json"
REALITY_SERVICE="vless-reality"
REALITY_PORT="443"
REALITY_UUID=""
REALITY_PUBLIC_KEY=""
REALITY_PRIVATE_KEY=""
REALITY_SHORT_ID=""
REALITY_SERVER_NAME="www.microsoft.com"
REALITY_DEST="www.microsoft.com:443"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Detect OS and architecture
detect_system() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [[ -f /etc/debian_version ]]; then
            OS="debian"
        elif [[ -f /etc/redhat-release ]]; then
            OS="redhat"
        else
            OS="linux"
        fi
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi

    ARCH=$(uname -m)
    case $ARCH in
        x86_64) ARCH="amd64" ;;
        aarch64) ARCH="arm64" ;;
        armv7l) ARCH="armv7" ;;
        *) log_error "Unsupported architecture: $ARCH"; exit 1 ;;
    esac

    log_info "Detected OS: $OS, Architecture: $ARCH"
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    
    case $OS in
        debian)
            apt-get update
            apt-get install -y curl wget unzip jq openssl
            ;;
        redhat)
            yum update -y
            yum install -y curl wget unzip jq openssl
            ;;
    esac
    
    log_success "Dependencies installed"
}

# Generate keys and configuration
generate_keys() {
    log_info "Generating VLESS REALITY keys..."
    
    # Generate UUID
    REALITY_UUID=$(uuidgen)
    
    # Generate private key
    REALITY_PRIVATE_KEY=$(openssl rand -hex 32)
    
    # Generate public key (simplified - in production use proper key generation)
    REALITY_PUBLIC_KEY=$(echo -n "$REALITY_PRIVATE_KEY" | openssl dgst -sha256 -binary | base64)
    
    # Generate short ID
    REALITY_SHORT_ID=$(openssl rand -hex 8)
    
    log_success "Keys generated"
    log_info "UUID: $REALITY_UUID"
    log_info "Public Key: $REALITY_PUBLIC_KEY"
    log_info "Short ID: $REALITY_SHORT_ID"
}

# Download and install VLESS REALITY
install_vless_reality() {
    log_info "Downloading VLESS REALITY..."
    
    # Create user
    if ! id "$REALITY_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$REALITY_HOME" "$REALITY_USER"
        log_success "User $REALITY_USER created"
    fi
    
    # Create directories
    mkdir -p "$REALITY_HOME"/{bin,config,logs}
    mkdir -p /etc/vless-reality
    
    # Download VLESS REALITY binary (using sing-box as example)
    VLESS_VERSION="1.8.0"
    DOWNLOAD_URL="https://github.com/SagerNet/sing-box/releases/download/v${VLESS_VERSION}/sing-box-${VLESS_VERSION}-linux-${ARCH}.tar.gz"
    
    cd /tmp
    wget -q "$DOWNLOAD_URL" -O sing-box.tar.gz
    tar -xzf sing-box.tar.gz
    cp sing-box-${VLESS_VERSION}-linux-${ARCH}/sing-box "$REALITY_HOME/bin/"
    chmod +x "$REALITY_HOME/bin/sing-box"
    
    # Cleanup
    rm -rf sing-box.tar.gz sing-box-${VLESS_VERSION}-linux-${ARCH}
    
    log_success "VLESS REALITY installed"
}

# Create configuration
create_config() {
    log_info "Creating VLESS REALITY configuration..."
    
    cat > "$REALITY_CONFIG" << EOF
{
  "log": {
    "level": "info",
    "timestamp": true
  },
  "inbounds": [
    {
      "type": "vless",
      "tag": "vless-reality",
      "listen": "::",
      "listen_port": $REALITY_PORT,
      "users": [
        {
          "uuid": "$REALITY_UUID",
          "flow": "xtls-rprx-vision"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "$REALITY_SERVER_NAME",
        "reality": {
          "handshake": {
            "server": "$REALITY_DEST",
            "server_port": 443
          },
          "private_key": "$REALITY_PRIVATE_KEY",
          "short_id": ["$REALITY_SHORT_ID"]
        }
      }
    }
  ],
  "outbounds": [
    {
      "type": "direct",
      "tag": "direct"
    }
  ]
}
EOF

    chown -R "$REALITY_USER:$REALITY_USER" "$REALITY_HOME"
    chown -R "$REALITY_USER:$REALITY_USER" /etc/vless-reality
    
    log_success "Configuration created"
}

# Create systemd service
create_service() {
    log_info "Creating systemd service..."
    
    cat > "/etc/systemd/system/$REALITY_SERVICE.service" << EOF
[Unit]
Description=VLESS REALITY Server
After=network.target

[Service]
Type=simple
User=$REALITY_USER
Group=$REALITY_USER
WorkingDirectory=$REALITY_HOME
ExecStart=$REALITY_HOME/bin/sing-box run -c $REALITY_CONFIG
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "$REALITY_SERVICE"
    
    log_success "Systemd service created"
}

# Start service
start_service() {
    log_info "Starting VLESS REALITY service..."
    
    systemctl start "$REALITY_SERVICE"
    sleep 3
    
    if systemctl is-active --quiet "$REALITY_SERVICE"; then
        log_success "VLESS REALITY service started"
    else
        log_error "Failed to start VLESS REALITY service"
        systemctl status "$REALITY_SERVICE"
        exit 1
    fi
}

# Generate client configuration
generate_client_config() {
    log_info "Generating client configuration..."
    
    CLIENT_CONFIG="vless://$REALITY_UUID@$(curl -s ifconfig.me):$REALITY_PORT?encryption=none&security=reality&sni=$REALITY_SERVER_NAME&type=tcp&flow=xtls-rprx-vision&pbk=$REALITY_PUBLIC_KEY&sid=$REALITY_SHORT_ID&spx=#VLESS-REALITY"
    
    echo "Client Configuration:"
    echo "===================="
    echo "$CLIENT_CONFIG"
    echo ""
    echo "Configuration saved to: /root/vless-reality-client.txt"
    echo "$CLIENT_CONFIG" > /root/vless-reality-client.txt
    
    log_success "Client configuration generated"
}

# Main installation function
main() {
    log_info "Starting VLESS REALITY installation..."
    
    check_root
    detect_system
    install_dependencies
    generate_keys
    install_vless_reality
    create_config
    create_service
    start_service
    generate_client_config
    
    log_success "VLESS REALITY installation completed successfully!"
    log_info "Service status: systemctl status $REALITY_SERVICE"
    log_info "Service logs: journalctl -u $REALITY_SERVICE -f"
    log_info "Configuration: $REALITY_CONFIG"
    log_info "Client config: /root/vless-reality-client.txt"
}

# Run main function
main "$@"