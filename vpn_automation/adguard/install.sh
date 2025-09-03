#!/bin/bash

# AdGuard Home Installation Script
# Comprehensive setup for AdGuard Home with monitoring and security

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ADGUARD_VERSION="latest"
DOCKER_COMPOSE_VERSION="2.20.0"
PROMETHEUS_VERSION="latest"
GRAFANA_VERSION="latest"
TRAEFIK_VERSION="v2.10"

# Logging
LOG_FILE="adguard_install.log"
exec > >(tee -a "$LOG_FILE") 2>&1

# Functions
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

check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        exit 1
    fi
}

check_system() {
    log_info "Checking system requirements..."
    
    # Check OS
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        log_error "Cannot detect OS"
        exit 1
    fi
    
    log_info "Detected OS: $OS $VER"
    
    # Check architecture
    ARCH=$(uname -m)
    if [[ "$ARCH" != "x86_64" && "$ARCH" != "aarch64" ]]; then
        log_error "Unsupported architecture: $ARCH"
        exit 1
    fi
    
    log_info "Architecture: $ARCH"
}

install_dependencies() {
    log_info "Installing system dependencies..."
    
    case $OS in
        "Ubuntu"|"Debian GNU/Linux")
            sudo apt update
            sudo apt install -y \
                curl \
                wget \
                git \
                jq \
                openssl \
                certbot \
                python3-certbot-nginx \
                ufw \
                fail2ban \
                htop \
                net-tools \
                dnsutils
            ;;
        "CentOS Linux"|"Red Hat Enterprise Linux")
            sudo yum update -y
            sudo yum install -y \
                curl \
                wget \
                git \
                jq \
                openssl \
                epel-release \
                certbot \
                python3-certbot-nginx \
                firewalld \
                fail2ban \
                htop \
                net-tools \
                bind-utils
            ;;
        *)
            log_error "Unsupported OS: $OS"
            exit 1
            ;;
    esac
    
    log_success "Dependencies installed"
}

install_docker() {
    log_info "Installing Docker..."
    
    if command -v docker &> /dev/null; then
        log_info "Docker is already installed"
        return
    fi
    
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    
    log_success "Docker installed"
    log_warning "Please log out and back in for docker group changes to take effect"
}

install_docker_compose() {
    log_info "Installing Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        log_info "Docker Compose is already installed"
        return
    fi
    
    sudo curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    log_success "Docker Compose installed"
}

create_directories() {
    log_info "Creating directory structure..."
    
    mkdir -p {certs,backups,custom_filters,monitoring/{grafana/{provisioning,dashboards},prometheus},traefik}
    
    # Set permissions
    chmod 700 certs
    chmod 755 backups custom_filters monitoring traefik
    
    log_success "Directories created"
}

generate_ssl_certificates() {
    log_info "Setting up SSL certificates..."
    
    read -p "Enter your domain name for AdGuard Home (e.g., dns.example.com): " DOMAIN
    
    if [[ -z "$DOMAIN" ]]; then
        log_warning "No domain provided, using self-signed certificate"
        generate_self_signed_cert
        return
    fi
    
    # Check if domain is reachable
    if ! nslookup $DOMAIN &> /dev/null; then
        log_warning "Domain $DOMAIN not reachable, using self-signed certificate"
        generate_self_signed_cert
        return
    fi
    
    # Stop any services using port 80/443
    sudo systemctl stop nginx 2>/dev/null || true
    sudo systemctl stop apache2 2>/dev/null || true
    
    # Generate Let's Encrypt certificate
    sudo certbot certonly --standalone \
        --email admin@$DOMAIN \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN
    
    # Copy certificates
    sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem certs/cert.pem
    sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem certs/privkey.pem
    
    # Set permissions
    sudo chown $USER:$USER certs/cert.pem certs/privkey.pem
    chmod 600 certs/cert.pem certs/privkey.pem
    
    log_success "SSL certificates generated for $DOMAIN"
}

generate_self_signed_cert() {
    log_info "Generating self-signed certificate..."
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout certs/privkey.pem \
        -out certs/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    
    chmod 600 certs/cert.pem certs/privkey.pem
    
    log_success "Self-signed certificate generated"
}

