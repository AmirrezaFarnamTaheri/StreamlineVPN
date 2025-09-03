# Quick Start Guide

## Prerequisites

- Python 3.10+
- `pip install -r requirements.txt`

## Basic Usage

1. **Configure sources** (optional): Edit `config/sources.unified.yaml` to add/remove sources.

2. **Run the merger**:
   ```bash
   python vpn_merger_main.py
   ```

3. **Check output files** in `output/` directory:
   - `vpn_subscription_base64.txt` - Base64 encoded subscription
   - `vpn_subscription_raw.txt` - Raw subscription data
   - `vpn_singbox.json` - Sing-box format configuration
   - `vpn_detailed.csv` - Detailed configuration data
   - `vpn_report.json` - JSON report with metadata

4. **Serve API and metrics** (optional):
   ```bash
   python vpn_merger_main.py --api --metrics-port 8001
   ```

## Advanced Usage

For more configuration options and advanced features, see the [Configuration Guide](CONFIGURATION.md) and [API Documentation](API.md).
