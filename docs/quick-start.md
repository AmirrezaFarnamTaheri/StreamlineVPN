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
    
    # Web interface
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