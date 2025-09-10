# FAQ

## Getting Started

- What’s the quickest way to try it?
  - See Quick Start: quick-start.md
- Should I use CLI or Python?
  - CLI for simple runs; Python API for integration or custom flows.

## Configuration

- Where is the main config?
  - config/sources.yaml
- Can I override settings with env vars?
  - Yes. Common ones: VPN_OUTPUT_DIR, VPN_CONCURRENT_LIMIT, VPN_TIMEOUT.

## Running & Output

- How do I run with a custom config?
  - CLI: `python cli.py process --config config/sources.yaml --output output`
  - API: `python run_api.py` then `POST /api/v1/pipeline/run`
- What output formats are supported?
  - raw, base64, CSV, JSON, sing-box, clash.
- Where do results go?
  - Default to output/ or custom path via --output or VPN_OUTPUT_DIR.

## Health & Observability

- Health & statistics endpoints?
  - `/health`, `/api/v1/statistics`
- Metrics?
  - Prometheus at /metrics when metrics port is enabled.

## Troubleshooting

- Seeing timeouts or slow runs?
  - Increase VPN_TIMEOUT or lower VPN_CONCURRENT_LIMIT; check network access.
- Outputs look empty?
  - Confirm sources are reachable; check logs and status endpoints.
- Rate limited by external sources?
  - Use retries, backoff, or curated Tier 1 sources.

## Common Terms

- See Glossary: glossary.md
