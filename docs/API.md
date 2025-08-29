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

### Schema (summary)

```graphql
type Outputs {
  raw: String!
  base64: String!
  csv: String!
  report: String!
  singbox: String!
}

type Stats {
  total_configs: Int!
  reachable_configs: Int!
  total_sources: Int!
}

type Query {
  outputs: Outputs!
  stats: Stats!
}
```

### Example Query

```graphql
query {
  outputs { raw base64 singbox }
  stats { total_configs reachable_configs total_sources }
}
```

Include `x-api-token: <token>` header if `API_TOKEN` is set.

## WebSocket API

The server exposes a WebSocket at `/ws` for real-time events when enabled. Messages are JSON objects with a `type` field and `data` payload.

- `run.start`: a merge run has begun
- `run.progress`: progress update; includes counts and stage
- `run.complete`: run finished; includes summary and output paths
- `health.update`: health/metrics snapshot

### Client example (JavaScript)

```javascript
const ws = new WebSocket("wss://<host>/ws?token=<API_TOKEN>");
ws.onmessage = (ev) => {
  const msg = JSON.parse(ev.data);
  switch (msg.type) {
    case "run.start":
    case "run.progress":
    case "run.complete":
    case "health.update":
      console.log(msg);
      break;
  }
};
```

If token auth is enabled, provide `?token=<token>` in the URL or send `{"type":"auth","token":"<token>"}` as the first message.

