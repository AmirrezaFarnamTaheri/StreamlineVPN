# Deployment Guide (Distributed + Monitoring)

## Local Run

```
pip install -r requirements.txt
python vpn_merger.py --concurrent-limit 50 --max-retries 3
```

## Distributed Fetching with Celery + Redis

1. Install Celery and a Redis broker.
2. Set `CELERY_BROKER_URL` (and `CELERY_RESULT_BACKEND` if desired).
3. Run a Celery worker:

```
celery -A vpn_merger.distributed.tasks worker --loglevel=info -Q celery -n worker@%h
```

4. Start the merger in distributed mode:

```
CELERY_BROKER_URL=redis://localhost:6379/0 \
python vpn_merger.py --distributed --redis-url redis://localhost:6379/0 --workers 8
```

The coordinator will partition sources and queue tasks. The runner waits for results with a timeout and falls back to local fetching if aggregation times out.

## Monitoring (Prometheus + Grafana)

- Metrics endpoint is exposed via `prometheus_client` (default port 8001). Scrape it with Prometheus and build dashboards in Grafana.
- Dashboard/API (FastAPI) defaults to port 8000. Set `API_TOKEN` to protect endpoints.

Example scrape_config:

```
- job_name: 'vpn_merger'
  static_configs:
  - targets: ['localhost:8001']
```

## Security Notes

- Set `API_TOKEN` in production.
- Respect upstream providers’ ToS and apply per‑host rate‑limits.
- Avoid running as root; prefer virtualenvs and non‑privileged users.

