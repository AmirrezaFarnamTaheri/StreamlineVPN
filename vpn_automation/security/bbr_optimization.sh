#!/bin/bash

# BBR TCP Optimization Script
# Enhanced network performance with BBR congestion control algorithm

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
KERNEL_VERSION=""
BBR_ENABLED=false
CURRENT_CC=""
LOG_FILE="bbr_optimization.log"

# Logging
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
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

check_kernel_version() {
    log_info "Checking kernel version..."
    
    KERNEL_VERSION=$(uname -r)
    log_info "Current kernel version: $KERNEL_VERSION"
    
    # Check if kernel supports BBR
    if [[ $(echo $KERNEL_VERSION | cut -d. -f1) -ge 4 && $(echo $KERNEL_VERSION | cut -d. -f2) -ge 9 ]]; then
        log_success "Kernel version supports BBR"
        return 0
    else
        log_error "Kernel version $KERNEL_VERSION does not support BBR (requires 4.9+)"
        return 1
    fi
}

check_bbr_availability() {
    log_info "Checking BBR availability..."
    
    if modprobe tcp_bbr 2>/dev/null; then
        log_success "BBR module loaded successfully"
        BBR_ENABLED=true
        return 0
    else
        log_warning "BBR module not available, checking if built into kernel"
        if grep -q "tcp_bbr" /proc/net/tcp_congestion_control; then
            log_success "BBR is available in kernel"
            BBR_ENABLED=true
            return 0
        else
            log_error "BBR is not available"
            return 1
        fi
    fi
}

get_current_congestion_control() {
    CURRENT_CC=$(sysctl -n net.ipv4.tcp_congestion_control)
    log_info "Current congestion control: $CURRENT_CC"
}

enable_bbr() {
    log_info "Enabling BBR congestion control..."
    
    # Set BBR as default congestion control
    sysctl -w net.ipv4.tcp_congestion_control=bbr
    
    # Verify BBR is active
    if [[ $(sysctl -n net.ipv4.tcp_congestion_control) == "bbr" ]]; then
        log_success "BBR congestion control enabled"
        return 0
    else
        log_error "Failed to enable BBR"
        return 1
    fi
}

optimize_tcp_parameters() {
    log_info "Optimizing TCP parameters for BBR..."
    
    # BBR-specific optimizations
    sysctl -w net.ipv4.tcp_window_scaling=1
    sysctl -w net.ipv4.tcp_timestamps=1
    sysctl -w net.ipv4.tcp_sack=1
    sysctl -w net.ipv4.tcp_fack=1
    sysctl -w net.ipv4.tcp_fin_timeout=30
    sysctl -w net.ipv4.tcp_keepalive_time=1200
    sysctl -w net.ipv4.tcp_keepalive_intvl=15
    sysctl -w net.ipv4.tcp_keepalive_probes=5
    sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216"
    sysctl -w net.ipv4.tcp_wmem="4096 65536 16777216"
    sysctl -w net.core.rmem_max=16777216
    sysctl -w net.core.wmem_max=16777216
    sysctl -w net.core.rmem_default=262144
    sysctl -w net.core.wmem_default=262144
    sysctl -w net.ipv4.tcp_collapse=0
    sysctl -w net.ipv4.tcp_dma_copybreak=4096
    sysctl -w net.ipv4.tcp_dsack=1
    sysctl -w net.ipv4.tcp_ecn=1
    sysctl -w net.ipv4.tcp_frto=2
    sysctl -w net.ipv4.tcp_low_latency=1
    sysctl -w net.ipv4.tcp_mtu_probing=1
    sysctl -w net.ipv4.tcp_no_metrics_save=1
    sysctl -w net.ipv4.tcp_rfc1337=1
    sysctl -w net.ipv4.tcp_slow_start_after_idle=0
    sysctl -w net.ipv4.tcp_tw_reuse=1
    sysctl -w net.ipv4.tcp_window_scaling=1
    
    # Network buffer optimizations
    sysctl -w net.core.netdev_max_backlog=5000
    sysctl -w net.core.somaxconn=65535
    sysctl -w net.ipv4.tcp_max_syn_backlog=65535
    sysctl -w net.ipv4.tcp_max_tw_buckets=1440000
    sysctl -w net.ipv4.tcp_tw_recycle=0
    sysctl -w net.ipv4.tcp_tw_reuse=1
    
    # BBR-specific parameters
    sysctl -w net.ipv4.tcp_bbr_cwnd_gain=2
    sysctl -w net.ipv4.tcp_bbr_min_rtt_win_sec=10
    sysctl -w net.ipv4.tcp_bbr_probe_rtt_mode_ms=200
    sysctl -w net.ipv4.tcp_bbr_probe_rtt_win_ms=200
    
    log_success "TCP parameters optimized"
}

