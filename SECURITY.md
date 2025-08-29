# Security Policy

This project fetches and processes third‑party VPN subscription feeds. Treat all inbound data as untrusted.

## Threat Model & Controls

- Input validation: All hostnames and ports are validated before any connection attempt.
- File safety: Output paths are validated; writes are atomic with rollback on error.
- Deserialization: YAML files are loaded using `yaml.safe_load()` only.
- TLS: No code disables certificate checks or hostname verification when TLS is used.
- Resource guards: Bounded concurrency, backoff + circuit breaker, and per‑host rate limiting reduce abuse and load.

## API Security

- REST endpoints can be protected with a static token by setting `API_TOKEN`.
- Rate limiting is applied per IP for public endpoints.

## Reporting a Vulnerability

Open a GitHub issue with a minimal PoC, or contact the maintainers off‑platform if disclosure should be private. We aim to respond within 72 hours and patch critical issues promptly.

