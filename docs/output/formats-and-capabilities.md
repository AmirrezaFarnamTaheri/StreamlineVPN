# Output Formats and Capabilities

## Overview

The StreamlineVPN system supports multiple output formats to meet different use cases and client requirements. This page provides an overview of supported formats, their capabilities, and configuration options.

## Supported Output Formats

### 1. Raw Text Format (.txt)

**File**: `configurations.txt`

**Description**: Plain text format containing raw VPN configuration strings, one per line.

**Example**:
```
vless://550e8400-e29b-41d4-a716-446655440000@test-server.example:443?encryption=none&security=reality&sni=www.microsoft.com&type=tcp&flow=xtls-rprx-vision&pbk=public_key&sid=short_id&spx=spider_x&fp=chrome&dest=www.microsoft.com:443#Server1
vmess://eyJ2IjoiMiIsInBzIjoiU2VydmVyMiIsImFkZCI6ImV4YW1wbGUuY29tIiwicG9ydCI6NDQzLCJpZCI6IjU1MGU4NDAwLWUyOWItNDFkNC1hNzE2LTQ0NjY1NTQ0MDAwMCIsImFpZCI6MCwic2N5IjoiYXV0byIsIm5ldCI6InRjcCIsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiJ0bHMifQ==
trojan://password123@test-server.example:443?security=tls&type=tcp&headerType=none#Server3
```

**Use Cases**:
- Direct import into VPN clients
- Manual configuration
- Simple text processing
- Backup and archival

### 2. Base64 Encoded Format (.txt)

**File**: `configurations.base64`

**Description**: Base64 encoded version of the raw text format, commonly used for subscription links.

### 3. CSV Format (.csv)

**File**: `configurations.csv`

**Description**: Comma-separated values format with detailed configuration metadata.

### 4. JSON Format (.json)

**File**: `configurations.json`

**Description**: JSON format with metadata and processing statistics.

### 5. YAML Format (.yaml)

**File**: `configurations.yaml`

**Description**: YAML format with human-readable structure and metadata.

### 6. Sing-box Format (.json)

**File**: `configurations_singbox.json`

**Description**: Sing-box compatible JSON configuration format.

### 7. Clash Format (.yaml)

**File**: `configurations_clash.yaml`

**Description**: Clash compatible YAML configuration format.

## How to Select Output Formats

- CLI:
```bash
python -m streamline_vpn --config config/sources.yaml --output output --format json,clash,singbox
```
- Configuration file (`config/sources.yaml`):
```yaml
output:
  directory: "output"
  formats:
    - json
    - yaml
    - csv
    - base64
    - clash
    - singbox
```
- API: see [API export endpoints](../api/index.md#export-and-download).

## Output Tips

- Control output formats via CLI `--format` or `output.formats` in configuration.
- Use the API’s `/api/v1/configurations` endpoint for filtered and paginated results.

## Validation & Performance

Depending on your workflow, prefer streaming and batching when handling very large outputs. For validation examples and performance tips, see the examples below.

### Basic JSON validation
```python
import json
with open('output/configurations.json', 'r') as f:
    json.load(f)
```

### Memory-friendly output generation (conceptual)
```python
def generate_output_stream(configs):
    for config in configs:
        yield {
            "protocol": config.protocol,
            "host": config.host,
            "port": config.port,
            "quality_score": config.quality_score,
            "config": config.config,
        }
```
