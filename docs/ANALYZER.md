Analyzer & Security Overview
============================

Security Manager
----------------

- High-level threat analysis via `security/manager.py` using:
  - Suspicious text pattern scanning
  - URL analysis for suspicious TLDs and block lists
  - Config validation via `security/validator.py`
- Risk score combines threats, suspicious patterns, and bad URLs.

Tuning
------

- Override suspicious TLDs, safe protocols/ports via environment variables (see `docs/CONFIGURATION.md`).
- Patterns for scanning can be extended via `STREAMLINE_SECURITY_SUSPICIOUS_TEXT_PATTERNS`.

Performance & Fetching
----------------------

- HTTP request behavior tunable via env (concurrency, timeouts, retries).
- Per-domain policies: circuit breakers and adaptive rate limiting (`fetcher/policies.py`).

Observability
-------------

- `utils/logging.py` provides structured logging helpers.
- Output statistics written to `output/statistics.json` via the merger.