configure_adguard() {
    log_info "Configuring AdGuard Home..."
    
    # Generate admin password hash
    read -s -p "Enter admin password for AdGuard Home: " ADMIN_PASSWORD
    echo
    
    if [[ -z "$ADMIN_PASSWORD" ]]; then
        ADMIN_PASSWORD="admin123"
        log_warning "Using default password: admin123"
    fi
    
    # Hash password (using Python)
    PASSWORD_HASH=$(python3 -c "
import bcrypt
password = '$ADMIN_PASSWORD'.encode('utf-8')
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password, salt)
print(hashed.decode('utf-8'))
")
    
    # Create configuration
    cat > AdGuardHome.yaml << EOF
http:
  pprof:
    port: 6060
    enabled: false
  address: 0.0.0.0:3000
  session_ttl: 720h
  users:
    - name: admin
      password: $PASSWORD_HASH
  auth_attempts: 5
  block_auth_min: 15
  http_proxy: ""
  language: en
  theme: auto

dns:
  bind_hosts:
    - 0.0.0.0
  port: 53
  anonymize_client_ip: false
  protection_enabled: true
  blocking_mode: default
  blocking_ipv4: ""
  blocking_ipv6: ""
  blocked_response_ttl: 10
  parental_block_host: family-block.dns.adguard.com
  safebrowsing_block_host: standard-block.dns.adguard.com
  ratelimit: 20
  ratelimit_whitelist: []
  refuse_any: true
  upstream_dns:
    - 1.1.1.1
    - 8.8.8.8
    - tls://cloudflare-dns.com
    - https://dns.cloudflare.com/dns-query
    - tls://dns.google
    - https://dns.google/dns-query
  upstream_dns_file: ""
  bootstrap_dns:
    - 9.9.9.10
    - 149.112.112.10
    - 2620:fe::10
    - 2620:fe::fe:10
  all_servers: false
  fastest_addr: false
  fastest_timeout: 1s
  allowed_clients: []
  disallowed_clients: []
  blocked_hosts:
    - version.bind
    - id.server
    - hostname.bind
  cache_size: 4194304
  cache_ttl_min: 0
  cache_ttl_max: 0
  cache_optimistic: false
  bogus_nxdomain: []
  aaaa_disabled: false
  enable_dnssec: false
  edns_client_subnet:
    custom_ip: ""
    enabled: false
    use_custom: false
  max_goroutines: 300
  handle_ddr: true
  ipset: []
  ipset_file: ""
  filtering_enabled: true
  filters_update_interval: 24
  parental_enabled: false
  safesearch_enabled: false
  safebrowsing_enabled: false
  safebrowsing_cache_size: 1048576
  safesearch_cache_size: 1048576
  parental_cache_size: 1048576
  cache_time: 30
  rewrites: []
  blocked_services: []
  upstream_timeout: 10s
  private_networks: []
  use_private_ptr_resolvers: true
  local_ptr_upstreams: []
  use_dns64: false
  dns64_prefixes: []
  serve_http3: false
  use_http3_upstreams: false

tls:
  enabled: true
  server_name: localhost
  force_https: true
  port_https: 443
  port_dns_over_tls: 853
  port_dns_over_quic: 784
  port_dnscrypt: 0
  dnscrypt_config_file: ""
  allow_unencrypted_doh: false
  certificate_chain: /opt/adguardhome/certs/cert.pem
  private_key: /opt/adguardhome/certs/privkey.pem
  certificate_path: ""
  private_key_path: ""
  strict_sni_check: false

querylog:
  ignored: []
  interval: 2160h
  size_memory: 1000
  enabled: true
  file_enabled: true

statistics:
  ignored: []
  interval: 24h
  enabled: true

filters:
  - enabled: true
    url: https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt
    name: AdGuard DNS filter
    id: 1
  - enabled: true
    url: https://someonewhocares.org/hosts/zero/hosts
    name: Dan Pollock's List
    id: 2
  - enabled: true
    url: https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts
    name: StevenBlack's List
    id: 3
  - enabled: true
    url: https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/fakenews-gambling-porn/hosts
    name: Malware Domain List
    id: 4
  - enabled: true
    url: https://dbl.oisd.nl/
    name: OISD Full List
    id: 5

whitelist_filters: []

user_rules:
  - "||example.com^$important"
  - "||test.example.com^"
  - "||blocked-domain.com^"

dhcp:
  enabled: false

clients:
  runtime_sources:
    whois: true
    arp: true
    rdns: true
    dhcp: true
    hosts: true
  persistent: []

log_file: ""
log_max_backups: 0
log_max_size: 100
log_max_age: 3
log_compress: false
log_localtime: false
verbose: false
schema_version: 24
EOF
    
    log_success "AdGuard Home configuration created"
}

