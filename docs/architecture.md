# Architecture Overview

The VPN Subscription Merger follows a modular, event-driven architecture designed for high performance and scalability.

## System Architecture

```mermaid
flowchart TD
  A[Sources: YAML + Discovery] -->|URLs| B[Fetcher]
  B --> C[Processor]
  C --> D[Deduplicator]
  D --> E[Scoring]
  E --> F[Threat Analysis (opt)]
  F --> G[Outputs]
  B -.-> M[Event Bus]
  C -.-> M
  D -.-> M
  E -.-> M
  F -.-> M
  M --> H[Metrics]
  M --> I[Dashboard/API]
```

## Key Components

### Core Processing Pipeline

- **SourceManager**: Loads sources from `config/sources.yaml` with tiered organization
- **SourceValidator**: Validates source accessibility and content quality
- **ConfigProcessor**: Handles protocol parsing, deduplication, and quality scoring
- **StreamlineVPNMerger**: Orchestrates the entire processing pipeline

### Features

- **Discovery**: GitHub + Telegram/paste (env-driven), cached via optional memory/Redis
- **Fetcher**: Retries, per-host rate limiting, circuit breaker, compression handling
- **Processor**: Protocol parsing, connection testing, app tests (optional)
- **Threat Analysis**: Feature-gated security engine with SSE + metrics
- **Outputs**: Raw, base64, CSV, sing-box, clash + optional report.json

### Monitoring & Observability

- **Event Bus**: Centralized event handling and metrics collection
- **Metrics**: Prometheus-compatible metrics endpoint
- **Health Checks**: Health monitoring
- **Logging**: Structured logging with correlation IDs

## Data Flow

1. **Source Loading**: Tiered sources loaded from configuration
2. **Validation**: Source accessibility and content validation
3. **Processing**: Configuration parsing and deduplication
4. **Scoring**: Quality assessment and ranking
5. **Output**: Multiple format generation with metadata
6. **Monitoring**: Real-time metrics and health tracking
