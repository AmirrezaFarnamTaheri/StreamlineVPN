# CleanConfigs SubMerger

A high-performance, production-ready VPN subscription merger that aggregates and processes VPN configurations from multiple sources with advanced filtering, validation, and output formatting.

## 🚀 Features

- **Multi-Source Aggregation**: Process VPN sources with tiered reliability
- **Advanced Validation**: Comprehensive security and quality validation
- **Multiple Output Formats**: Raw, Base64, CSV, JSON, Sing-box, Clash
- **Web-Based Configuration Generator**: Generate VPN client configs for VLESS REALITY, WireGuard, Shadowsocks
- **Free Nodes Aggregator**: Fetches, validates, and scores free VPN nodes from public sources
- **Universal Client & QR**: Parse, manage, and export VPN configurations with QR code generation
- **Server Deployment Tools**: Xray REALITY installer and Cloudflare WS+TLS deployment packs
- **Real-time Monitoring**: Performance tracking and health checks with analytics dashboard
- **Production Deployment**: Kubernetes-ready with comprehensive monitoring
- **Security Focused**: Input validation, rate limiting, threat detection
- **Modular Architecture**: Clean, maintainable codebase with separation of concerns

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/CleanConfigs-SubMerger.git
cd CleanConfigs-SubMerger

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-enhanced.txt
```

### Basic Usage

```bash
# Run the merger
python vpn_merger_main.py

# Or use the module directly
python -m vpn_merger

# Start integrated web server (VPN merger + config generator + analytics)
python -m vpn_merger --web

# Start web server on custom port
python -m vpn_merger --web --web-port 9000

# Check system health
python -c "from vpn_merger import VPNSubscriptionMerger; print('System OK')"
```

### Production Deployment

```bash
# Run production deployment
python scripts/deploy_production.py

# Start continuous monitoring
python scripts/monitor_performance.py monitor

# Run performance test
python scripts/monitor_performance.py test
```

## 🌐 Web Interface

The integrated web server provides a comprehensive interface for VPN management:

### Access Points

- **Main Dashboard**: `http://localhost:8000` - Unified interface with links to all services
- **Configuration Generator**: `http://localhost:8080` - Generate VPN client configurations
- **Universal Client & QR**: `http://localhost:8000/client` - Parse, manage, and export VPN configurations
- **Analytics Dashboard**: `http://localhost:8081` - Real-time metrics and monitoring

### Configuration Generator Features

- **VLESS REALITY**: Generate client links with REALITY protocol support
- **sing-box JSON**: Create sing-box compatible configurations
- **WireGuard**: Generate WireGuard client configurations with QR codes
- **Shadowsocks**: Create Shadowsocks links with multiple encryption methods
- **Real-time Validation**: Input validation with error highlighting
- **QR Code Generation**: Mobile-friendly QR codes for easy client setup
- **API Endpoints**: Programmatic access to all generation functions

### Universal Client & QR Features

- **Multi-Protocol Support**: Parse VLESS, VMESS, Trojan, Shadowsocks links
- **QR Code Generation**: Generate QR codes for easy mobile client setup
- **Export Functions**: Export to sing-box JSON, raw links, or individual configs
- **Free Nodes Integration**: Fetch and manage nodes from the aggregator API
- **Quality Scoring**: Automatic scoring and sorting of nodes by quality

### Free Nodes Aggregator Features

- **Enhanced Persistence**: SQLite database with automatic backup and recovery
- **Scheduled Operations**: Auto-refresh every 20 minutes with configurable intervals
- **Health Monitoring**: TCP latency checks and automatic node scoring
- **Production Ready**: Docker containerization with health checks and monitoring
- **Multiple Protocols**: Supports VLESS, VMESS, Trojan, Shadowsocks with parsing
- **Quality Management**: Automatic pruning of unhealthy nodes and score-based ranking
- **API Integration**: RESTful API with rate limiting and CORS support
- **Export Formats**: Sing-box JSON, raw subscription text, and individual node data

### API Endpoints

```bash
# Configuration Generation
POST /api/v1/generate/vless          # Generate VLESS REALITY config
POST /api/v1/generate/singbox        # Generate sing-box JSON
POST /api/v1/generate/wireguard      # Generate WireGuard config
POST /api/v1/generate/shadowsocks    # Generate Shadowsocks config

# Utility Functions
GET /api/v1/utils/uuid               # Generate UUID
GET /api/v1/utils/shortid            # Generate short ID
GET /api/v1/utils/password           # Generate secure password
GET /api/v1/utils/wg-key             # Generate WireGuard key

# Free Nodes Aggregator
GET /aggregator/health               # Health check
GET /aggregator/nodes                # Get available nodes
GET /aggregator/stats                # Node statistics

# Enhanced Aggregator API
GET /api/nodes.json                  # Get nodes with filtering and sorting
POST /api/ingest                     # Ingest proxy links
POST /api/sources                    # Add source URLs
POST /api/refresh                    # Trigger manual refresh
GET /api/subscription.txt            # Raw subscription text
GET /api/export/singbox.json         # Sing-box outbounds
POST /api/ping                       # Health check specific nodes
```

## 🚀 Enhanced Free Nodes Aggregator

### Quick Deployment

The enhanced aggregator includes SQLite persistence, scheduled operations, and Docker deployment:

```bash
# Navigate to web directory
cd vpn_merger/web

# Run setup script (Linux/macOS)
chmod +x setup-free-nodes.sh
./setup-free-nodes.sh

# Windows users
setup-free-nodes.bat

# Manual deployment
docker-compose -f compose.free-nodes.yml up -d --build
```

