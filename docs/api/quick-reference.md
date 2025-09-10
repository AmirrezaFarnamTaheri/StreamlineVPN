---
layout: default
title: API Quick Reference
description: Concise summary of StreamlineVPN REST API endpoints.
---

# API Quick Reference

Use this page as a compact, copy‑paste friendly summary of the current REST API.

Base URL (local): `http://localhost:8080`

## Health & Statistics

- GET `/health` — API health
- GET `/api/v1/statistics` — totals, success rate, last update

Examples:
```bash
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/statistics
```

## Pipeline

- POST `/api/v1/pipeline/run` — start the pipeline
  - Body (JSON):
    - `output_dir` (string, optional, default `"output"`)
    - `formats` (array[string], e.g. `["json","clash","singbox"]`)
    - `config_path` (string, optional; server applies fallbacks when omitted)

- GET `/api/v1/pipeline/status/{job_id}` — get job status

Example:
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"output_dir":"output","formats":["json","clash","singbox"]}' \
  http://localhost:8080/api/v1/pipeline/run

curl http://localhost:8080/api/v1/pipeline/status/<job_id>
```

## Configurations

- GET `/api/v1/configurations` — list processed configurations
  - Query params:
    - `limit` (int, default 100)
    - `offset` (int, default 0)
    - `protocol` (string, optional; filter)

Example:
```bash
curl "http://localhost:8080/api/v1/configurations?limit=50&offset=0"
```

## Sources

- GET `/api/v1/sources` — list configured sources
- POST `/api/v1/sources` — add a source
  - Body (JSON): `{ "url": "https://example.com/configs.txt" }`

Examples:
```bash
curl http://localhost:8080/api/v1/sources
curl -X POST -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/configs.txt"}' \
  http://localhost:8080/api/v1/sources
```

## WebSocket

- WS `/ws` — periodic server‑pushed updates (e.g., statistics)

Notes:
- The Web UI reads `API_BASE_URL` to locate the API and may enforce CSP `connect-src` rules; see Web Interface docs.

