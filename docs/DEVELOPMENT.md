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

