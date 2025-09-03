#!/bin/bash

# VPN Server Security Hardening Script
# Comprehensive security measures for production VPN infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SSH_PORT=2222
FAIL2BAN_ENABLED=true
FIREWALL_ENABLED=true
LOG_FILE="security_hardening.log"

# Logging
exec > >(tee -a "$LOG_FILE") 2>&1

# Functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

update_system() {
    log_info "Updating system packages..."
    
    if command -v apt &> /dev/null; then
        apt update && apt upgrade -y
    elif command -v yum &> /dev/null; then
        yum update -y
    elif command -v dnf &> /dev/null; then
        dnf update -y
    fi
    
    log_success "System updated"
}

install_security_packages() {
    log_info "Installing security packages..."
    
    if command -v apt &> /dev/null; then
        apt install -y \
            fail2ban \
            ufw \
            rkhunter \
            chkrootkit \
            lynis \
            auditd \
            apparmor \
            apparmor-utils \
            clamav \
            clamav-daemon \
            unattended-upgrades
    elif command -v yum &> /dev/null; then
        yum install -y \
            fail2ban \
            firewalld \
            rkhunter \
            chkrootkit \
            lynis \
            audit \
            selinux-policy \
            clamav \
            clamav-update \
            yum-cron
    fi
    
    log_success "Security packages installed"
}

configure_ssh_security() {
    log_info "Configuring SSH security..."
    
    # Backup original config
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
    
    # Configure SSH
    cat > /etc/ssh/sshd_config << EOF
# SSH Security Configuration
Port $SSH_PORT
Protocol 2
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key

# Authentication
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes

# Security
X11Forwarding no
AllowTcpForwarding no
PermitTunnel no
MaxAuthTries 3
MaxSessions 10
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 60

# Logging
SyslogFacility AUTH
LogLevel INFO

# Allow specific users (modify as needed)
AllowUsers admin
EOF
    
    # Generate SSH keys if not exist
    if [[ ! -f /root/.ssh/id_rsa ]]; then
        ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ""
    fi
    
    log_success "SSH security configured"
}

configure_firewall() {
    if [[ "$FIREWALL_ENABLED" == "true" ]]; then
        log_info "Configuring firewall..."
        
        if command -v ufw &> /dev/null; then
            ufw --force reset
            ufw default deny incoming
            ufw default allow outgoing
            ufw allow $SSH_PORT/tcp
            ufw allow 80/tcp
            ufw allow 443/tcp
            ufw allow 53/tcp
            ufw allow 53/udp
            ufw allow 853/tcp
            ufw allow 784/udp
            ufw --force enable
        elif command -v firewall-cmd &> /dev/null; then
            systemctl enable firewalld
            systemctl start firewalld
            firewall-cmd --permanent --add-port=$SSH_PORT/tcp
            firewall-cmd --permanent --add-service=http
            firewall-cmd --permanent --add-service=https
            firewall-cmd --permanent --add-service=dns
            firewall-cmd --permanent --add-port=853/tcp
            firewall-cmd --permanent --add-port=784/udp
            firewall-cmd --reload
        fi
        
        log_success "Firewall configured"
    fi
}

configure_fail2ban() {
    if [[ "$FAIL2BAN_ENABLED" == "true" ]]; then
        log_info "Configuring Fail2ban..."
        
        # Create custom jail for SSH
        cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = $SSH_PORT
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[sshd-ddos]
enabled = true
port = $SSH_PORT
filter = sshd-ddos
logpath = /var/log/auth.log
maxretry = 2
bantime = 7200
EOF
        
        systemctl enable fail2ban
        systemctl restart fail2ban
        
        log_success "Fail2ban configured"
    fi
}

configure_system_hardening() {
    log_info "Applying system hardening..."
    
    # Disable unnecessary services
    systemctl disable bluetooth 2>/dev/null || true
    systemctl disable cups 2>/dev/null || true
    systemctl disable avahi-daemon 2>/dev/null || true
    
    # Configure system limits
    cat >> /etc/security/limits.conf << EOF
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
EOF
    
    # Configure kernel parameters
    cat > /etc/sysctl.d/99-security.conf << EOF
# Security kernel parameters
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.core.netdev_max_backlog = 5000
net.core.somaxconn = 65535
EOF
    
    sysctl -p /etc/sysctl.d/99-security.conf
    
    log_success "System hardening applied"
}

