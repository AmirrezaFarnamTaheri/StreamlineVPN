from __future__ import annotations

"""Data model re-exports for compatibility with new layout."""

try:
    from vpn_merger.core.processor import ConfigResult  # type: ignore
except Exception:  # pragma: no cover
    class ConfigResult:  # type: ignore
        pass