configure_monitoring() {
    log_info "Configuring monitoring..."
    
    # Prometheus configuration
    cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'adguard-home'
    static_configs:
      - targets: ['adguard-home:3000']
    metrics_path: /control/metrics
    scrape_interval: 15s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          # - alertmanager:9093
EOF
    
    # Grafana provisioning
    mkdir -p monitoring/grafana/provisioning/{datasources,dashboards}
    
    # Datasource configuration
    cat > monitoring/grafana/provisioning/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF
    
    # Dashboard configuration
    cat > monitoring/grafana/provisioning/dashboards/dashboard.yml << EOF
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF
    
    # Create sample dashboard
    cat > monitoring/grafana/dashboards/adguard-dashboard.json << EOF
{
  "dashboard": {
    "id": null,
    "title": "AdGuard Home Dashboard",
    "tags": ["adguard", "dns"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "DNS Queries",
        "type": "stat",
        "targets": [
          {
            "expr": "adguard_dns_queries_total",
            "legendFormat": "Total Queries"
          }
        ]
      },
      {
        "id": 2,
        "title": "Blocked Queries",
        "type": "stat",
        "targets": [
          {
            "expr": "adguard_dns_blocked_total",
            "legendFormat": "Blocked"
          }
        ]
      }
    ]
  }
}
EOF
    
    log_success "Monitoring configuration created"
}

configure_traefik() {
    log_info "Configuring Traefik..."
    
    # Traefik configuration
    cat > traefik/traefik.yml << EOF
api:
  dashboard: true
  insecure: false

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entrypoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"
  dns:
    address: ":53"
    udp:
      address: ":53"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
  file:
    directory: /etc/traefik/dynamic
    watch: true

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: /acme.json
      httpChallenge:
        entryPoint: web

log:
  level: INFO

accessLog: {}
EOF
    
    # Create ACME file
    touch traefik/acme.json
    chmod 600 traefik/acme.json
    
    log_success "Traefik configuration created"
}

configure_firewall() {
    log_info "Configuring firewall..."
    
    case $OS in
        "Ubuntu"|"Debian GNU/Linux")
            sudo ufw --force enable
            sudo ufw default deny incoming
            sudo ufw default allow outgoing
            sudo ufw allow ssh
            sudo ufw allow 53/tcp
            sudo ufw allow 53/udp
            sudo ufw allow 443/tcp
            sudo ufw allow 853/tcp
            sudo ufw allow 784/udp
            sudo ufw allow 3000/tcp
            sudo ufw allow 9090/tcp
            sudo ufw allow 3001/tcp
            ;;
        "CentOS Linux"|"Red Hat Enterprise Linux")
            sudo systemctl enable firewalld
            sudo systemctl start firewalld
            sudo firewall-cmd --permanent --add-service=ssh
            sudo firewall-cmd --permanent --add-port=53/tcp
            sudo firewall-cmd --permanent --add-port=53/udp
            sudo firewall-cmd --permanent --add-port=443/tcp
            sudo firewall-cmd --permanent --add-port=853/tcp
            sudo firewall-cmd --permanent --add-port=784/udp
            sudo firewall-cmd --permanent --add-port=3000/tcp
            sudo firewall-cmd --permanent --add-port=9090/tcp
            sudo firewall-cmd --permanent --add-port=3001/tcp
            sudo firewall-cmd --reload
            ;;
    esac
    
    log_success "Firewall configured"
}

configure_fail2ban() {
    log_info "Configuring Fail2ban..."
    
    # Create AdGuard Home jail
    sudo tee /etc/fail2ban/jail.local > /dev/null << EOF
[adguard-home]
enabled = true
port = 3000
filter = adguard-home
logpath = /var/log/adguard-home.log
maxretry = 5
bantime = 3600
findtime = 600
EOF
    
    # Create filter
    sudo tee /etc/fail2ban/filter.d/adguard-home.conf > /dev/null << EOF
[Definition]
failregex = ^.*Failed login attempt from <HOST>.*$
ignoreregex =
EOF
    
    sudo systemctl enable fail2ban
    sudo systemctl restart fail2ban
    
    log_success "Fail2ban configured"
}