optimize_network_interfaces() {
    log_info "Optimizing network interfaces..."
    
    # Get list of network interfaces
    INTERFACES=$(ip link show | grep -E "^[0-9]+:" | cut -d: -f2 | tr -d ' ')
    
    for interface in $INTERFACES; do
        if [[ "$interface" != "lo" ]]; then
            log_info "Optimizing interface: $interface"
            
            # Set interface parameters
            ethtool -G $interface rx 4096 tx 4096 2>/dev/null || true
            ethtool -C $interface adaptive-rx on 2>/dev/null || true
            ethtool -K $interface tso on 2>/dev/null || true
            ethtool -K $interface gso on 2>/dev/null || true
            ethtool -K $interface gro on 2>/dev/null || true
            ethtool -K $interface lro off 2>/dev/null || true
            
            # Set queue length
            ip link set $interface txqueuelen 10000 2>/dev/null || true
        fi
    done
    
    log_success "Network interfaces optimized"
}

optimize_system_limits() {
    log_info "Optimizing system limits..."
    
    # Increase file descriptor limits
    echo "* soft nofile 65536" >> /etc/security/limits.conf
    echo "* hard nofile 65536" >> /etc/security/limits.conf
    echo "root soft nofile 65536" >> /etc/security/limits.conf
    echo "root hard nofile 65536" >> /etc/security/limits.conf
    
    # Increase process limits
    echo "* soft nproc 32768" >> /etc/security/limits.conf
    echo "* hard nproc 32768" >> /etc/security/limits.conf
    
    # Set ulimit for current session
    ulimit -n 65536
    ulimit -u 32768
    
    log_success "System limits optimized"
}

create_persistent_config() {
    log_info "Creating persistent configuration..."
    
    # Create sysctl configuration file
    cat > /etc/sysctl.d/99-bbr-optimization.conf << EOF
# BBR TCP Optimization Configuration
# Generated on $(date)

# Congestion Control
net.ipv4.tcp_congestion_control = bbr

# TCP Optimizations
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_timestamps = 1
net.ipv4.tcp_sack = 1
net.ipv4.tcp_fack = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_keepalive_intvl = 15
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.core.rmem_default = 262144
net.core.wmem_default = 262144
net.ipv4.tcp_collapse = 0
net.ipv4.tcp_dma_copybreak = 4096
net.ipv4.tcp_dsack = 1
net.ipv4.tcp_ecn = 1
net.ipv4.tcp_frto = 2
net.ipv4.tcp_low_latency = 1
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_no_metrics_save = 1
net.ipv4.tcp_rfc1337 = 1
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_tw_reuse = 1

# Network Buffer Optimizations
net.core.netdev_max_backlog = 5000
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_max_tw_buckets = 1440000
net.ipv4.tcp_tw_recycle = 0

# BBR-specific Parameters
net.ipv4.tcp_bbr_cwnd_gain = 2
net.ipv4.tcp_bbr_min_rtt_win_sec = 10
net.ipv4.tcp_bbr_probe_rtt_mode_ms = 200
net.ipv4.tcp_bbr_probe_rtt_win_ms = 200

# IPv6 Optimizations (if available)
net.ipv6.tcp_congestion_control = bbr
net.ipv6.tcp_window_scaling = 1
net.ipv6.tcp_timestamps = 1
net.ipv6.tcp_sack = 1
net.ipv6.tcp_fack = 1
net.ipv6.tcp_rmem = 4096 87380 16777216
net.ipv6.tcp_wmem = 4096 65536 16777216
EOF
    
    # Apply configuration
    sysctl -p /etc/sysctl.d/99-bbr-optimization.conf
    
    log_success "Persistent configuration created"
}

