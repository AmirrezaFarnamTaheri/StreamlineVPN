# Quick Start Guide

This guide will help you get started with the VPN Subscription Merger quickly, regardless of your experience level.

## 🎯 For Beginners

### What is VPN Subscription Merger?

The VPN Subscription Merger is a tool that collects VPN configurations from multiple sources, validates them, and combines them into a single, optimized list. Think of it as a "super aggregator" that finds the best VPN servers from hundreds of sources.

### Installation

1. **Install Python** (3.10 or higher) from [python.org](https://python.org)
2. **Install the tool**:
   ```bash
   pip install vpn-subscription-merger
   ```

### Basic Usage

1. **Run the tool**:
   ```bash
   vpn-merger
   ```

2. **Find your results** in the `output/` folder:
   - `vpn_subscription_raw.txt` - Raw configurations
   - `vpn_subscription_base64.txt` - Base64 encoded
   - `clash.yaml` - Clash configuration
   - `vpn_singbox.json` - Sing-box configuration

### What You Get

- **1000+ VPN servers** from multiple sources
- **Tested and validated** configurations
- **Multiple formats** for different VPN clients
- **Quality-ranked** servers (best ones first)

## 🔧 For Intermediate Users

### Custom Configuration

Create a custom configuration file:

```yaml
# config/my-sources.yaml
metadata:
  name: "My VPN Sources"
  version: "1.0.0"

sources:
  premium:
    metadata:
      type: "validated"
      reliability: "high"
    urls:
      - url: "https://my-source.com/servers.txt"
        weight: 1.0
        protocols: ["vmess", "vless"]
```

Run with custom config:
```bash
vpn-merger --config config/my-sources.yaml
```

### Python API Usage

```python
import asyncio
from vpn_merger import VPNSubscriptionMerger

async def main():
    # Initialize with custom config
    merger = VPNSubscriptionMerger("config/my-sources.yaml")
    
    # Process sources
    results = await merger.run_comprehensive_merge()
    
    # Filter by quality
    high_quality = [r for r in results if r.quality_score > 0.8]
    
    # Save specific format
    merger.save_results("output/", formats=["clash", "singbox"])
    
    print(f"Found {len(high_quality)} high-quality servers")

asyncio.run(main())
```

### Output Formats

- **Raw**: Plain text configurations
- **Base64**: Encoded for subscription URLs
- **Clash**: For Clash clients
- **Sing-box**: For Sing-box clients
- **CSV**: For analysis and filtering
- **JSON**: For programmatic use

## 🚀 For Advanced Users

### Performance Optimization

```python
from vpn_merger import VPNSubscriptionMerger

# High-performance configuration
merger = VPNSubscriptionMerger()
merger.configure(
    max_concurrent=100,  # Increase concurrency
    batch_size=50,       # Larger batches
    enable_ml=True,      # Enable ML quality prediction
    enable_caching=True  # Enable caching
)

# Run with performance monitoring
results = await merger.run_comprehensive_merge(
    max_sources=1000,
    enable_analytics=True
)
```

### Custom Processing Pipeline

```python
from vpn_merger import (
    SourceManager, 
    SourceProcessor, 
    ConfigurationProcessor,
    OutputManager
)

# Build custom pipeline
source_manager = SourceManager("config/sources.yaml")
processor = SourceProcessor()
config_processor = ConfigurationProcessor()
output_manager = OutputManager()

# Custom processing
sources = await source_manager.get_sources()
configs = await processor.process_sources(sources)
processed = config_processor.process_configurations(configs)
output_manager.save_results(processed, "output/")
```

### Machine Learning Integration

```python
from vpn_merger import VPNSubscriptionMerger
from vpn_merger.ml import EnhancedConfigQualityPredictor

# Enable ML quality prediction
merger = VPNSubscriptionMerger()
merger.enable_ml_quality_prediction()

# Train custom model
predictor = EnhancedConfigQualityPredictor()
predictor.train_on_historical_data("data/training/")

# Use custom predictor
merger.set_quality_predictor(predictor)
```

### Web Interface

Start the web interface for real-time monitoring:

```bash
vpn-merger --web --port 8080
```

Access at `http://localhost:8080` for:
- Real-time processing status
- Quality metrics and analytics
- Configuration management
- Performance monitoring

## 🔍 Troubleshooting

### Common Issues

1. **"No sources found"**
   - Check your internet connection
   - Verify source URLs are accessible
   - Check configuration file syntax

2. **"Import error"**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version (3.10+ required)

3. **"Permission denied"**
   - Run with appropriate permissions
   - Check output directory permissions

### Debug Mode

Enable debug logging:
```bash
vpn-merger --debug --verbose
```

### Performance Issues

- Reduce `max_concurrent` if experiencing timeouts
- Increase `timeout` for slow sources
- Enable caching for repeated runs

## 📚 Next Steps

- [Configuration Guide](configuration/) - Detailed configuration options
- [API Reference](api/) - Complete API documentation
- [Performance Tuning](performance/) - Optimization guidelines
- [Contributing Guide](../CONTRIBUTING.md) - How to contribute

## 💡 Tips

1. **Start Simple**: Begin with default settings and gradually customize
2. **Monitor Performance**: Use the web interface to monitor processing
3. **Regular Updates**: Run the merger regularly to get fresh configurations
4. **Quality Over Quantity**: Focus on high-quality sources for better results
5. **Backup Configs**: Keep backups of your custom configurations