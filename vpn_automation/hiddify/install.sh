#!/usr/bin/env bash

# Hiddify Manager Installation Script
# Advanced VPN management platform with web interface

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HIDDIFY_VERSION="latest"
HIDDIFY_DIR="/opt/hiddify"
HIDDIFY_DATA_DIR="/opt/hiddify-data"
HIDDIFY_PORT="8443"
HIDDIFY_DOMAIN="your-domain.com"
HIDDIFY_EMAIL="admin@your-domain.com"

# Logging
LOG_FILE="/tmp/hiddify-install.log"

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
            apt-get install -y curl wget git docker.io docker-compose ca-certificates gnupg lsb-release
            ;;
        *CentOS*|*RedHat*|*Fedora*)
            yum update -y
            yum install -y curl wget git docker docker-compose ca-certificates
            ;;
        *)
            warning "Unknown OS, attempting to install basic dependencies..."
            if command -v apt-get &> /dev/null; then
                apt-get update && apt-get install -y curl wget git docker.io docker-compose ca-certificates
            elif command -v yum &> /dev/null; then
                yum install -y curl wget git docker docker-compose ca-certificates
            fi
            ;;
    esac
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    # Install Docker Compose if not available
    if ! command -v docker-compose &> /dev/null; then
        log "Installing Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
}

# Function to create directories
create_directories() {
    log "Creating directories..."
    
    mkdir -p "$HIDDIFY_DIR"
    mkdir -p "$HIDDIFY_DATA_DIR"
    mkdir -p "$HIDDIFY_DATA_DIR/postgres"
    mkdir -p "$HIDDIFY_DATA_DIR/redis"
    mkdir -p "$HIDDIFY_DATA_DIR/caddy"
    mkdir -p "$HIDDIFY_DATA_DIR/hiddify"
    mkdir -p "$HIDDIFY_DATA_DIR/logs"
    
    # Set permissions
    chown -R 1000:1000 "$HIDDIFY_DATA_DIR"
    chmod 755 "$HIDDIFY_DATA_DIR"
}

# Function to create Docker Compose configuration
create_docker_compose() {
    log "Creating Docker Compose configuration..."
    
    cat > "$HIDDIFY_DIR/docker-compose.yml" << EOF
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
      - HIDDIFY_DOMAIN=$HIDDIFY_DOMAIN
      - HIDDIFY_EMAIL=$HIDDIFY_EMAIL
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
      - $HIDDIFY_DATA_DIR/hiddify:/opt/hiddify-config
      - $HIDDIFY_DATA_DIR/logs:/var/log/hiddify
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
      - $HIDDIFY_DATA_DIR/postgres:/var/lib/postgresql/data
    networks:
      - hiddify-network

  redis:
    image: redis:7-alpine
    container_name: hiddify-redis
    restart: unless-stopped
    command: redis-server --requirepass redis_password
    volumes:
      - $HIDDIFY_DATA_DIR/redis:/data
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
      - $HIDDIFY_DATA_DIR/caddy:/etc/caddy
      - $HIDDIFY_DATA_DIR/caddy/certs:/etc/caddy/certs
    depends_on:
      - hiddify
    networks:
      - hiddify-network

networks:
  hiddify-network:
    driver: bridge
EOF
    
    log "Docker Compose configuration created"
}

# Function to create Caddy configuration
create_caddy_config() {
    log "Creating Caddy configuration..."
    
    cat > "$HIDDIFY_DATA_DIR/caddy/Caddyfile" << EOF
{
    email $HIDDIFY_EMAIL
    admin off
}

$HIDDIFY_DOMAIN {
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
    redir https://$HIDDIFY_DOMAIN{uri} permanent
}
EOF
    
    log "Caddy configuration created"
}

# Function to create environment file
create_env_file() {
    log "Creating environment configuration..."
    
    cat > "$HIDDIFY_DIR/.env" << EOF
# Hiddify Configuration
HIDDIFY_DOMAIN=$HIDDIFY_DOMAIN
HIDDIFY_EMAIL=$HIDDIFY_EMAIL
HIDDIFY_PORT=$HIDDIFY_PORT

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
SECRET_KEY=$(openssl rand -hex 32)
EOF
    
    log "Environment configuration created"
}