create_management_script() {
    log_info "Creating management script..."
    
    cat > manage_adguard.sh << 'EOF'
#!/bin/bash

# AdGuard Home Management Script

set -e

ADGUARD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$1" in
    start)
        echo "Starting AdGuard Home..."
        cd "$ADGUARD_DIR"
        docker-compose up -d
        echo "AdGuard Home started"
        ;;
    stop)
        echo "Stopping AdGuard Home..."
        cd "$ADGUARD_DIR"
        docker-compose down
        echo "AdGuard Home stopped"
        ;;
    restart)
        echo "Restarting AdGuard Home..."
        cd "$ADGUARD_DIR"
        docker-compose restart
        echo "AdGuard Home restarted"
        ;;
    status)
        echo "AdGuard Home Status:"
        cd "$ADGUARD_DIR"
        docker-compose ps
        ;;
    logs)
        echo "AdGuard Home Logs:"
        cd "$ADGUARD_DIR"
        docker-compose logs -f adguard-home
        ;;
    backup)
        echo "Creating backup..."
        cd "$ADGUARD_DIR"
        docker-compose run --rm backup
        echo "Backup completed"
        ;;
    update)
        echo "Updating AdGuard Home..."
        cd "$ADGUARD_DIR"
        docker-compose pull
        docker-compose up -d
        echo "AdGuard Home updated"
        ;;
    config)
        echo "Reloading configuration..."
        curl -X POST http://localhost:3000/control/reload_config
        echo "Configuration reloaded"
        ;;
    stats)
        echo "AdGuard Home Statistics:"
        curl http://localhost:3000/control/stats | jq .
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|backup|update|config|stats}"
        exit 1
        ;;
esac
EOF
    
    chmod +x manage_adguard.sh
    
    log_success "Management script created"
}

create_systemd_service() {
    log_info "Creating systemd service..."
    
    sudo tee /etc/systemd/system/adguard-home.service > /dev/null << EOF
[Unit]
Description=AdGuard Home DNS Server
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable adguard-home.service
    
    log_success "Systemd service created"
}

start_services() {
    log_info "Starting AdGuard Home services..."
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to start..."
    sleep 30
    
    # Check service status
    if docker-compose ps | grep -q "Up"; then
        log_success "Services started successfully"
    else
        log_error "Some services failed to start"
        docker-compose logs
        exit 1
    fi
}

test_installation() {
    log_info "Testing installation..."
    
    # Test DNS resolution
    if nslookup google.com 127.0.0.1 &> /dev/null; then
        log_success "DNS resolution working"
    else
        log_error "DNS resolution failed"
    fi
    
    # Test web interface
    if curl -s http://localhost:3000 &> /dev/null; then
        log_success "Web interface accessible"
    else
        log_error "Web interface not accessible"
    fi
    
    # Test Prometheus metrics
    if curl -s http://localhost:9090 &> /dev/null; then
        log_success "Prometheus accessible"
    else
        log_error "Prometheus not accessible"
    fi
    
    # Test Grafana
    if curl -s http://localhost:3001 &> /dev/null; then
        log_success "Grafana accessible"
    else
        log_error "Grafana not accessible"
    fi
}

print_summary() {
    log_success "AdGuard Home installation completed!"
    
    echo
    echo "=== Installation Summary ==="
    echo "AdGuard Home Web Interface: http://localhost:3000"
    echo "Prometheus: http://localhost:9090"
    echo "Grafana: http://localhost:3001"
    echo
    echo "=== Management Commands ==="
    echo "Start services: ./manage_adguard.sh start"
    echo "Stop services: ./manage_adguard.sh stop"
    echo "View logs: ./manage_adguard.sh logs"
    echo "Create backup: ./manage_adguard.sh backup"
    echo
    echo "=== Next Steps ==="
    echo "1. Access the web interface and complete initial setup"
    echo "2. Configure your router to use this server as DNS"
    echo "3. Set up monitoring alerts"
    echo "4. Configure custom filter lists"
    echo
    echo "=== Security Notes ==="
    echo "- Change default passwords"
    echo "- Configure firewall rules"
    echo "- Set up SSL certificates"
    echo "- Enable monitoring and alerts"
    echo
    echo "Installation log: $LOG_FILE"
}

# Main installation process
main() {
    log_info "Starting AdGuard Home installation..."
    
    check_root
    check_system
    install_dependencies
    install_docker
    install_docker_compose
    create_directories
    generate_ssl_certificates
    configure_adguard
    configure_monitoring
    configure_traefik
    configure_firewall
    configure_fail2ban
    create_management_script
    create_systemd_service
    start_services
    test_installation
    print_summary
    
    log_success "Installation completed successfully!"
}

# Run main function
main "$@"
