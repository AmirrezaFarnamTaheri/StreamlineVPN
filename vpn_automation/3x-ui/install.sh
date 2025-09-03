#!/usr/bin/env bash

# 3X-UI Installation Script
# Advanced Xray panel with web interface

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
XUI_VERSION="latest"
XUI_DIR="/usr/local/x-ui"
XUI_CONFIG_DIR="/usr/local/x-ui/config"
XUI_LOG_DIR="/usr/local/x-ui/logs"
XUI_PORT="54321"
XUI_DOMAIN="your-domain.com"
XUI_EMAIL="admin@your-domain.com"

# Logging
LOG_FILE="/tmp/3x-ui-install.log"

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
            apt-get install -y curl wget git nodejs npm ca-certificates gnupg lsb-release
            ;;
        *CentOS*|*RedHat*|*Fedora*)
            yum update -y
            yum install -y curl wget git nodejs npm ca-certificates
            ;;
        *)
            warning "Unknown OS, attempting to install basic dependencies..."
            if command -v apt-get &> /dev/null; then
                apt-get update && apt-get install -y curl wget git nodejs npm ca-certificates
            elif command -v yum &> /dev/null; then
                yum install -y curl wget git nodejs npm ca-certificates
            fi
            ;;
    esac
    
    # Install Node.js if not available
    if ! command -v node &> /dev/null; then
        log "Installing Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
        apt-get install -y nodejs
    fi
    
    # Install PM2 for process management
    if ! command -v pm2 &> /dev/null; then
        log "Installing PM2..."
        npm install -g pm2
    fi
}

# Function to create directories
create_directories() {
    log "Creating directories..."
    
    mkdir -p "$XUI_DIR"
    mkdir -p "$XUI_CONFIG_DIR"
    mkdir -p "$XUI_LOG_DIR"
    mkdir -p "$XUI_DIR/ssl"
    mkdir -p "$XUI_DIR/cert"
    
    # Set permissions
    chown -R nobody:nobody "$XUI_DIR"
    chmod 755 "$XUI_DIR"
}

# Function to download 3X-UI
download_xui() {
    log "Downloading 3X-UI..."
    
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
    DOWNLOAD_URL="https://github.com/alireza0/x-ui/releases/latest/download/x-ui-linux-${ARCH}.tar.gz"
    
    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # Download and extract
    if curl -L -o x-ui.tar.gz "$DOWNLOAD_URL"; then
        tar -xzf x-ui.tar.gz
        sudo cp x-ui "$XUI_DIR/"
        sudo chmod +x "$XUI_DIR/x-ui"
        log "3X-UI downloaded and installed successfully"
    else
        error "Failed to download 3X-UI"
    fi
    
    # Cleanup
    cd /
    rm -rf "$TEMP_DIR"
}

# Function to create configuration
create_config() {
    log "Creating 3X-UI configuration..."
    
    # Check if config already exists
    if [[ -f "$XUI_CONFIG_DIR/config.json" ]]; then
        warning "Configuration file already exists. Creating backup..."
        sudo cp "$XUI_CONFIG_DIR/config.json" "$XUI_CONFIG_DIR/config.json.backup"
    fi
    
    # Create default configuration
    cat > /tmp/x-ui-config.json << EOF
{
  "panel": {
    "type": "tcp",
    "host": "0.0.0.0",
    "port": $XUI_PORT,
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
    "path": "$XUI_CONFIG_DIR/x-ui.db"
  },
  "log": {
    "level": "info",
    "output": "$XUI_LOG_DIR/x-ui.log"
  }
}
EOF
    
    sudo cp /tmp/x-ui-config.json "$XUI_CONFIG_DIR/config.json"
    sudo chown nobody:nobody "$XUI_CONFIG_DIR/config.json"
    sudo chmod 644 "$XUI_CONFIG_DIR/config.json"
    
    log "Configuration created at $XUI_CONFIG_DIR/config.json"
}

# Function to create systemd service
create_service() {
    log "Creating systemd service..."
    
    cat > /tmp/x-ui.service << EOF
[Unit]
Description=3X-UI Panel Service
Documentation=https://github.com/alireza0/x-ui
After=network.target nss-lookup.target

[Service]
Type=simple
User=nobody
Group=nobody
WorkingDirectory=$XUI_DIR
ExecStart=$XUI_DIR/x-ui
Restart=on-failure
RestartSec=10
LimitNOFILE=infinity

[Install]
WantedBy=multi-user.target
EOF
    
    sudo cp /tmp/x-ui.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable x-ui
    
    log "Systemd service created and enabled"
}

# Function to configure firewall
configure_firewall() {
    log "Configuring firewall..."
    
    # Detect firewall type
    if command -v ufw &> /dev/null; then
        # UFW (Ubuntu)
        sudo ufw allow $XUI_PORT/tcp
        sudo ufw allow 443/tcp
        sudo ufw allow 80/tcp
        log "UFW rules added"
    elif command -v firewall-cmd &> /dev/null; then
        # Firewalld (CentOS/RHEL)
        sudo firewall-cmd --permanent --add-port=$XUI_PORT/tcp
        sudo firewall-cmd --permanent --add-port=443/tcp
        sudo firewall-cmd --permanent --add-port=80/tcp
        sudo firewall-cmd --reload
        log "Firewalld rules added"
    else
        warning "No supported firewall detected. Please manually configure your firewall."
    fi
}