# Function to create management script
create_management_script() {
    log "Creating management script..."
    
    cat > "$HIDDIFY_DIR/hiddify-manager.sh" << 'EOF'
#!/bin/bash

# Hiddify Manager Script

HIDDIFY_DIR="/opt/hiddify"
HIDDIFY_DATA_DIR="/opt/hiddify-data"

case "$1" in
    start)
        echo "Starting Hiddify..."
        cd "$HIDDIFY_DIR"
        docker-compose up -d
        ;;
    stop)
        echo "Stopping Hiddify..."
        cd "$HIDDIFY_DIR"
        docker-compose down
        ;;
    restart)
        echo "Restarting Hiddify..."
        cd "$HIDDIFY_DIR"
        docker-compose restart
        ;;
    status)
        echo "Hiddify Status:"
        cd "$HIDDIFY_DIR"
        docker-compose ps
        ;;
    logs)
        echo "Hiddify Logs:"
        cd "$HIDDIFY_DIR"
        docker-compose logs -f
        ;;
    update)
        echo "Updating Hiddify..."
        cd "$HIDDIFY_DIR"
        docker-compose pull
        docker-compose up -d
        ;;
    backup)
        echo "Backing up Hiddify data..."
        tar -czf "/tmp/hiddify-backup-$(date +%Y%m%d_%H%M%S).tar.gz" -C "$HIDDIFY_DATA_DIR" .
        echo "Backup created: /tmp/hiddify-backup-$(date +%Y%m%d_%H%M%S).tar.gz"
        ;;
    restore)
        if [ -f "$2" ]; then
            echo "Restoring Hiddify data from $2..."
            cd "$HIDDIFY_DIR"
            docker-compose down
            rm -rf "$HIDDIFY_DATA_DIR"/*
            tar -xzf "$2" -C "$HIDDIFY_DATA_DIR"
            docker-compose up -d
        else
            echo "Usage: $0 restore <backup-file>"
        fi
        ;;
    clean)
        echo "Cleaning Hiddify..."
        cd "$HIDDIFY_DIR"
        docker-compose down -v
        docker system prune -f
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|update|backup|restore <file>|clean}"
        exit 1
        ;;
esac
EOF
    
    chmod +x "$HIDDIFY_DIR/hiddify-manager.sh"
    
    # Create symlink for easy access
    ln -sf "$HIDDIFY_DIR/hiddify-manager.sh" /usr/local/bin/hiddify-manager
    
    log "Management script created"
}

# Function to configure firewall
configure_firewall() {
    log "Configuring firewall..."
    
    # Detect firewall type
    if command -v ufw &> /dev/null; then
        # UFW (Ubuntu)
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 8443/tcp
        log "UFW rules added"
    elif command -v firewall-cmd &> /dev/null; then
        # Firewalld (CentOS/RHEL)
        firewall-cmd --permanent --add-port=80/tcp
        firewall-cmd --permanent --add-port=443/tcp
        firewall-cmd --permanent --add-port=8443/tcp
        firewall-cmd --reload
        log "Firewalld rules added"
    else
        warning "No supported firewall detected. Please manually configure your firewall."
    fi
}

# Function to start services
start_services() {
    log "Starting Hiddify services..."
    
    cd "$HIDDIFY_DIR"
    
    # Pull latest images
    docker-compose pull
    
    # Start services
    if docker-compose up -d; then
        log "Hiddify services started successfully"
    else
        error "Failed to start Hiddify services"
    fi
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30
    
    # Check service status
    if docker-compose ps | grep -q "Up"; then
        log "All services are running"
        docker-compose ps
    else
        error "Some services failed to start"
    fi
}

# Function to create SSL certificates
setup_ssl() {
    log "Setting up SSL certificates..."
    
    # Create certificates directory
    mkdir -p "$HIDDIFY_DATA_DIR/caddy/certs"
    
    # Generate self-signed certificate for testing
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$HIDDIFY_DATA_DIR/caddy/certs/private.key" \
        -out "$HIDDIFY_DATA_DIR/caddy/certs/certificate.crt" \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=$HIDDIFY_DOMAIN"
    
    log "Self-signed certificate created for testing"
    info "For production, replace with Let's Encrypt certificates"
}

# Function to create backup script
create_backup_script() {
    log "Creating backup script..."
    
    cat > "$HIDDIFY_DIR/backup.sh" << 'EOF'
#!/bin/bash

# Hiddify Backup Script

HIDDIFY_DATA_DIR="/opt/hiddify-data"
BACKUP_DIR="/opt/hiddify-backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Stop services
cd /opt/hiddify
docker-compose down

# Create backup
tar -czf "$BACKUP_DIR/hiddify-backup-$DATE.tar.gz" -C "$HIDDIFY_DATA_DIR" .

# Start services
docker-compose up -d

# Clean old backups (keep last 7 days)
find "$BACKUP_DIR" -name "hiddify-backup-*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/hiddify-backup-$DATE.tar.gz"
EOF
    
    chmod +x "$HIDDIFY_DIR/backup.sh"
    
    # Add to crontab for daily backups
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/hiddify/backup.sh") | crontab -
    
    log "Backup script created and scheduled"
}

# Function to display installation summary
display_summary() {
    log "Installation completed successfully!"
    echo
    echo "=========================================="
    echo "         Hiddify Manager Installation     "
    echo "=========================================="
    echo
    echo "Installation Directory: $HIDDIFY_DIR"
    echo "Data Directory: $HIDDIFY_DATA_DIR"
    echo "Domain: $HIDDIFY_DOMAIN"
    echo "Port: $HIDDIFY_PORT"
    echo "Email: $HIDDIFY_EMAIL"
    echo
    echo "Access Information:"
    echo "  Web Interface: https://$HIDDIFY_DOMAIN"
    echo "  Admin Username: admin"
    echo "  Admin Password: admin123"
    echo
    echo "Management Commands:"
    echo "  Start:   hiddify-manager start"
    echo "  Stop:    hiddify-manager stop"
    echo "  Restart: hiddify-manager restart"
    echo "  Status:  hiddify-manager status"
    echo "  Logs:    hiddify-manager logs"
    echo "  Update:  hiddify-manager update"
    echo "  Backup:  hiddify-manager backup"
    echo
    echo "Docker Commands:"
    echo "  View logs: docker-compose logs -f"
    echo "  View status: docker-compose ps"
    echo "  Update images: docker-compose pull"
    echo
    echo "Next Steps:"
    echo "1. Update domain configuration in .env file"
    echo "2. Configure SSL certificates for production"
    echo "3. Change default admin password"
    echo "4. Configure your VPN servers"
    echo "5. Set up monitoring and alerts"
    echo
    echo "Configuration files:"
    echo "- Docker Compose: $HIDDIFY_DIR/docker-compose.yml"
    echo "- Environment: $HIDDIFY_DIR/.env"
    echo "- Caddy Config: $HIDDIFY_DATA_DIR/caddy/Caddyfile"
    echo
    echo "For more information, visit: https://github.com/hiddify/hiddify"
    echo
}

# Function to prompt for configuration
prompt_configuration() {
    echo
    echo "=========================================="
    echo "         Hiddify Configuration            "
    echo "=========================================="
    echo
    
    read -p "Enter your domain name (e.g., vpn.yourdomain.com): " HIDDIFY_DOMAIN
    read -p "Enter your email address: " HIDDIFY_EMAIL
    read -p "Enter admin username [admin]: " ADMIN_USERNAME
    read -p "Enter admin password [admin123]: " ADMIN_PASSWORD
    
    # Set defaults if empty
    ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
    ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}
    
    echo
    echo "Configuration Summary:"
    echo "  Domain: $HIDDIFY_DOMAIN"
    echo "  Email: $HIDDIFY_EMAIL"
    echo "  Admin Username: $ADMIN_USERNAME"
    echo "  Admin Password: $ADMIN_PASSWORD"
    echo
    
    read -p "Continue with this configuration? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        error "Installation cancelled"
    fi
}

# Main installation function
main() {
    log "Starting Hiddify Manager installation..."
    
    # Check prerequisites
    check_root
    detect_os
    
    # Prompt for configuration
    prompt_configuration
    
    # Installation steps
    install_dependencies
    create_directories
    create_docker_compose
    create_caddy_config
    create_env_file
    create_management_script
    configure_firewall
    setup_ssl
    create_backup_script
    start_services
    
    # Display summary
    display_summary
    
    log "Installation log saved to: $LOG_FILE"
}

# Run main function
main "$@"
