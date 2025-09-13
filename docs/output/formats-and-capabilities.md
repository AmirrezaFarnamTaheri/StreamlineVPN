# Output Formats and Capabilities

## Overview

The VPN Subscription Merger supports multiple output formats to meet different use cases and client requirements. This page provides an overview of supported formats, their capabilities, and configuration options.

## Supported Output Formats

### 1. Raw Text Format (.txt)

**File**: `vpn_subscription_raw.txt`

**Description**: Plain text format containing raw VPN configuration strings, one per line.

**Example**:
```
vless://550e8400-e29b-41d4-a716-446655440000@example.com:443?encryption=none&security=reality&sni=www.microsoft.com&type=tcp&flow=xtls-rprx-vision&pbk=public_key&sid=short_id&spx=spider_x&fp=chrome&dest=www.microsoft.com:443#Server1
vmess://eyJ2IjoiMiIsInBzIjoiU2VydmVyMiIsImFkZCI6ImV4YW1wbGUuY29tIiwicG9ydCI6NDQzLCJpZCI6IjU1MGU4NDAwLWUyOWItNDFkNC1hNzE2LTQ0NjY1NTQ0MDAwMCIsImFpZCI6MCwic2N5IjoiYXV0byIsIm5ldCI6InRjcCIsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiJ0bHMifQ==
trojan://password123@example.com:443?security=tls&type=tcp&headerType=none#Server3
```

**Use Cases**:
- Direct import into VPN clients
- Manual configuration
- Simple text processing
- Backup and archival

**Configuration**:
```bash
# Always enabled by default
# No specific configuration needed
```

### 2. Base64 Encoded Format (.txt)

**File**: `vpn_subscription_base64.txt`

**Description**: Base64 encoded version of the raw text format, commonly used for subscription links.

**Example**:
```
dmxlc3M6Ly81NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDBAZXhhbXBsZS5jb206NDQzP2VuY3J5cHRpb249bm9uZSZzZWN1cml0eT1yZWFsaXR5JnNuaT13d3cubWljcm9zb2Z0LmNvbSZ0eXBlPXRjcCZmbG93PXh0bHMtcnByeC12aXNpb24jc2VydmVyMQ==
```

**Use Cases**:
- Subscription links for VPN clients
- URL-safe transmission
- API responses
- Mobile app integration

**Configuration**:
```bash
export VPN_WRITE_BASE64=true
```

### 3. CSV Format (.csv)

**File**: `vpn_detailed.csv`

**Description**: Comma-separated values format with detailed configuration metadata.

**Example**:
```csv
protocol,host,port,quality_score,latency_ms,country,created_at,config
vless,example.com,443,0.95,45.2,US,2023-12-01T10:00:00Z,vless://550e8400-e29b-41d4-a716-446655440000@example.com:443?encryption=none&security=reality&sni=www.microsoft.com&type=tcp&flow=xtls-rprx-vision&pbk=public_key&sid=short_id&spx=spider_x&fp=chrome&dest=www.microsoft.com:443#Server1
vmess,example.com,443,0.88,52.1,US,2023-12-01T10:00:00Z,vmess://eyJ2IjoiMiIsInBzIjoiU2VydmVyMiIsImFkZCI6ImV4YW1wbGUuY29tIiwicG9ydCI6NDQzLCJpZCI6IjU1MGU4NDAwLWUyOWItNDFkNC1hNzE2LTQ0NjY1NTQ0MDAwMCIsImFpZCI6MCwic2N5IjoiYXV0byIsIm5ldCI6InRjcCIsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiJ0bHMifQ==
trojan,example.com,443,0.92,38.7,US,2023-12-01T10:00:00Z,trojan://password123@example.com:443?security=tls&type=tcp&headerType=none#Server3
```

**Columns**:
- `protocol`: VPN protocol (vless, vmess, trojan, shadowsocks, etc.)
- `host`: Server hostname or IP address
- `port`: Server port number
- `quality_score`: Quality score (0.0-1.0)
- `latency_ms`: Network latency in milliseconds
- `country`: Server country code
- `created_at`: Timestamp when configuration was processed
- `config`: Full configuration string

**Use Cases**:
- Data analysis and reporting
- Excel/Google Sheets import
- Database import
- Quality assessment
- Geographic analysis

**Configuration**:
```bash
export VPN_WRITE_CSV=true
```

### 4. JSON Format (.json)

**File**: `vpn_report.json`

**Description**: JSON format with metadata and processing statistics.

