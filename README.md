# StreamlineVPN – VPN Configuration Aggregator

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](./src/streamline_vpn/__init__.py)
[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)

StreamlineVPN aggregates, validates, and exports VPN configurations from multiple sources. It provides a FastAPI backend, a lightweight static control center, and a multi-level cache to keep things fast and reliable.

## Features

- Protocols: VLESS, VMess, Shadowsocks (incl. 2022), ShadowsocksR, Trojan
- Processing: async fetching, validation, deduplication, export (JSON/CSV/Base64/Clash/Sing-Box)
- Caching: L1 in-memory, L2 Redis, L3 SQLite fallback (new)
- Web API: unified FastAPI app with background pipeline endpoints
- Static Control Center: serves assets and proxies API; shows health and stats
- Scheduler: APScheduler job to periodically run the pipeline

## Requirements

- Python 3.8+
- Redis 6.0+ (optional, for L2 cache)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### One-off Processing

To run a single processing job from the command line:
```bash
python -m streamline_vpn --config config/sources.yaml --output output
```

### API Server

The unified server includes the FastAPI backend and serves the static control panel.

**For Development:**
```bash
# Start the unified server (API + static assets)
python run_unified.py

# Or run uvicorn directly for more options
uvicorn streamline_vpn.web.unified_api:create_unified_app --host 0.0.0.0 --port 8080 --reload
```

## Configuration

Environment variables (JSON arrays preferred; comma lists accepted):

```bash
# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8080"]
ALLOWED_METHODS=["GET","POST","PUT","DELETE","OPTIONS"]
ALLOWED_HEADERS=["Content-Type","Authorization"]
ALLOW_CREDENTIALS=false

# Optional Redis cluster nodes
STREAMLINE_REDIS__NODES='[{"host":"localhost","port":"6379"}]'

# Optional jobs persistence override
# JOBS_DIR=data
# JOBS_FILE=data/jobs.json
```

Key config files:

- `config/sources.yaml` – source lists (tiers and URLs)
- `output/` – generated artifacts (JSON/Clash/Sing-Box etc.)

## Testing & Coverage

```bash
# Run tests
pytest -q

# Coverage (terminal summary)
pytest -q --cov=src --cov-report=term-missing

# Coverage XML for CI/gates
pytest -q --cov=src --cov-report=xml:coverage.xml
python scripts/coverage_gate.py coverage.xml
```

CI runs the coverage gate and will fail on regressions.

### Windows Notes

- Use PowerShell activation when using venv: `venv\Scripts\Activate.ps1`
- If execution policy prevents activation: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

## Docker (Development)

Two workflows are available:

- Standard:

```bash
docker-compose up -d
```

- With hot reload and live-mounted code:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

The dev override runs Uvicorn with `--reload` and mounts `src/`, `config/`, and `docs/` for quick iteration.

## Architecture (high level)

```
src/streamline_vpn/
  core/           # processing engine, parsers, cache
  web/            # FastAPI app + static server
  jobs/           # background jobs & cleanup
  models/         # typed configuration models
  utils/          # logging, helpers
  scheduler.py    # APScheduler glue
```

## Notes

- L3 cache uses a local SQLite DB (`vpn_configs.db`). It is safe to run without Redis; the system falls back to L1+L3.
- Windows: tests set a selector loop policy to avoid noisy SSL teardown logs.

## License

GPL-3.0 – see [LICENSE](./LICENSE).

## API Documentation

The StreamlineVPN API provides programmatic access to VPN configuration management:

- **GET /api/v1/sources** - List configured sources
- **GET /api/v1/configurations** - Retrieve processed configurations
- **POST /api/v1/pipeline/run** - Trigger processing pipeline
- **GET /api/statistics** - Get real-time statistics
- **GET /api/health** - Health check endpoint

See the docs site for details: `docs/api/index.html`.

## Security

StreamlineVPN implements several security measures:

- Input validation for all configuration sources
- Rate limiting on API endpoints
- Secure credential handling via environment variables
- CORS protection for web interfaces

## Performance

- Multi-level caching (Redis L2, SQLite L3)
- Async processing with configurable concurrency
- Background job scheduling with APScheduler
- Optimized deduplication algorithms

## Troubleshooting

Common issues and solutions:

1. **Redis Connection Issues**: Ensure Redis is running or disable L2 cache
2. **Source Timeout**: Increase timeout values in config
3. **Memory Usage**: Reduce max_concurrent setting
4. **API Errors**: Check logs in `logs/` directory

For detailed troubleshooting, see `docs/troubleshooting.html`.
