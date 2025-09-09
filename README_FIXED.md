# StreamlineVPN - Fixed & Enhanced Edition

<div align="center">

![StreamlineVPN Logo](https://img.shields.io/badge/StreamlineVPN-v3.0-purple?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge)

**Enterprise-grade VPN Configuration Management Platform**

[Quick Start](#-quick-start) • [Features](#-features) • [Documentation](#-documentation) • [Support](#-support)

</div>

---

## 🚨 Important: Complete Fix Applied

This version includes comprehensive fixes for all identified issues:
- ✅ **Unified API** - Single coherent API implementation
- ✅ **Frontend Integration** - Properly wired to backend
- ✅ **Async Tests** - All coroutines properly awaited
- ✅ **Configuration Management** - Centralized and robust
- ✅ **Job Management** - Automatic cleanup and monitoring
- ✅ **CORS Fixed** - Single middleware configuration
- ✅ **Environment Configuration** - Comprehensive .env support
- ✅ **Docker Ready** - Production-grade containerization
- ✅ **Modern UI** - Beautiful, responsive web interface

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Run the complete setup script
python streamline_setup.py

# This will:
# 1. Check prerequisites
# 2. Create necessary directories
# 3. Setup configuration
# 4. Install dependencies
# 5. Run tests
# 6. Provide startup instructions
```

### Option 2: Docker Deployment

```bash
# Copy environment template
cp env.example .env

# Edit configuration (important!)
nano .env

# Deploy with Docker Compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Option 3: Manual Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup configuration
cp env.example .env
cp config/sources.yaml.example config/sources.yaml

# 4. Run services
python run_all.py  # Runs all services
# OR individually:
python run_unified.py  # API server on port 8080
python run_web.py      # Web interface on port 8000
```

## 📋 Features

### Core Functionality
- 🔄 **Automated VPN Config Aggregation** - Fetch from multiple sources
- 🎯 **Multi-Format Export** - JSON, Clash, Sing-box, Base64, Raw
- 🚀 **High Performance** - Async processing with connection pooling
- 💾 **Smart Caching** - Redis-based caching for optimal performance
- 🔍 **Configuration Validation** - Automatic validation and deduplication

### Web Interface
- 🎨 **Modern Dashboard** - Beautiful, responsive design
- 📊 **Real-time Statistics** - Live metrics and monitoring
- 🔧 **Control Panel** - Full pipeline control from browser
- 📈 **Performance Graphs** - Visual analytics and trends
- 🔄 **WebSocket Updates** - Real-time status updates

### API Features
- 📚 **RESTful API** - Complete API with OpenAPI documentation
- 🔐 **Authentication** - JWT-based authentication (optional)
- 📡 **WebSocket Support** - Real-time bidirectional communication
- 📊 **Metrics Endpoint** - Prometheus-compatible metrics
- 🎯 **Rate Limiting** - Configurable rate limiting

### DevOps & Deployment
- 🐳 **Docker Support** - Production-ready containers
- ☸️ **Kubernetes Ready** - Helm charts available
- 📈 **Monitoring** - Prometheus + Grafana integration
- 🔄 **CI/CD** - GitHub Actions workflows
- 🔐 **Security** - Environment-based configuration

## 🏗️ Architecture

```
StreamlineVPN/
├── src/streamline_vpn/
│   ├── core/               # Core processing engine
│   │   ├── merger.py       # Main orchestration
│   │   ├── source_manager.py
│   │   └── processing/
│   ├── web/               # Web services
│   │   ├── unified_api.py # Unified API (NEW)
│   │   └── static_server.py
│   ├── models/            # Data models
│   ├── utils/             # Utilities
│   └── security/          # Security features
├── docs/                  # Web interface
│   ├── index.html        # Main dashboard
│   ├── interactive.html  # Control panel
│   └── assets/           # CSS/JS assets
├── config/               # Configuration
│   └── sources.yaml      # Source configuration
├── tests/                # Test suite
├── docker/               # Docker files
└── scripts/              # Deployment scripts
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8080

# Web Configuration
WEB_HOST=0.0.0.0
WEB_PORT=8000

# Processing
VPN_CONCURRENT_LIMIT=50
VPN_TIMEOUT=30

# Cache
VPN_CACHE_ENABLED=true
VPN_REDIS_URL=redis://localhost:6379/0

# See env.example for full list
```

### Source Configuration

Edit `config/sources.yaml`:

```yaml
sources:
  free:
    - "https://example.com/free-configs.txt"
  premium:
    - "https://example.com/premium-configs.txt"
  custom:
    - "https://your-source.com/configs.txt"
```

## 📡 API Usage

### Health Check
```bash
curl http://localhost:8080/health
```

### Run Pipeline
```bash
curl -X POST http://localhost:8080/api/v1/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"formats": ["json", "clash"]}'
```

### Get Statistics
```bash
curl http://localhost:8080/api/v1/statistics
```

### Get Configurations
```bash
curl http://localhost:8080/api/v1/configurations?limit=100
```

### API Documentation
Visit http://localhost:8080/docs for interactive API documentation.

## 🖥️ Web Interface

### Access Points
- **Main Dashboard**: http://localhost:8000
- **Control Panel**: http://localhost:8000/interactive.html
- **API Docs**: http://localhost:8080/docs

### Features
- Real-time statistics dashboard
- Pipeline control with format selection
- Source management
- Configuration browser with search
- Export functionality
- WebSocket-based live updates

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=streamline_vpn --cov-report=html

# Run specific tests
pytest tests/test_unified_api.py -v

# Run fixed async tests
pytest tests/test_fixed_suite.py -v
```

## 🐳 Docker Deployment

### Development
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Production
```bash
# Build images
docker-compose build

# Deploy
docker-compose up -d

# Scale API servers
docker-compose up -d --scale api=3

# View logs
docker-compose logs -f api
```

## 📊 Monitoring

### Prometheus Metrics
Available at http://localhost:9090

### Grafana Dashboards
Available at http://localhost:3000 (admin/admin)

### Health Monitoring
```bash
# Use the monitoring script
./scripts/monitor.sh
```

## 🔒 Security

### Best Practices
1. Always use environment variables for sensitive data
2. Enable HTTPS in production
3. Use strong JWT secret keys
4. Implement rate limiting
5. Regular security updates

### Production Checklist
- [ ] Change default passwords
- [ ] Update JWT secret key
- [ ] Configure firewall rules
- [ ] Enable HTTPS/TLS
- [ ] Setup backup strategy
- [ ] Configure monitoring alerts

## 🚨 Troubleshooting

### Common Issues

#### API Not Responding
```bash
# Check if running
docker-compose ps

# Check logs
docker-compose logs api

# Restart service
docker-compose restart api
```

#### Frontend Can't Connect to API
```bash
# Check CORS settings in .env
ALLOWED_ORIGINS=http://localhost:8000

# Verify API_BASE_URL
API_BASE_URL=http://localhost:8080
```

#### Tests Failing
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run specific test
pytest tests/test_fixed_suite.py::TestUnifiedAPI -v
```

## 📝 CLI Usage

```bash
# Process configurations
python cli.py process --config config/sources.yaml --output output

# Start API server
python cli.py serve --host 0.0.0.0 --port 8080

# Check status
python cli.py status

# Add source
python cli.py add-source https://example.com/configs.txt

# Validate configuration
python cli.py validate

# Cleanup old files
python cli.py cleanup --days 7
```

## 🔄 Updates & Maintenance

### Backup
```bash
./scripts/backup.sh
```

### Update
```bash
git pull
docker-compose build --no-cache
docker-compose up -d
```

### Rollback
```bash
./scripts/rollback.sh backups/streamline_20240115_120000
```

## 📚 Documentation

- [API Documentation](http://localhost:8080/docs)
- [Configuration Guide](docs/configuration/)
- [Deployment Guide](docs/deployment/)
- [Development Guide](docs/development/)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the GPL-3.0 License - see [LICENSE](LICENSE) file.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/streamlinevpn/issues)
- **Documentation**: [docs/](docs/)
- **Email**: support@streamlinevpn.com

## ✨ What's Fixed in This Version

### Backend Fixes
- ✅ Consolidated multiple API implementations into unified_api.py
- ✅ Fixed configuration path resolution
- ✅ Implemented proper job management with cleanup
- ✅ Fixed async test mocks (no more unawaited coroutine warnings)
- ✅ Single CORS middleware configuration
- ✅ Proper environment variable handling

### Frontend Fixes
- ✅ Complete API integration in main.js
- ✅ WebSocket connection for real-time updates
- ✅ Error handling and loading states
- ✅ Search and filter functionality
- ✅ Export capabilities

### Infrastructure
- ✅ Production-ready Docker configuration
- ✅ Comprehensive environment configuration
- ✅ Deployment and rollback scripts
- ✅ Monitoring and backup solutions
- ✅ Complete test suite

## 🎯 Quick Commands Reference

```bash
# Setup
python streamline_setup.py          # Complete setup

# Run Services
python run_all.py                   # All services
python run_unified.py               # API only
python run_web.py                   # Web only

# Docker
docker-compose up -d                # Start all
docker-compose logs -f              # View logs
docker-compose down                 # Stop all

# Management
python cli.py status                # Check status
python cli.py process               # Run pipeline
./scripts/monitor.sh                # Monitor system
./scripts/backup.sh                 # Create backup

# Development
pytest                              # Run tests
python -m pytest --cov              # With coverage
```

---

<div align="center">

**StreamlineVPN v3.0** - Fixed & Enhanced Edition

Built with ❤️ for the VPN community

[Report Bug](https://github.com/streamlinevpn/issues) • [Request Feature](https://github.com/streamlinevpn/issues)

</div>
