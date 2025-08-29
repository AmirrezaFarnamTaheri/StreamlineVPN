from __future__ import annotations

"""Expose source manager from core."""

try:
    from vpn_merger.core.source_manager import IntelligentSourceManager as SourceManager  # type: ignore
except Exception:  # pragma: no cover
    class SourceManager:  # type: ignore
        pass

