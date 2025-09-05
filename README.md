# StreamlineVPN

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen.svg)](https://github.com/streamlinevpn/streamline-vpn)

**Enterprise-grade VPN configuration aggregator with advanced features**

StreamlineVPN is a high-performance, production-ready VPN configuration aggregator that processes VPN configurations from multiple sources with advanced filtering, validation, and output formatting. Built for enterprise use with comprehensive monitoring, caching, and quality prediction.

## 🚀 Features

### Core Features
- **Multi-source Aggregation**: Process configurations from 500+ sources
- **Real-time Validation**: Validate accessibility and configuration validity
- **Advanced Deduplication**: Semantic analysis-based deduplication
- **Quality Scoring**: ML-powered quality prediction and ranking
- **Multiple Output Formats**: Raw, base64, CSV, JSON, Clash, SingBox

### Advanced Features
- **Machine Learning**: Quality prediction with feature analysis
- **Geographic Optimization**: Location-based server selection
- **Real-time Discovery**: Automatic source discovery from GitHub, Telegram
- **Multi-tier Caching**: L1 (memory), L2 (Redis), L3 (disk) caching
- **Enterprise Monitoring**: Prometheus metrics, Grafana dashboards
- **High Availability**: Circuit breakers, retry logic, fault tolerance

## 📦 Installation

### From PyPI (Recommended)
```bash
pip install streamline-vpn
```

### From Source
```bash
git clone https://github.com/streamlinevpn/streamline-vpn.git
cd streamline-vpn
pip install -e .
```

### With Optional Features
```bash
# With ML features
pip install streamline-vpn[ml]

# With geographic optimization
pip install streamline-vpn[geo]

# With source discovery
pip install streamline-vpn[discovery]

# All features
pip install streamline-vpn[ml,geo,discovery]
```

## 🎯 Quick Start

### Basic Usage

```python
import asyncio
from streamline_vpn import StreamlineVPNMerger

async def main():
    # Create merger instance
    merger = StreamlineVPNMerger()
    
    # Process all sources
    results = await merger.process_all()

    # Save results
    await merger.save_results("output/")

    print(f"Processed {results['configurations_found']} configurations")

# Run the merger
asyncio.run(main())
```

### Command Line Usage

```bash
# Run with default configuration
streamline-vpn

# Run with custom config
streamline-vpn --config config/sources.yaml

# Run with specific output directory
streamline-vpn --output output/ --format clash
```

### Advanced Usage

```python
from streamline_vpn import StreamlineVPNMerger, create_merger

# Create with custom configuration
merger = create_merger("config/custom_sources.yaml")

# Process with specific options
results = await merger.process_all(
    output_dir="output/",
    formats=["json", "clash", "singbox"]
)

# Get statistics
stats = await merger.get_statistics()
print(f"Success rate: {stats['success_rate']:.1%}")

# Get configurations
configs = await merger.get_configurations()
print(f"Found {len(configs)} high-quality configurations")
```

## 🏗️ Architecture

StreamlineVPN follows a modular, event-driven architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Source        │    │   Configuration │    │   Output        │
│   Manager       │───▶│   Processor     │───▶│   Manager       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Discovery     │    │   Quality       │    │   Cache         │
│   Manager       │    │   Predictor     │    │   Manager       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components

- **SourceManager**: Manages VPN sources with reputation tracking
- **ConfigurationProcessor**: Parses and validates configurations
- **QualityPredictor**: ML-based quality scoring
- **GeographicOptimizer**: Location-based optimization
- **CacheManager**: Multi-tier caching system
- **OutputManager**: Multiple format generation
- **DiscoveryManager**: Automatic source discovery

## 📊 Configuration

### Sources Configuration

```yaml
# config/sources.yaml
sources:
  premium:
    description: "High-quality, reliable sources"
    urls:
      - url: "https://example.com/configs.txt"
        weight: 0.9
        protocols: ["vmess", "vless", "trojan"]
        update: "1h"
        metadata:
          description: "Premium source"
          region: "global"

  reliable:
    description: "Trusted sources with good performance"
    urls:
      - url: "https://example.com/bulk.txt"
        weight: 0.7
        protocols: ["vmess", "vless"]
        update: "4h"
```

### Processing Configuration

```yaml
processing:
  max_concurrent: 50
  timeout: 30
  retry_attempts: 3
  retry_delay: 2

quality:
  min_score: 0.3
  high_quality_threshold: 0.7
  blacklist_threshold: 0.1

output:
  formats: ["raw", "base64", "json", "csv", "clash", "singbox"]
  include_metadata: true
  sort_by_quality: true
```

## 🔧 API Reference

### Core Classes

#### StreamlineVPNMerger
Main orchestration class for VPN configuration processing.

```python
class StreamlineVPNMerger:
    def __init__(self, config_path: str = "config/sources.yaml")
    async def process_all(self, output_dir: str = "output") -> Dict[str, Any]
    async def get_statistics(self) -> Dict[str, Any]
    async def get_configurations(self) -> List[VPNConfiguration]
    def save_results(self, output_dir: str) -> None
```

#### VPNConfiguration
Data model for VPN configurations.

```python
@dataclass
class VPNConfiguration:
    protocol: ProtocolType
    server: str
    port: int
    user_id: Optional[str] = None
    password: Optional[str] = None
    encryption: Optional[str] = None
    quality_score: float = 0.0
    # ... other fields
```

### Utility Functions

```python
# Create merger instance
merger = create_merger("config/sources.yaml")

# Quick merge function
results = await merge_configurations("config/sources.yaml", "output/")
```

## 📈 Monitoring

### Metrics

StreamlineVPN exposes Prometheus-compatible metrics:

- `streamline_requests_total`: Total requests processed
- `streamline_errors_total`: Total errors encountered
- `streamline_request_duration_seconds`: Request duration histogram
- `streamline_configs_processed_total`: Total configurations processed
- `streamline_cache_hit_rate`: Cache hit rate
- `streamline_source_reputation`: Source reputation scores

### Health Checks

```bash
# Health check endpoint
curl http://localhost:8000/health

# Metrics endpoint
curl http://localhost:8000/metrics
```

### Grafana Dashboards

Pre-configured dashboards for:
- System overview and performance
- Application metrics and errors
- Business metrics and quality scores
- Infrastructure health and caching

## 🚀 Deployment

### Docker

```bash
# Build image
docker build -t streamline-vpn .

# Run container
docker run -p 8000:8000 -v $(pwd)/config:/app/config streamline-vpn
```

### Docker Compose

```bash
# Start complete stack
docker-compose -f docker-compose.production.yml up -d
```

### Kubernetes

```bash
# Deploy to Kubernetes
kubectl apply -f kubernetes/
```

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=streamline_vpn --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m performance
```

## 📚 Documentation

- [Installation Guide](docs/installation/)
- [Configuration Reference](docs/configuration/)
- [API Documentation](docs/api/)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/streamlinevpn/streamline-vpn.git
cd streamline-vpn

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/

# Type checking
mypy src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.streamlinevpn.io](https://docs.streamlinevpn.io)
- **Issues**: [GitHub Issues](https://github.com/streamlinevpn/streamline-vpn/issues)
- **Discussions**: [GitHub Discussions](https://github.com/streamlinevpn/streamline-vpn/discussions)
- **Email**: support@streamlinevpn.io

## 🙏 Acknowledgments

- VPN community for source contributions
- Open source projects that made this possible
- Contributors and maintainers

---

**Made with ❤️ by the StreamlineVPN Team**