# Function to create management script
create_management_script() {
    log "Creating management script..."
    
    cat > /tmp/x-ui-manager.sh << 'EOF'
#!/bin/bash

# 3X-UI Management Script

XUI_DIR="/usr/local/x-ui"
XUI_CONFIG="/usr/local/x-ui/config/config.json"
XUI_SERVICE="x-ui"

case "$1" in
    start)
        echo "Starting 3X-UI..."
        sudo systemctl start $XUI_SERVICE
        ;;
    stop)
        echo "Stopping 3X-UI..."
        sudo systemctl stop $XUI_SERVICE
        ;;
    restart)
        echo "Restarting 3X-UI..."
        sudo systemctl restart $XUI_SERVICE
        ;;
    status)
        echo "3X-UI Status:"
        sudo systemctl status $XUI_SERVICE --no-pager
        ;;
    logs)
        echo "3X-UI Logs:"
        sudo journalctl -u $XUI_SERVICE -f
        ;;
    config)
        echo "Testing configuration..."
        sudo $XUI_DIR/x-ui -test -c $XUI_CONFIG
        ;;
    reload)
        echo "Reloading configuration..."
        sudo systemctl reload $XUI_SERVICE
        ;;
    backup)
        echo "Backing up 3X-UI data..."
        sudo tar -czf "/tmp/x-ui-backup-$(date +%Y%m%d_%H%M%S).tar.gz" -C $XUI_DIR .
        echo "Backup created: /tmp/x-ui-backup-$(date +%Y%m%d_%H%M%S).tar.gz"
        ;;
    restore)
        if [ -f "$2" ]; then
            echo "Restoring 3X-UI data from $2..."
            sudo systemctl stop $XUI_SERVICE
            sudo rm -rf $XUI_DIR/*
            sudo tar -xzf "$2" -C $XUI_DIR
            sudo systemctl start $XUI_SERVICE
        else
            echo "Usage: $0 restore <backup-file>"
        fi
        ;;
    update)
        echo "Updating 3X-UI..."
        sudo systemctl stop $XUI_SERVICE
        sudo curl -L -o /tmp/x-ui.tar.gz "https://github.com/alireza0/x-ui/releases/latest/download/x-ui-linux-amd64.tar.gz"
        sudo tar -xzf /tmp/x-ui.tar.gz -C $XUI_DIR
        sudo chmod +x $XUI_DIR/x-ui
        sudo systemctl start $XUI_SERVICE
        sudo rm /tmp/x-ui.tar.gz
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|config|reload|backup|restore <file>|update}"
        exit 1
        ;;
esac
EOF
    
    sudo cp /tmp/x-ui-manager.sh /usr/local/bin/x-ui-manager
    sudo chmod +x /usr/local/bin/x-ui-manager
    
    log "Management script created at /usr/local/bin/x-ui-manager"
}

# Function to create SSL certificates
setup_ssl() {
    log "Setting up SSL certificates..."
    
    # Create certificates directory
    mkdir -p "$XUI_DIR/ssl"
    
    # Generate self-signed certificate for testing
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$XUI_DIR/ssl/private.key" \
        -out "$XUI_DIR/ssl/certificate.crt" \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=$XUI_DOMAIN"
    
    # Set permissions
    sudo chown -R nobody:nobody "$XUI_DIR/ssl"
    sudo chmod 600 "$XUI_DIR/ssl/private.key"
    sudo chmod 644 "$XUI_DIR/ssl/certificate.crt"
    
    log "Self-signed certificate created for testing"
    info "For production, replace with Let's Encrypt certificates"
}

# Function to create nginx configuration
create_nginx_config() {
    log "Creating Nginx configuration..."
    
    # Install nginx if not available
    if ! command -v nginx &> /dev/null; then
        case $OS in
            *Ubuntu*|*Debian*)
                apt-get install -y nginx
                ;;
            *CentOS*|*RedHat*|*Fedora*)
                yum install -y nginx
                ;;
        esac
    fi
    
    # Create nginx configuration
    cat > /tmp/x-ui-nginx.conf << EOF
server {
    listen 80;
    server_name $XUI_DOMAIN;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $XUI_DOMAIN;
    
    # SSL configuration
    ssl_certificate $XUI_DIR/ssl/certificate.crt;
    ssl_certificate_key $XUI_DIR/ssl/private.key;
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
        proxy_pass http://127.0.0.1:$XUI_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
    
    # Logs
    access_log /var/log/nginx/x-ui-access.log;
    error_log /var/log/nginx/x-ui-error.log;
}
EOF
    
    sudo cp /tmp/x-ui-nginx.conf /etc/nginx/sites-available/x-ui
    sudo ln -sf /etc/nginx/sites-available/x-ui /etc/nginx/sites-enabled/
    
    # Test nginx configuration
    if sudo nginx -t; then
        sudo systemctl reload nginx
        log "Nginx configuration created and loaded"
    else
        error "Nginx configuration test failed"
    fi
}

# Function to create backup script
create_backup_script() {
    log "Creating backup script..."
    
    cat > /tmp/x-ui-backup.sh << 'EOF'
#!/bin/bash

# 3X-UI Backup Script

XUI_DIR="/usr/local/x-ui"
BACKUP_DIR="/opt/x-ui-backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Stop service
sudo systemctl stop x-ui

# Create backup
sudo tar -czf "$BACKUP_DIR/x-ui-backup-$DATE.tar.gz" -C "$XUI_DIR" .

# Start service
sudo systemctl start x-ui

# Clean old backups (keep last 7 days)
find "$BACKUP_DIR" -name "x-ui-backup-*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/x-ui-backup-$DATE.tar.gz"
EOF
    
    sudo cp /tmp/x-ui-backup.sh "$XUI_DIR/backup.sh"
    sudo chmod +x "$XUI_DIR/backup.sh"
    
    # Add to crontab for daily backups
    (crontab -l 2>/dev/null; echo "0 2 * * * $XUI_DIR/backup.sh") | crontab -
    
    log "Backup script created and scheduled"
}

# Function to start service
start_service() {
    log "Starting 3X-UI service..."
    
    if sudo systemctl start x-ui; then
        log "3X-UI service started successfully"
    else
        error "Failed to start 3X-UI service"
    fi
    
    # Wait for service to be ready
    log "Waiting for service to be ready..."
    sleep 10
    
    # Check service status
    if sudo systemctl is-active --quiet x-ui; then
        log "3X-UI is running"
        sudo systemctl status x-ui --no-pager
    else
        error "3X-UI failed to start"
    fi
}

# Function to display installation summary
display_summary() {
    log "Installation completed successfully!"
    echo
    echo "=========================================="
    echo "           3X-UI Installation             "
    echo "=========================================="
    echo
    echo "Installation Directory: $XUI_DIR"
    echo "Configuration Directory: $XUI_CONFIG_DIR"
    echo "Log Directory: $XUI_LOG_DIR"
    echo "Port: $XUI_PORT"
    echo "Domain: $XUI_DOMAIN"
    echo
    echo "Access Information:"
    echo "  Web Interface: http://$XUI_DOMAIN:$XUI_PORT"
    echo "  HTTPS Interface: https://$XUI_DOMAIN"
    echo "  Default Username: admin"
    echo "  Default Password: admin"
    echo
    echo "Management Commands:"
    echo "  Start:   x-ui-manager start"
    echo "  Stop:    x-ui-manager stop"
    echo "  Restart: x-ui-manager restart"
    echo "  Status:  x-ui-manager status"
    echo "  Logs:    x-ui-manager logs"
    echo "  Update:  x-ui-manager update"
    echo "  Backup:  x-ui-manager backup"
    echo
    echo "Service Commands:"
    echo "  Start:   sudo systemctl start x-ui"
    echo "  Stop:    sudo systemctl stop x-ui"
    echo "  Restart: sudo systemctl restart x-ui"
    echo "  Status:  sudo systemctl status x-ui"
    echo "  Logs:    sudo journalctl -u x-ui -f"
    echo
    echo "Next Steps:"
    echo "1. Access the web interface and change default credentials"
    echo "2. Configure SSL certificates for production"
    echo "3. Add your first Xray server configuration"
    echo "4. Configure user accounts and subscriptions"
    echo "5. Set up monitoring and alerts"
    echo
    echo "Configuration files:"
    echo "- Main config: $XUI_CONFIG_DIR/config.json"
    echo "- SSL certificates: $XUI_DIR/ssl/"
    echo "- Nginx config: /etc/nginx/sites-available/x-ui"
    echo
    echo "For more information, visit: https://github.com/alireza0/x-ui"
    echo
}

# Function to prompt for configuration
prompt_configuration() {
    echo
    echo "=========================================="
    echo "          3X-UI Configuration            "
    echo "=========================================="
    echo
    
    read -p "Enter your domain name (e.g., panel.yourdomain.com): " XUI_DOMAIN
    read -p "Enter your email address: " XUI_EMAIL
    read -p "Enter panel port [54321]: " XUI_PORT
    
    # Set defaults if empty
    XUI_PORT=${XUI_PORT:-54321}
    
    echo
    echo "Configuration Summary:"
    echo "  Domain: $XUI_DOMAIN"
    echo "  Email: $XUI_EMAIL"
    echo "  Port: $XUI_PORT"
    echo
    
    read -p "Continue with this configuration? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        error "Installation cancelled"
    fi
}

# Main installation function
main() {
    log "Starting 3X-UI installation..."
    
    # Check prerequisites
    check_root
    detect_os
    
    # Prompt for configuration
    prompt_configuration
    
    # Installation steps
    install_dependencies
    create_directories
    download_xui
    create_config
    create_service
    configure_firewall
    create_management_script
    setup_ssl
    create_nginx_config
    create_backup_script
    start_service
    
    # Display summary
    display_summary
    
    log "Installation log saved to: $LOG_FILE"
}

# Run main function
main "$@"
