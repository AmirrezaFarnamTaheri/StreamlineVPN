---
layout: default
title: Quick Start
description: Get up and running in minutes.
---

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/streamlinevpn/streamlinevpn.git
    cd streamlinevpn
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```bash
    # Command line interface
    python -m streamline_vpn --config config/sources.yaml --output output

    # API server (respects API_HOST, API_PORT)
    python run_api.py

    # Web interface (respects WEB_HOST, WEB_PORT)
    # Optionally set API_BASE_URL if API is not localhost:8080
    # Optionally set WEB_CONNECT_SRC_EXTRA for additional CSP connect-src entries
    python run_web.py

    # Production deployment
    python scripts/deploy_production.py
    ```

## Production Deployment

For production environments, we recommend using Docker or Kubernetes.

### Docker Compose
```bash
docker-compose -f docker-compose.production.yml up -d
```

### Kubernetes
```bash
kubectl apply -f kubernetes/
```

## Environment Tips

- API server
  - `API_HOST` (default `0.0.0.0`), `API_PORT` (default `8080`).
- Web interface
  - `API_BASE_URL` to point the UI at a non-default API (e.g., `https://api.example.com`).
  - `WEB_CONNECT_SRC_EXTRA` to add extra CSP connect-src origins (space or comma separated). Example:
    ```bash
    WEB_CONNECT_SRC_EXTRA="https://api.example.com wss://ws.example.com"
    ```