**Example**:
```json
{
  "metadata": {
    "generated_at": "2023-12-01T10:00:00Z",
    "total_configs": 150,
    "valid_configs": 142,
    "processing_time": 45.2,
    "sources_processed": 25,
    "quality_threshold": 0.7
  },
  "statistics": {
    "protocols": {
      "vless": 45,
      "vmess": 38,
      "trojan": 32,
      "shadowsocks": 27
    },
    "countries": {
      "US": 35,
      "UK": 28,
      "DE": 22,
      "JP": 18,
      "SG": 15,
      "CA": 12,
      "AU": 12
    },
    "quality_distribution": {
      "0.9-1.0": 25,
      "0.8-0.9": 45,
      "0.7-0.8": 38,
      "0.6-0.7": 22,
      "0.5-0.6": 12
    }
  },
  "configurations": [
    {
      "id": "config_001",
      "protocol": "vless",
      "host": "example.com",
      "port": 443,
      "quality_score": 0.95,
      "latency_ms": 45.2,
      "country": "US",
      "config": "vless://550e8400-e29b-41d4-a716-446655440000@example.com:443?encryption=none&security=reality&sni=www.microsoft.com&type=tcp&flow=xtls-rprx-vision&pbk=public_key&sid=short_id&spx=spider_x&fp=chrome&dest=www.microsoft.com:443#Server1",
      "created_at": "2023-12-01T10:00:00Z"
    }
  ]
}
```

**Use Cases**:
- API responses
- Web application integration
- Data processing pipelines
- Analytics and reporting
- Machine learning training data

**Configuration**:
```bash
export VPN_WRITE_JSON=true
```

### 5. YAML Format (.yaml)

**File**: `vpn_report.yaml`

**Description**: YAML format with human-readable structure and metadata.

**Example**:
```yaml
metadata:
  generated_at: "2023-12-01T10:00:00Z"
  total_configs: 150
  valid_configs: 142
  processing_time: 45.2
  sources_processed: 25
  quality_threshold: 0.7

statistics:
  protocols:
    vless: 45
    vmess: 38
    trojan: 32
    shadowsocks: 27
  
  countries:
    US: 35
    UK: 28
    DE: 22
    JP: 18
    SG: 15
    CA: 12
    AU: 12
  
  quality_distribution:
    "0.9-1.0": 25
    "0.8-0.9": 45
    "0.7-0.8": 38
    "0.6-0.7": 22
    "0.5-0.6": 12

configurations:
  - id: "config_001"
    protocol: "vless"
    host: "example.com"
    port: 443
    quality_score: 0.95
    latency_ms: 45.2
    country: "US"
    config: "vless://550e8400-e29b-41d4-a716-446655440000@example.com:443?encryption=none&security=reality&sni=www.microsoft.com&type=tcp&flow=xtls-rprx-vision&pbk=public_key&sid=short_id&spx=spider_x&fp=chrome&dest=www.microsoft.com:443#Server1"
    created_at: "2023-12-01T10:00:00Z"
```

**Use Cases**:
- Configuration management
- Human-readable reports
- DevOps integration
- Documentation
- Manual review and editing

**Configuration**:
```bash
export VPN_WRITE_YAML=true
```

### 6. Sing-box Format (.json)

**File**: `vpn_singbox.json`

**Description**: Sing-box compatible JSON configuration format.

**Example**:
```json
{
  "outbounds": [
    {
      "type": "vless",
      "tag": "server1",
      "server": "example.com",
      "server_port": 443,
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "flow": "xtls-rprx-vision",
      "encryption": "none",
      "network": "tcp",
      "tls": {
        "enabled": true,
        "server_name": "www.microsoft.com",
        "reality": {
          "enabled": true,
          "public_key": "public_key",
          "short_id": "short_id",
          "spider_x": "spider_x"
        }
      }
    },
    {
      "type": "vmess",
      "tag": "server2",
      "server": "example.com",
      "server_port": 443,
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "alter_id": 0,
      "cipher": "auto",
      "network": "tcp",
      "tls": {
        "enabled": true
      }
    }
  ],
  "routing": {
    "rules": [
      {
        "type": "field",
        "outbound": "direct",
        "domain": ["geosite:cn"]
      }
    ]
  }
}
```

**Use Cases**:
- Sing-box client configuration
- Multi-protocol support
- Custom proxy chains

**Configuration**:
```bash
export VPN_WRITE_SINGBOX=true
```

### 7. Clash Format (.yaml)

**File**: `clash.yaml`

**Description**: Clash compatible YAML configuration format.

**Example**:
```yaml
port: 7890
socks-port: 7891
allow-lan: false
mode: rule
log-level: info
external-controller: 127.0.0.1:9090

proxies:
  - name: "server1"
    type: vless
    server: example.com
    port: 443
    uuid: 550e8400-e29b-41d4-a716-446655440000
    flow: xtls-rprx-vision
    encryption: none
    network: tcp
    tls: true
    servername: www.microsoft.com
    reality-opts:
      public-key: public_key
      short-id: short_id
      spider-x: spider_x

  - name: "server2"
    type: vmess
    server: example.com
    port: 443
    uuid: 550e8400-e29b-41d4-a716-446655440000
    alterId: 0
    cipher: auto
    network: tcp
    tls: true

proxy-groups:
  - name: "auto"
    type: url-test
    proxies:
      - server1
      - server2
    url: "http://www.gstatic.com/generate_204"
    interval: 300

rules:
  - DOMAIN-SUFFIX,local,direct
  - IP-CIDR,127.0.0.0/8,direct
  - IP-CIDR,172.16.0.0/12,direct
  - IP-CIDR,192.168.0.0/16,direct
  - IP-CIDR,10.0.0.0/8,direct
  - GEOIP,CN,direct
  - MATCH,auto
```