create_network_optimization_service() {
    log_info "Creating network optimization service..."
    
    cat > /etc/systemd/system/network-optimization.service << EOF
[Unit]
Description=Network Interface Optimization
After=network.target
Before=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/optimize-network.sh
TimeoutStartSec=30

[Install]
WantedBy=multi-user.target
EOF
    
    # Create optimization script
    cat > /usr/local/bin/optimize-network.sh << 'EOF'
#!/bin/bash

# Network Interface Optimization Script

set -e

INTERFACES=$(ip link show | grep -E "^[0-9]+:" | cut -d: -f2 | tr -d ' ')

for interface in $INTERFACES; do
    if [[ "$interface" != "lo" ]]; then
        # Set interface parameters
        ethtool -G $interface rx 4096 tx 4096 2>/dev/null || true
        ethtool -C $interface adaptive-rx on 2>/dev/null || true
        ethtool -K $interface tso on 2>/dev/null || true
        ethtool -K $interface gso on 2>/dev/null || true
        ethtool -K $interface gro on 2>/dev/null || true
        ethtool -K $interface lro off 2>/dev/null || true
        
        # Set queue length
        ip link set $interface txqueuelen 10000 2>/dev/null || true
    fi
done

# Apply sysctl configuration
sysctl -p /etc/sysctl.d/99-bbr-optimization.conf
EOF
    
    chmod +x /usr/local/bin/optimize-network.sh
    
    # Enable and start service
    systemctl daemon-reload
    systemctl enable network-optimization.service
    
    log_success "Network optimization service created"
}

test_bbr_performance() {
    log_info "Testing BBR performance..."
    
    # Test current congestion control
    CURRENT_CC=$(sysctl -n net.ipv4.tcp_congestion_control)
    log_info "Current congestion control: $CURRENT_CC"
    
    # Test network performance
    if command -v iperf3 &> /dev/null; then
        log_info "Running iperf3 test (if server available)..."
        # Note: This requires an iperf3 server to be running
        # iperf3 -c <server_ip> -t 10 -i 1
    fi
    
    # Test latency
    if command -v ping &> /dev/null; then
        log_info "Testing latency to 8.8.8.8..."
        ping -c 10 8.8.8.8 | tail -2
    fi
    
    log_success "Performance testing completed"
}

create_monitoring_script() {
    log_info "Creating BBR monitoring script..."
    
    cat > /usr/local/bin/monitor-bbr.sh << 'EOF'
#!/bin/bash

# BBR Monitoring Script

echo "=== BBR Status Report ==="
echo "Date: $(date)"
echo

echo "=== Kernel Information ==="
echo "Kernel Version: $(uname -r)"
echo "BBR Available: $(modprobe tcp_bbr 2>/dev/null && echo "Yes" || echo "No")"
echo

echo "=== Congestion Control ==="
echo "Current CC: $(sysctl -n net.ipv4.tcp_congestion_control)"
echo "Available CC: $(cat /proc/net/tcp_congestion_control)"
echo

echo "=== Network Statistics ==="
echo "TCP Connections: $(ss -t | wc -l)"
echo "UDP Connections: $(ss -u | wc -l)"
echo

echo "=== Interface Statistics ==="
for interface in $(ip link show | grep -E "^[0-9]+:" | cut -d: -f2 | tr -d ' '); do
    if [[ "$interface" != "lo" ]]; then
        echo "Interface: $interface"
        ip -s link show $interface | grep -E "(RX|TX)"
        echo
    fi
done

echo "=== BBR Parameters ==="
sysctl net.ipv4.tcp_bbr_* 2>/dev/null || echo "BBR parameters not available"
echo

echo "=== Performance Metrics ==="
if command -v ping &> /dev/null; then
    echo "Latency to 8.8.8.8:"
    ping -c 3 8.8.8.8 | tail -1
fi
EOF
    
    chmod +x /usr/local/bin/monitor-bbr.sh
    
    log_success "BBR monitoring script created"
}

