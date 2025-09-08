---
layout: default
title: Configuration
description: Customize your StreamlineVPN setup.
---

StreamlineVPN can be configured through a YAML file (`config/sources.yaml` by default) and environment variables.

## Configuration File

The main configuration is done in a YAML file. Here is an example with all the available options:

```yaml
sources:
  tier_1_premium:
    - "https://example1.com"
    - "https://example2.com"
  
  tier_2_reliable:
    - "https://example3.com"
    - "https://example4.com"

settings:
  concurrent_limit: 50
  timeout: 30
  max_retries: 3

output:
  directory: "output"
  formats:
    - raw
    - base64
    - clash
    - singbox
```

### `sources`
A dictionary of tiers, where each tier is a list of VPN source URLs. The tiers are processed in the order they are defined.

### `settings`
- `concurrent_limit`: The maximum number of concurrent requests to fetch sources.
- `timeout`: The timeout in seconds for each request.
- `max_retries`: The maximum number of retries for a failed request.

### `output`
- `directory`: The directory where the output files will be saved.
- `formats`: A list of output formats to generate.

## Environment Variables

You can also use environment variables to override the settings in the configuration file.

- `STREAMLINE_VPN_CONFIG`: Path to the configuration file.
- `STREAMLINE_VPN_CONCURRENT_LIMIT`: Overrides `settings.concurrent_limit`.
- `STREAMLINE_VPN_TIMEOUT`: Overrides `settings.timeout`.
- `STREAMLINE_VPN_MAX_RETRIES`: Overrides `settings.max_retries`.
- `STREAMLINE_VPN_OUTPUT_DIR`: Overrides `output.directory`.
