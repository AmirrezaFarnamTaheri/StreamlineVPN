# VPN Subscription Merger

A high‑performance, production‑ready VPN subscription merger that aggregates and processes VPN configurations from multiple sources with advanced filtering, validation, and output formatting.

## Quick Start

### Installation

```bash
# Install from PyPI
pip install vpn-subscription-merger

# Or install from source
git clone https://github.com/vpn-merger-team/vpn-subscription-merger.git
cd vpn-subscription-merger
pip install -e .
```

### Basic Usage

```python
import asyncio
from vpn_merger import VPNSubscriptionMerger

async def main():
    # Initialize the merger
    merger = VPNSubscriptionMerger()
    
    # Run comprehensive merge
    results = await merger.run_comprehensive_merge()
    
    # Save results
    merger.save_results("output/")
    
    print(f"Processed {len(results)} configurations")

# Run the merger
asyncio.run(main())
```

### Command Line Usage

```bash
# Run with default configuration
vpn-merger

# Run with custom config
vpn-merger --config config/sources.unified.yaml

# Run with specific output directory
vpn-merger --output output/ --format clash
```

## Features

### Core Features
- Multi‑source aggregation from 500+ sources
- Real‑time validation of accessibility and configuration validity
- Advanced deduplication using semantic analysis
- Quality scoring by performance and reliability
- Multiple output formats: raw, base64, CSV, JSON, sing‑box, and clash

### Advanced Features
- Machine learning‑based quality prediction
- Geographic optimization for location‑based selection
- Real‑time source discovery (GitHub, Telegram)
- Web analytics dashboard
- Multi‑tier caching for performance

## Architecture

The VPN Subscription Merger follows a modular, event‑driven architecture.

### Key Components

- SourceManager: Manages VPN subscription sources with tiered reliability
- SourceProcessor: Processes and validates configurations
- ConfigurationProcessor: Handles protocol parsing and deduplication
- OutputManager: Generates multiple output formats
- QualityPredictor: ML‑based quality assessment
- AnalyticsDashboard: Real‑time monitoring and analytics

## Documentation

### Choose Your Path

- New to SubMerger: Start with the [Quick Start Guide](docs/quick-start.md)
- Power users: Configure deeply in [Configuration](docs/configuration/)
- Operators/SREs: Deploy via the [Deployment Guide](docs/deployment.md) and see [Troubleshooting](docs/troubleshooting.md)
- Developers: Use the [Python SDK](docs/sdk-python.md), study the [Architecture](docs/architecture.md), and browse the [API Reference](docs/api/)

### User Guides
- Quick Start: [docs/quick-start.md](docs/quick-start.md)
- Configuration Guide: [docs/configuration/](docs/configuration/)
- Output Formats: [docs/output/](docs/output/)

### Developer Documentation
- API Reference: [docs/api/](docs/api/)
- Architecture Overview: [docs/architecture.md](docs/architecture.md)
- Contributing Guide: [CONTRIBUTING.md](CONTRIBUTING.md)

### Advanced Topics
- Performance Tuning: [docs/performance/](docs/performance/)
- Security Policies: [SECURITY.md](SECURITY.md)
- Troubleshooting: [docs/troubleshooting.md](docs/troubleshooting.md)

## Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/                    # Unit tests
pytest tests/integration/             # Integration tests
pytest tests/performance/             # Performance tests

# Run with coverage
pytest --cov=vpn_merger --cov-report=html
```

## Performance

- Processing speed: 1000+ configurations per second
- Memory usage: Optimized for large‑scale processing
- Concurrency: Async/await for maximum efficiency
- Caching: Multi‑tier caching reduces redundant operations

## Configuration

The merger uses YAML configuration files to define sources and processing options:

```yaml
metadata:
  name: "VPN Sources"
  version: "2.0.0"
  description: "Comprehensive VPN source collection"

sources:
  tier1:
    metadata:
      type: "validated"
      reliability: "high"
    urls:
      - url: "https://example.com/sources.txt"
        weight: 1.0
        protocols: ["vmess", "vless"]
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/vpn-merger-team/vpn-subscription-merger.git
cd vpn-subscription-merger

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black src/ tests/
isort src/ tests/
ruff check src/ tests/
```

## License

This project is licensed under the GPL-3.0-or-later License — see the [LICENSE](LICENSE) file for details.

## Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/vpn-merger-team/vpn-subscription-merger/issues)
- Discussions: [GitHub Discussions](https://github.com/vpn-merger-team/vpn-subscription-merger/discussions)

## Acknowledgments

- VPN community for providing source configurations
- Open source contributors and maintainers
- Security researchers for vulnerability reports

---

Note: This tool is for educational and research purposes. Please ensure compliance with local laws and regulations when using VPN services.

