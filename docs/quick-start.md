---
layout: default
title: Quick Start Guide
description: Get StreamlineVPN running in 5 minutes
---

# Quick Start Guide

## Prerequisites

- Python 3.8 or higher
- Redis (optional, for caching)
- 2GB RAM minimum
- Internet connection for source fetching

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/cleanconfigs-submerger-.git
cd CleanConfigs-SubMerger-
```

### 2. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
# On Unix/macOS:
source venv/bin/activate
# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 3. Configure Sources

The default configuration includes curated sources. Review and customize:

```bash
# Edit source configuration
nano config/sources.yaml
```

Example configuration structure:
```yaml
sources:
  tier_1_premium:
    - url: "https://premium-provider.com/configs"
      weight: 1.0
      protocols: ["vless", "vmess"]
  
  tier_2_reliable:
    - url: "https://reliable-source.com/list.txt"
      weight: 0.8
```

## Running StreamlineVPN

### Option 1: Command Line Interface

```bash
# Basic run with defaults
python -m streamline_vpn

# Custom configuration
python -m streamline_vpn --config config/sources.yaml --output output --format json,clash,singbox
```

### Option 2: Web Interface

```bash
# Start API server
python run_api.py &

# Start web interface
python run_web.py

# Open browser to http://localhost:8000
```

### Option 3: Docker

```bash
# Build and run
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## First Run Checklist

✅ **Step 1**: Verify installation
```bash
python -c "import streamline_vpn; print('Installation successful!')"
```

✅ **Step 2**: Test source connectivity
```bash
curl -I https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt
```

✅ **Step 3**: Run initial processing
```bash
python -m streamline_vpn --config config/sources.yaml --output output
```

✅ **Step 4**: Check output files
```bash
ls -la output/
# Should see: configurations.json, configurations_clash.yaml, etc.
```

## Common Issues & Solutions

### Issue: "No module named streamline_vpn"
**Solution**: Ensure you're in the project directory and dependencies are installed:
```bash
pip install -e .
```

### Issue: Redis connection error
**Solution**: Redis is optional. Disable caching:
```bash
export STREAMLINE_REDIS__NODES='[]'
```

### Issue: Timeout errors
**Solution**: Increase timeout and reduce concurrency:
```bash
export STREAMLINE_VPN_TIMEOUT=60
export STREAMLINE_VPN_CONCURRENT_LIMIT=10
```

## Next Steps

1. **Explore the Web Interface**: Open `http://localhost:8000/interactive.html`
2. **Configure automation**: Set up cron job or systemd service
3. **Review API docs**: Visit `http://localhost:8080/docs` or `docs/api/index.html`
4. **Customize sources**: Add your own VPN configuration sources

## Support

- 📖 [Full Documentation](index.html)
- 🐛 Report Issues: open a GitHub issue on the repository
- 💬 Community: join your team's preferred chat channel

## Shortcuts

- Configuration Reference: `configuration/index.html`
- API Error Codes: `api/error-codes.md`
- Troubleshooting: `troubleshooting.html`