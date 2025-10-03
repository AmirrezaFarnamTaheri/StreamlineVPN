# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-03

### Added
- Centralized, non-blocking `aiohttp.ClientSession` management within the application lifespan to resolve server timeouts.
- New, modular API structure with dedicated files for routes, models, and dependencies.
- Hypercorn as the default ASGI server for improved performance and stability.
- Comprehensive project validator script (`scripts/comprehensive_validator.py`).
- `CHANGELOG.md` and `CONTRIBUTING.md` to improve project documentation.

### Changed
- Refactored monolithic `api.py`, `unified_api.py`, and `merger.py` files into smaller, more maintainable modules.
- Replaced Uvicorn with Hypercorn in the main runner script (`run_unified.py`).
- Switched all route modules to use robust, absolute imports instead of fragile relative ones.
- Updated `README.md` to reflect the change to Hypercorn.

### Fixed
- Resolved persistent server timeout issue by replacing Uvicorn and fixing blocking I/O patterns.
- Corrected a critical circular import between the `unified_api` and `api` modules.
- Fixed numerous `ImportError`, `NameError`, and `IndentationError` bugs that were preventing the application from starting.
- Fixed a `TypeError` in the `SecurityManager`'s shutdown method.
- Corrected a `RuntimeError` in the pipeline and system route modules related to session handling in background tasks.

### Removed
- Deleted the redundant and overly complex `static_server.py`.
- Removed the faulty and blocking `io_client.py` module.

## [1.0.0] - Initial Release
- Initial release of the StreamlineVPN aggregator.