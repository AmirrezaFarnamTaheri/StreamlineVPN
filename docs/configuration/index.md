---
layout: default
title: Configuration
description: Customize your StreamlineVPN setup.
---

StreamlineVPN can be configured through a YAML file (`config/sources.yaml` by default) and environment variables.

## Quick Reference

| Area | Key | Type | Default | Notes |
|------|-----|------|---------|-------|
| Sources | `sources.<tier>[]` | list(str or obj) | — | Tiered URLs; order matters |
| Processing | `settings.concurrent_limit` | int | 50 | Concurrency; also `STREAMLINE_VPN_CONCURRENT_LIMIT` |
| Processing | `settings.timeout` | int (s) | 30 | Per-request timeout; also `STREAMLINE_VPN_TIMEOUT` |
| Processing | `settings.max_retries` | int | 3 | Retry attempts; also `STREAMLINE_VPN_MAX_RETRIES` |
| Output | `output.directory` | str | `output` | Where artifacts are written |
| Output | `output.formats[]` | list(str) | — | e.g., `json`, `yaml`, `csv`, `base64`, `clash`, `singbox` |
| Cache (opt) | `cache.ttl` | int (s) | 300 | Basic TTL; Redis optional via `STREAMLINE_REDIS__NODES` |

## Example Configuration

```yaml
sources:
  tier_1_premium:
    - url: "https://premium-provider.com/configs"
      weight: 1.0
      protocols: ["vless", "vmess"]
  tier_2_reliable:
    - "https://reliable-source.com/list.txt"

settings:
  concurrent_limit: 50
  timeout: 30
  max_retries: 3

output:
  directory: "output"
  formats: [json, clash, singbox]
```

## Environment Variables

Common overrides:

- `STREAMLINE_VPN_CONFIG` → path to YAML (default `config/sources.yaml`)
- `STREAMLINE_VPN_CONCURRENT_LIMIT` → overrides `settings.concurrent_limit`
- `STREAMLINE_VPN_TIMEOUT` → overrides `settings.timeout`
- `STREAMLINE_VPN_MAX_RETRIES` → overrides `settings.max_retries`
- `STREAMLINE_VPN_OUTPUT_DIR` → overrides `output.directory`
- Redis nodes (optional): `STREAMLINE_REDIS__NODES='[{"host":"localhost","port":"6379"}]'`

See detailed list: [Environment Variables](environment-variables.md)

## Related Guides

- Advanced schema and options: [Advanced Configuration](advanced-configuration.md)
- Output formats and selection: [Formats & Capabilities](../output/formats-and-capabilities.md)
- Troubleshooting config: [Troubleshooting](../troubleshooting.md)
