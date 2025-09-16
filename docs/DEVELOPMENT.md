Development Guide
=================

Setup
-----

- Python 3.8+
- Create a venv and install requirements: `pip install -r requirements.txt`
- Optional: dev extras `pip install -e .[dev]`

Run Tests
---------

- Run full suite: `pytest -q`
- With coverage summary: `pytest -q --cov=src --cov-report=term-missing`
- XML coverage (for gates/CI): `pytest -q --cov=src --cov-report=xml:coverage.xml`
- Coverage gate: `python scripts/coverage_gate.py coverage.xml`

Code Structure
--------------

- Core orchestration: `src/streamline_vpn/core/merger.py`, `core/source/manager.py`, `core/output_manager.py`
- Configuration processing: `src/streamline_vpn/core/processing/` with protocol parsers in `src/streamline_vpn/core/parsers/`
- Output formatting: `src/streamline_vpn/core/output_manager.py`
- Fetching: `src/streamline_vpn/core/fetcher/` with IO in `io_client.py`, policies in `policies.py`
- Security: `src/streamline_vpn/security/manager.py`, `security/auth/threat_analyzer.py`
- Utilities: `src/streamline_vpn/utils/`
- Settings: `src/streamline_vpn/settings.py` (env-aware getters)

Conventions
-----------

- Keep modules small and cohesive; prefer delegating to helpers.
- Use `streamline_vpn.settings` getters for runtime-tunable values.
- Avoid circular imports by deferring imports inside functions where reasonable.

Formatting & Linting
--------------------

- Use Black, Ruff/Flake8, and MyPy if installed (see `setup.py` extras).

Releases
--------

- Versioning in `setup.py`/`pyproject.toml`. Ensure README and docs are up to date.

Run Servers
-----------

Development servers for API and Web UI:

```bash
# API server (respects API_HOST, API_PORT)
python run_api.py

# Web interface (respects WEB_HOST, WEB_PORT)
# Optionally set API_BASE_URL if API is not localhost:8080
# Optionally set WEB_CONNECT_SRC_EXTRA for additional CSP connect-src entries
python run_web.py
```

Environment tips:

- API: `API_HOST` (default `0.0.0.0`), `API_PORT` (default `8080`).
- Web: `API_BASE_URL` to point the UI at a non-default API (e.g., `https://api.test-server.example`).
- Web CSP: `WEB_CONNECT_SRC_EXTRA` to add extra `connect-src` origins (space or comma separated).
