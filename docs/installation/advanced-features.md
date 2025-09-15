# Advanced Features Installation Guide

## Overview

This guide explains how to enable optional advanced features in StreamlineVPN: multi-level caching with Redis, optional ML quality prediction, and operational tooling. All instructions reference this repository layout.

## Prerequisites

### System Requirements

- Development: 2GB RAM, 2 CPU cores
- Production: scale resources based on concurrency and load

### Operating System Support

- Linux, macOS, and Windows (WSL2 or native Python)

### Python Version

- Minimum: Python 3.8; Recommended: 3.10+

## Standard Installation

```bash
git clone https://github.com/streamlinevpn/streamlinevpn.git
cd streamlinevpn
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Optional Extras

```bash
# ML (already included in requirements.txt)
pip install scikit-learn joblib

# Redis client (already included)
pip install redis

# Dev/test utilities
pip install -r tests/requirements.txt
```

## Docker

```bash
docker-compose -f docker-compose.production.yml up -d
```

## Advanced Features

### 1. Machine Learning (Optional)

StreamlineVPN provides ML hooks to score and sort configurations.

```bash
export STREAMLINE_VPN_ENV=production
export STREAMLINE_VPN_LOG_LEVEL=INFO
```

> Integrate your model via `ml/quality_predictor.py` and `ml/quality_service.py` as needed.

### 2. Redis Caching (L2)

Multi-level cache: L1 (in-memory), L2 (Redis), L3 (SQLite fallback). L2 is optional.

```bash
# Run Redis
docker run -p 6379:6379 redis:7

# Configure nodes (JSON array)
export STREAMLINE_REDIS__NODES='[{"host":"localhost","port":"6379"}]'
```

### 3. Control Center (Static UI)

```bash
python run_web.py  # WEB_PORT, API_PORT, API_BASE_URL supported

# Extend CSP connect-src (space or comma separated)
export WEB_CONNECT_SRC_EXTRA="https://api.test-server.example wss://ws.test-server.example"
```

### 4. Metrics

Prometheus/Grafana scaffolding is available under `monitoring/`. Point Prometheus to the API metrics endpoint if enabled.