**Key Features:**
- **SQLite Database**: Persistent storage with automatic backup
- **Scheduled Refresh**: Auto-updates every 20 minutes (configurable)
- **Health Monitoring**: TCP latency checks and node scoring
- **Production Ready**: Docker with health checks and monitoring
- **API Integration**: RESTful endpoints for programmatic access

### Configuration

```bash
# Add sources
curl -X POST http://localhost:8000/api/sources \
  -H 'Content-Type: application/json' \
  -d '{"urls":["https://example.com/free.txt"]}'

# Trigger refresh
curl -X POST 'http://localhost:8000/api/refresh?healthcheck=true'

# Get nodes
curl http://localhost:8000/api/nodes.json?limit=100&sort=score
```

For detailed deployment instructions, see `vpn_merger/web/DEPLOYMENT.md`

## 🚀 Deployment Tools

### Xray REALITY Installer

One-click installer for Xray-core with VLESS + REALITY protocol:

```bash
# Basic installation
curl -fsSL https://example.com/install-reality.sh -o install-reality.sh
sudo bash install-reality.sh

# Advanced options
sudo bash install-reality.sh --port 443 --server-names "www.microsoft.com" --dest "www.microsoft.com:443"
```

**Features:**
- Automatic Xray-core installation
- REALITY protocol configuration
- Firewall setup (UFW)
- BBR optimization
- Client link generation
- Health monitoring

### Cloudflare WS+TLS Deployment Pack

Production-ready deployment with Cloudflare integration:

```bash
# Setup
cd deployments/cloudflare-ws-pack
cp env.example .env
# Edit .env with your domain and UUID

# Deploy
docker compose up -d
```

**Features:**
- Nginx reverse proxy with Cloudflare Origin Certificates
- WebSocket + TLS termination
- Automatic HTTPS redirect
- Security headers
- Health checks
- Docker-based deployment

**Client Configuration:**
```
vless://<UUID>@yourdomain.com:443?encryption=none&security=tls&type=ws&path=%2Fws&sni=yourdomain.com#CF-WS
```

## 📁 Output Files

The merger generates multiple output formats:

- `vpn_subscription_raw.txt` - Raw subscription data
- `vpn_subscription_base64.txt` - Base64 encoded data
- `vpn_detailed.csv` - Detailed configuration data
- `vpn_report.json` - JSON report with metadata
- `vpn_singbox.json` - Sing-box format
- `clash.yaml` - Clash configuration

## 🔧 Configuration

### Source Configuration

Sources are managed in `config/sources.unified.yaml` with tiered organization:

- **Tier 1 Premium**: High-quality, reliable sources
- **Tier 2 Reliable**: Good quality sources
- **Tier 3 Bulk**: Large volume sources
- **Specialized**: Protocol-specific sources
- **Regional**: Geographic-specific sources
- **Experimental**: New or testing sources

### Environment Variables

```bash
# Core settings
VPN_SOURCES_CONFIG=config/sources.unified.yaml
VPN_CONCURRENT_LIMIT=50
VPN_TIMEOUT=30

# Output settings
VPN_OUTPUT_DIR=output
VPN_WRITE_BASE64=true
VPN_WRITE_CSV=true
```

## 📈 Monitoring & Metrics

### Performance Monitoring

```bash
# Real-time monitoring
python scripts/monitor_performance.py monitor

# Generate performance report
python scripts/monitor_performance.py report

# Run performance test
python scripts/monitor_performance.py test
```

### Health Checks

```bash
# Validate sources only
python -m vpn_merger --validate

# Check system health
python scripts/health_check.py
```

## 🏗️ Architecture

The project follows a modular architecture with clear separation of concerns:

### Core Modules

- **`vpn_merger/core/`**: Main business logic
  - `merger.py`: Main orchestration class
  - `source_manager.py`: Source management
  - `source_processor.py`: Source processing
  - `config_processor.py`: Configuration processing
  - `health_checker.py`: Health validation
  - `output_manager.py`: Output formatting

- **`vpn_merger/discovery/`**: Real-time source discovery
  - `github_monitor.py`: GitHub repository monitoring
  - `telegram_monitor.py`: Telegram channel monitoring
  - `web_crawler.py`: Web crawling
  - `discovery_manager.py`: Discovery orchestration

- **`vpn_merger/cache/`**: Advanced caching system
  - `cache_manager.py`: Multi-tier cache management
  - `predictive_warmer.py`: Cache warming
  - `ml_predictor.py`: ML-based prediction

- **`vpn_merger/ml/`**: Machine learning components
- **`vpn_merger/analytics/`**: Analytics and dashboards
- **`vpn_merger/geo/`**: Geographic optimization

### Models

- **`vpn_merger/models/`**: Data models and structures
- **`vpn_merger/utils/`**: Utility functions and helpers

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/test_core_components.py
pytest tests/test_performance.py

# Run with coverage
pytest --cov=vpn_merger --cov-report=html
```

## 📚 API Documentation

### Basic Usage

```python
from vpn_merger import VPNSubscriptionMerger

# Initialize merger
merger = VPNSubscriptionMerger()

# Run comprehensive merge
results = await merger.run_comprehensive_merge()

# Save results
output_files = merger.save_results()

# Get statistics
stats = merger.get_processing_statistics()
```

### Advanced Usage

```python
# Quick merge for testing
results = await merger.run_quick_merge(max_sources=10)

# Validate sources only
validation_results = await merger.validate_sources_only()

# Get filtered results
high_quality_results = merger.get_results(limit=100, min_quality=0.8)
```

## 🔒 Security

- Input validation and sanitization
- Rate limiting and request throttling
- Threat detection and prevention
- Secure configuration handling
- Audit logging and monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: See the [docs/](docs/) directory
- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Use GitHub Discussions for questions and ideas

## 📊 Status

![License](https://img.shields.io/badge/license-MIT-blue.svg)