configure_audit() {
    log_info "Configuring audit system..."
    
    # Enable auditd
    systemctl enable auditd
    systemctl start auditd
    
    # Configure audit rules
    cat > /etc/audit/rules.d/99-security.rules << EOF
# Security audit rules
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/ssh/sshd_config -p wa -k sshd
-w /etc/sudoers -p wa -k sudo
-w /var/log/auth.log -p wa -k auth
-w /var/log/audit.log -p wa -k audit
EOF
    
    auditctl -R /etc/audit/rules.d/99-security.rules
    
    log_success "Audit system configured"
}

configure_antivirus() {
    log_info "Configuring antivirus..."
    
    if command -v freshclam &> /dev/null; then
        freshclam
        systemctl enable clamav-daemon
        systemctl start clamav-daemon
    fi
    
    log_success "Antivirus configured"
}

create_security_scripts() {
    log_info "Creating security monitoring scripts..."
    
    # Security check script
    cat > /usr/local/bin/security-check.sh << 'EOF'
#!/bin/bash

echo "=== Security Check Report ==="
echo "Date: $(date)"
echo

echo "=== System Updates ==="
if command -v apt &> /dev/null; then
    apt list --upgradable 2>/dev/null | wc -l | xargs echo "Available updates:"
elif command -v yum &> /dev/null; then
    yum check-update 2>/dev/null | wc -l | xargs echo "Available updates:"
fi
echo

echo "=== Failed Login Attempts ==="
grep "Failed password" /var/log/auth.log | tail -5
echo

echo "=== Suspicious Activities ==="
grep -i "suspicious\|attack\|intrusion" /var/log/auth.log | tail -5
echo

echo "=== Open Ports ==="
ss -tuln | grep LISTEN
echo

echo "=== Running Services ==="
systemctl list-units --type=service --state=running | head -10
echo

echo "=== Disk Usage ==="
df -h
echo

echo "=== Memory Usage ==="
free -h
echo
EOF
    
    chmod +x /usr/local/bin/security-check.sh
    
    # Automated security updates
    cat > /etc/cron.daily/security-updates << 'EOF'
#!/bin/bash

# Security updates script
if command -v apt &> /dev/null; then
    apt update && apt upgrade -y
elif command -v yum &> /dev/null; then
    yum update -y
fi

# Update antivirus
if command -v freshclam &> /dev/null; then
    freshclam
fi

# Run security checks
/usr/local/bin/security-check.sh >> /var/log/security-check.log
EOF
    
    chmod +x /etc/cron.daily/security-updates
    
    log_success "Security scripts created"
}

print_summary() {
    log_success "Security hardening completed!"
    
    echo
    echo "=== Security Summary ==="
    echo "SSH Port: $SSH_PORT"
    echo "Fail2ban: $FAIL2BAN_ENABLED"
    echo "Firewall: $FIREWALL_ENABLED"
    echo
    echo "=== Next Steps ==="
    echo "1. Test SSH connection on port $SSH_PORT"
    echo "2. Configure SSH keys for remote access"
    echo "3. Run security checks: /usr/local/bin/security-check.sh"
    echo "4. Monitor logs: tail -f /var/log/auth.log"
    echo "5. Schedule regular security audits"
    echo
    echo "=== Important Notes ==="
    echo "- SSH is now on port $SSH_PORT"
    echo "- Root login is disabled"
    echo "- Password authentication is disabled"
    echo "- Configure SSH keys before disconnecting"
    echo
    echo "Installation log: $LOG_FILE"
}

# Main hardening process
main() {
    log_info "Starting security hardening..."
    
    check_root
    update_system
    install_security_packages
    configure_ssh_security
    configure_firewall
    configure_fail2ban
    configure_system_hardening
    configure_audit
    configure_antivirus
    create_security_scripts
    print_summary
    
    log_success "Security hardening completed successfully!"
}

# Run main function
main "$@"
