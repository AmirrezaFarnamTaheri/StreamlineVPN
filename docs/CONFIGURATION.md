Configuration
=============

Environment Variables
---------------------

- `STREAMLINE_FETCHER_MAX_CONCURRENT` (int): concurrent HTTP requests. Default 50.
- `STREAMLINE_FETCHER_TIMEOUT_SECONDS` (int): per-request timeout. Default 30.
- `STREAMLINE_FETCHER_RETRY_ATTEMPTS` (int): retries on failure. Default 3.
- `STREAMLINE_FETCHER_RETRY_DELAY` (float): backoff base seconds. Default 1.0.
- `STREAMLINE_FETCHER_CB_FAILURE_THRESHOLD` (int): circuit breaker failures before open. Default 5.
- `STREAMLINE_FETCHER_CB_RECOVERY_TIMEOUT_SECONDS` (int): breaker recovery seconds. Default 60.
- `STREAMLINE_FETCHER_RL_MAX_REQUESTS` (int): max requests per window. Default 60.
- `STREAMLINE_FETCHER_RL_TIME_WINDOW_SECONDS` (int): window seconds. Default 60.
- `STREAMLINE_FETCHER_RL_BURST_LIMIT` (int): burst capacity. Default 10.

- `STREAMLINE_SECURITY_SUSPICIOUS_TLDS` (csv): e.g. `.tk,.ml`.
- `STREAMLINE_SECURITY_SAFE_PROTOCOLS` (csv): e.g. `http,https,vmess`.
- `STREAMLINE_SECURITY_SAFE_ENCRYPTIONS` (csv): e.g. `aes-256-gcm,chacha20-poly1305`.
- `STREAMLINE_SECURITY_SAFE_PORTS` (csv-int): e.g. `80,443,8080`.
- `STREAMLINE_SECURITY_SUSPICIOUS_TEXT_PATTERNS` (csv): regex fragments for scanning.

- `STREAMLINE_SUPPORTED_PROTOCOL_PREFIXES` (csv): e.g. `vmess://,vless://,trojan://`.

CLI Flags
---------

The CLI (`python -m streamline_vpn`) accepts the following flags:

- `--config <path>`: sources config file. Default `config/sources.yaml`.
- `--output <dir>`: output directory. Default `output`.
- `--format <name>` (repeatable): output formats (e.g., `json`, `clash`, `singbox`, `raw`).
- `--max-concurrent <int>`: sets `STREAMLINE_FETCHER_MAX_CONCURRENT`.
- `--timeout <int>`: sets `STREAMLINE_FETCHER_TIMEOUT_SECONDS`.
- `--retry-attempts <int>`: sets `STREAMLINE_FETCHER_RETRY_ATTEMPTS`.
- `--retry-delay <float>`: sets `STREAMLINE_FETCHER_RETRY_DELAY`.

These flags translate into environment variables and are consumed by modules
at runtime through `streamline_vpn.settings` getters.

