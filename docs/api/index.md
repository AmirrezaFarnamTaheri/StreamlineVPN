---
layout: default
title: API Documentation
description: Guide to the StreamlineVPN REST API.
---

The StreamlineVPN API provides a REST interface for running the pipeline, inspecting statistics, listing configurations, and managing sources. All responses are JSON.

## Base URLs

- Local development: `http://localhost:8080`
- In the Web UI, `API_BASE_URL` controls the API location used by the frontend.

## Endpoints

### Health & Statistics

- `GET /health` — API health
- `GET /api/v1/statistics` — current statistics (sources, configs, success rate)

Examples:
```bash
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/statistics
```

### Pipeline

- `POST /api/v1/pipeline/run` — start the pipeline
- `GET /api/v1/pipeline/status/{job_id}` — check job status

Example:
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"output_dir":"output","formats":["json","clash","singbox"]}' \
  http://localhost:8080/api/v1/pipeline/run

# Then poll status
curl http://localhost:8080/api/v1/pipeline/status/<job_id>
```

### Configurations

- `GET /api/v1/configurations?limit=100&offset=0` — list processed configurations

Example:
```bash
curl "http://localhost:8080/api/v1/configurations?limit=50"
```

### Sources

- `GET /api/v1/sources` — list configured sources
- `POST /api/v1/sources` — add a new source (JSON body `{ "url": "..." }`)

Examples:
```bash
curl http://localhost:8080/api/v1/sources
curl -X POST -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/configs.txt"}' \
  http://localhost:8080/api/v1/sources
```

For the interactive API docs, start the server and open `http://localhost:8080/docs`.