**Use Cases**:
- Clash client configuration
- Rule-based routing
- Load balancing
- Geographic routing

**Configuration**:
```bash
export VPN_WRITE_CLASH=true
```

## Output Configuration

### Environment Variables

```bash
# Output directory
export VPN_OUTPUT_DIR=output

# Enable/disable specific formats
export VPN_WRITE_BASE64=true
export VPN_WRITE_CSV=true
export VPN_WRITE_JSON=true
export VPN_WRITE_YAML=true
export VPN_WRITE_SINGBOX=true
export VPN_WRITE_CLASH=true

# Output customization
export VPN_INCLUDE_METADATA=true
export VPN_QUALITY_THRESHOLD=0.7
export VPN_MAX_CONFIGS=1000
```

### Configuration File

```yaml
# config/output.yaml
output:
  directory: "output"
  formats:
    raw: true
    base64: true
    csv: true
    json: true
    yaml: true
    singbox: true
    clash: true
  
  options:
    include_metadata: true
    quality_threshold: 0.7
    max_configs: 1000
    sort_by: "quality_score"
    sort_order: "desc"
  
  customizations:
    csv_delimiter: ","
    json_indent: 2
    yaml_indent: 2
```

## Output Tips

- Control output formats with environment variables shown above.
- Use the API’s `/api/v1/configurations` endpoint for filtered and paginated results.

## Output Validation

### Format Validation

```python
# Validate output format
def validate_output_format(file_path: str, format_type: str) -> bool:
    """Validate output file format."""
    
    if format_type == "json":
        try:
            with open(file_path, 'r') as f:
                json.load(f)
            return True
        except json.JSONDecodeError:
            return False
    
    elif format_type == "yaml":
        try:
            with open(file_path, 'r') as f:
                yaml.safe_load(f)
            return True
        except yaml.YAMLError:
            return False
    
    elif format_type == "csv":
        try:
            with open(file_path, 'r') as f:
                csv.reader(f)
            return True
        except csv.Error:
            return False
    
    return False
```

### Content Validation

```python
# Validate output content
def validate_output_content(file_path: str) -> dict:
    """Validate output file content."""
    
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    # Check file exists and is readable
    if not os.path.exists(file_path):
        validation_result["valid"] = False
        validation_result["errors"].append("File does not exist")
        return validation_result
    
    # Check file size
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        validation_result["warnings"].append("File is empty")
    
    # Check file permissions
    if not os.access(file_path, os.R_OK):
        validation_result["valid"] = False
        validation_result["errors"].append("File is not readable")
    
    return validation_result
```

## Performance Considerations

### Large Dataset Handling

```python
# For large datasets, use streaming
async def process_large_dataset(configs):
    """Process large dataset with streaming output."""
    
    batch_size = 1000
    output_files = {}
    
    for i in range(0, len(configs), batch_size):
        batch = configs[i:i + batch_size]
        
        # Process batch
        batch_results = await process_batch(batch)
        
        # Append to output files
        for format_type, content in batch_results.items():
            if format_type not in output_files:
                output_files[format_type] = []
            output_files[format_type].append(content)
    
    return output_files
```

### Memory Optimization

```python
# Use generators for memory efficiency
def generate_output_stream(configs):
    """Generate output stream for memory efficiency."""
    
    for config in configs:
        yield {
            "protocol": config.protocol,
            "host": config.host,
            "port": config.port,
            "quality_score": config.quality_score,
            "config": config.config
        }
```

## Integration Examples

### Web API Integration

```python
# REST API endpoint
@app.get("/api/v1/configs")
async def get_configs(format: str = "json"):
    """Get configurations in specified format."""
    
    merger = StreamlineVPNMerger()
    results = await merger.run_quick_merge()
    
    formatter = get_formatter(format)
    return formatter.format(results)
```

### Database Integration

```python
# Save to database
async def save_to_database(configs, db_connection):
    """Save configurations to database."""
    
    for config in configs:
        await db_connection.execute(
            "INSERT INTO vpn_configs (protocol, host, port, quality_score, config) VALUES (?, ?, ?, ?, ?)",
            (config.protocol, config.host, config.port, config.quality_score, config.config)
        )
```

### File System Integration

```python
# Save to multiple locations
async def save_to_multiple_locations(configs):
    """Save configurations to multiple locations."""
    
    locations = [
        "output/",
        "/var/www/html/configs/",
        "s3://bucket/configs/",
        "ftp://server/configs/"
    ]
    
    for location in locations:
        await save_to_location(configs, location)
```

This page outlines output formats and capabilities of the VPN Subscription Merger system and how to configure and use them.
