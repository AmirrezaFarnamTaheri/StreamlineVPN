# Web Interface Documentation

StreamlineVPN includes a web interface that surfaces controls, exports, and live statistics.

## Overview

The web interface consists of:

1. **Main Dashboard** – Landing page with quick actions and stats
2. **Control Panel** – Interactive view (`docs/interactive.html`) with sources/jobs
3. **Docs Navigation** – Links to API, configuration, and troubleshooting

## Quick Start

### Starting the Servers

```bash
# Start the API server (respects API_HOST, API_PORT)
python run_api.py

# Start the Web interface (respects WEB_HOST, WEB_PORT)
python run_web.py
```

### Accessing the Interface

- Main Dashboard: `http://localhost:8000` (docs site, see `docs/index.html`)
- API Docs: `http://localhost:8080/docs` or `docs/api/index.html`
- Control Panel: `http://localhost:8000/interactive.html`

## API Endpoints used by the UI

- `GET /api/health` – API health
- `GET /api/v1/statistics` – system statistics
- `POST /api/v1/pipeline/run` – start processing
- `GET /api/v1/pipeline/status/{job_id}` – job status
- `GET /api/v1/sources` – list configured sources

These are consumed via `docs/api-base.js` using `API_BASE_URL`.

## Configuring the Web UI

- `API_BASE_URL`: Base URL the Web UI uses for API calls (default `http://localhost:8080`).
- `WEB_CONNECT_SRC_EXTRA`: Extra CSP `connect-src` entries (space/comma separated).

Example:

```bash
API_BASE_URL=https://api.test-server.example \
WEB_CONNECT_SRC_EXTRA="https://api.test-server.example wss://ws.test-server.example" \
python run_web.py
```

## UX Tips

- Prefer the Control Panel for quick pipeline runs and export actions.
- Use the docs site sidebar (`docs/_data/nav.yml`) to jump between API and configuration guides.
- If the dashboard shows dashes for stats, ensure the API is reachable and `API_BASE_URL` points to it.

## Deployment

See `docs/DEPLOYMENT.md` for production guidance (Docker, Kubernetes, Nginx).

## Troubleshooting

- Stats not loading: check `API_BASE_URL` and browser console network errors.
- CORS blocks: ensure `ALLOWED_ORIGINS` includes your web origin in API settings.
- Mixed content: use HTTPS for both API and Web under the same scheme/host.
 
