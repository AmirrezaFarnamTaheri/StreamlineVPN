Development Guide
=================

Setup
-----

- Python 3.10+
- Create a venv and install requirements: `pip install -r requirements.txt`
- Optional: dev extras `pip install -e .[dev]`

Run Tests
---------

- Run core suite: `pytest -q`
- Focus specific tests: `pytest -q tests/test_core.py`

Code Structure
--------------

- Core orchestration: `streamline_vpn/core/merger.py`, `merger_base.py`, `merger_processor.py`
- Configuration processing: `core/processing/` with protocol parsers in `parsers/`
- Output formatting: `core/output/` with `OutputManager`
- Fetching: `fetcher/` with IO in `io_client.py`, policies in `policies.py`
- Security: `security/manager.py`, `security/validator.py`, helpers in `security/manager_utils/`
- Utilities: `utils/`
- Settings: `settings.py` (env-aware getters)

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

- Versioning in `setup.py`. Ensure README and docs are up to date.

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
- Web: `API_BASE_URL` to point the UI at a non-default API (e.g., `https://api.example.com`).
- Web CSP: `WEB_CONNECT_SRC_EXTRA` to add extra `connect-src` origins (space or comma separated).
