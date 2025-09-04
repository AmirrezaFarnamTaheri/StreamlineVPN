# CleanConfigs SubMerger

A trustworthy, fast, maintainable VPN subscription aggregator that auto-discovers sources, verifies endpoints by real connectivity and QoS, deduplicates and ranks nodes with transparent scoring, and exports client‑valid artifacts with enterprise‑grade security and observability.

## Highlights

- ML‑powered quality scoring with drift detection
- Zero‑trust validation pipeline with warm‑up FSM (new → probation → trusted → suspended)
- Kubernetes‑ready deployment with metrics and tracing
- Multi‑tier caching and adaptive processing

## Quick Links

- Production sources: `config/sources.unified.yaml`
- Main runner: `vpn_merger_main.py`
- Configuration: See [configuration/](configuration/)
- Deployment: See [deployment.md](deployment.md)
- API reference: See [api/](api/)

## Choose Your Path

- New to SubMerger: Start with the [Quick Start](quick-start.md)
- Power users: Tune options in [Configuration](configuration/)
- Operators/SREs: See [Deployment](deployment.md) and [Troubleshooting](troubleshooting.md)
- Developers: Check the [Python SDK](sdk-python.md), [Architecture](architecture.md), and [API](api/)
- Performance enthusiasts: Visit [Performance Tuning](performance/tuning-guide.md)

## Helpful Scripts

- Smoke run integrated server (start/stop on ephemeral port):
  - `PYTHONPATH=src python scripts/smoke_integrated_server.py`

- Smoke core endpoints from the integrated server (health/status previews):
  - `PYTHONPATH=src python scripts/smoke_endpoints.py`

- Run non‑network tests quickly (skips network‑marked tests via env):
  - `PYTHONPATH=src python scripts/run_tests_no_network.py`

## Dependency Report (ASCII Only)

Environment/dependency status prints clean ASCII with YES/NO statuses.

Run report:

```bash
python -c "from vpn_merger.utils.dependencies import print_dependency_report; print_dependency_report()"
```
