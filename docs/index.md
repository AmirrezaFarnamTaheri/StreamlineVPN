# CleanConfigs SubMerger

A trustworthy, fast, maintainable VPN subscription aggregator that auto-discovers sources, verifies endpoints by real connectivity and QoS, deduplicates and ranks nodes with transparent scoring, and exports client-valid artifacts with enterprise-grade security and observability.

## Highlights

- ML-powered quality scoring with drift detection
- Zero-trust validation pipeline with warm-up FSM (new → probation → trusted → suspended)
- Kubernetes-ready deployment with metrics and tracing
- Multi-tier caching and adaptive processing

## Quick Links

- **Production sources**: `config/sources.unified.yaml`
- **Main runner**: `vpn_merger_main.py`
- **Configuration**: See [CONFIGURATION.md](CONFIGURATION.md)
- **Deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **API Reference**: See [API.md](API.md)
