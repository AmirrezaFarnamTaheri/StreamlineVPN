# Environment Variables Reference

## Overview

StreamlineVPN supports environment-based configuration for deployment without modifying files. This page lists commonly used variables.

## Core Configuration

### STREAMLINE_VPN_CONFIG

- Description: Path to the main sources configuration file
- Type: String (file path)
- Default: `config/sources.yaml`
- Example:
```bash
export STREAMLINE_VPN_CONFIG=/etc/streamline/sources.yaml
```

### STREAMLINE_VPN_CONCURRENT_LIMIT

- Description: Maximum number of concurrent operations
- Type: Integer
- Default: `50`
- Example:
```bash
export STREAMLINE_VPN_CONCURRENT_LIMIT=100
```

### STREAMLINE_VPN_TIMEOUT

- Description: Request timeout in seconds
- Type: Integer
- Default: `30`
- Example:
```bash
export STREAMLINE_VPN_TIMEOUT=60
```

### STREAMLINE_VPN_MAX_RETRIES

- Description: Retry attempts for failed requests
- Type: Integer
- Default: `3`
- Example:
```bash
export STREAMLINE_VPN_MAX_RETRIES=5
```

## Output Configuration

### STREAMLINE_VPN_OUTPUT_DIR

- Description: Directory for output files
- Type: String (directory path)
- Default: `output`
- Example:
```bash
export STREAMLINE_VPN_OUTPUT_DIR=/var/lib/streamline/output
```

- To select formats, prefer CLI `--format` or config `output.formats`.

## Logging

### STREAMLINE_VPN_LOG_LEVEL

- Description: Logging level
- Type: Enum `DEBUG|INFO|WARNING|ERROR|CRITICAL`
- Default: `INFO`
- Example:
```bash
export STREAMLINE_VPN_LOG_LEVEL=DEBUG
```

## Caching (optional)

### STREAMLINE_REDIS__NODES

- Description: JSON list of Redis nodes for L2 cache
- Type: JSON string
- Default: unset (L1+L3 only)
- Example:
```bash
export STREAMLINE_REDIS__NODES='[{"host":"localhost","port":"6379"}]'
```

## Web UI

### API_BASE_URL

- Description: Base URL the Web UI uses for API calls
- Default: `http://localhost:8080`
- Example:
```bash
export API_BASE_URL="https://api.example"
```

### WEB_CONNECT_SRC_EXTRA

- Description: Extra CSP `connect-src` entries (space/comma separated)
- Example:
```bash
export WEB_CONNECT_SRC_EXTRA="https://api.example wss://ws.example"
```
