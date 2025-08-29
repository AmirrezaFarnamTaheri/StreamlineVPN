# API Overview

All endpoints are exposed under `/api/v1`. If `API_TOKEN` is set in the environment, include `x-api-token: <token>` or `?token=<token>`.

## Endpoints

- `GET /api/v1/health`
  - Returns `{"status":"ok"}` for readiness checks.

- `GET /api/v1/limits`
  - Returns current rate‑limit state for the requesting IP.

- `GET /api/v1/sub/raw`
  - Plain text, one config per line. Token‑gated when `API_TOKEN` is set.

- `GET /api/v1/sub/base64`
  - Base64 subscription of the merged output. Token‑gated when `API_TOKEN` is set.

- `GET /api/v1/sub/singbox`
  - JSON outbounds for sing‑box. Token‑gated when `API_TOKEN` is set.

- `GET /api/v1/sub/report`
  - JSON report of the latest run, including counts and file paths. Token‑gated when `API_TOKEN` is set.

- `GET /api/v1/stats/latest`
  - Compact stats derived from the last report + quarantine DB count.

## GraphQL (optional)

If `strawberry-graphql` is installed, a GraphQL endpoint is mounted at `/graphql` with the following queries:

- `outputs`: returns paths to output files (raw/base64/CSV/report/singbox)
- `stats`: returns `total_configs`, `reachable_configs`, `total_sources`