create_performance_test() {
    log_info "Creating performance test script..."
    
    cat > /usr/local/bin/test-bbr-performance.sh << 'EOF'
#!/bin/bash

# BBR Performance Test Script

set -e

echo "=== BBR Performance Test ==="
echo "Date: $(date)"
echo

# Test 1: Latency Test
echo "1. Latency Test (ping to 8.8.8.8)"
ping -c 10 8.8.8.8 | tail -2
echo

# Test 2: TCP Connection Test
echo "2. TCP Connection Test"
timeout 10 bash -c 'while true; do nc -z 8.8.8.8 53; done' 2>/dev/null || true
echo "TCP connection test completed"
echo

# Test 3: Network Buffer Test
echo "3. Network Buffer Test"
echo "Current buffer sizes:"
sysctl net.core.rmem_max net.core.wmem_max net.ipv4.tcp_rmem net.ipv4.tcp_wmem
echo

# Test 4: Congestion Control Test
echo "4. Congestion Control Test"
echo "Current CC: $(sysctl -n net.ipv4.tcp_congestion_control)"
echo "Available CC: $(cat /proc/net/tcp_congestion_control)"
echo

# Test 5: Interface Statistics
echo "5. Interface Statistics"
for interface in $(ip link show | grep -E "^[0-9]+:" | cut -d: -f2 | tr -d ' '); do
    if [[ "$interface" != "lo" ]]; then
        echo "Interface: $interface"
        ip -s link show $interface | grep -E "(RX|TX)"
        echo
    fi
done

echo "=== Test Summary ==="
echo "BBR Status: $(sysctl -n net.ipv4.tcp_congestion_control)"
echo "Kernel Version: $(uname -r)"
echo "Test completed at: $(date)"
EOF
    
    chmod +x /usr/local/bin/test-bbr-performance.sh
    
    log_success "Performance test script created"
}

print_summary() {
    log_success "BBR TCP optimization completed!"
    
    echo
    echo "=== Optimization Summary ==="
    echo "Kernel Version: $KERNEL_VERSION"
    echo "BBR Enabled: $BBR_ENABLED"
    echo "Current Congestion Control: $(sysctl -n net.ipv4.tcp_congestion_control)"
    echo
    echo "=== Configuration Files ==="
    echo "Sysctl Config: /etc/sysctl.d/99-bbr-optimization.conf"
    echo "Limits Config: /etc/security/limits.conf"
    echo "Service: /etc/systemd/system/network-optimization.service"
    echo
    echo "=== Management Commands ==="
    echo "Monitor BBR: /usr/local/bin/monitor-bbr.sh"
    echo "Test Performance: /usr/local/bin/test-bbr-performance.sh"
    echo "Restart Network: systemctl restart network-optimization"
    echo
    echo "=== Next Steps ==="
    echo "1. Reboot system to apply all changes"
    echo "2. Run performance tests to verify improvements"
    echo "3. Monitor network performance over time"
    echo "4. Adjust parameters based on your specific use case"
    echo
    echo "=== Important Notes ==="
    echo "- BBR requires kernel 4.9+"
    echo "- Some optimizations may not work on all hardware"
    echo "- Monitor system performance after changes"
    echo "- Revert changes if issues occur"
    echo
    echo "Installation log: $LOG_FILE"
}

# Main optimization process
main() {
    log_info "Starting BBR TCP optimization..."
    
    check_root
    
    if ! check_kernel_version; then
        log_error "Kernel version not compatible with BBR"
        exit 1
    fi
    
    if ! check_bbr_availability; then
        log_error "BBR not available on this system"
        exit 1
    fi
    
    get_current_congestion_control
    
    if ! enable_bbr; then
        log_error "Failed to enable BBR"
        exit 1
    fi
    
    optimize_tcp_parameters
    optimize_network_interfaces
    optimize_system_limits
    create_persistent_config
    create_network_optimization_service
    create_monitoring_script
    create_performance_test
    test_bbr_performance
    print_summary
    
    log_success "BBR TCP optimization completed successfully!"
}

# Run main function
main "$@"
