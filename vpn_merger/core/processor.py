from __future__ import annotations

"""Expose config processing API from legacy module."""

try:
    from .. import vpn_merger as _root  # type: ignore
    EnhancedConfigProcessor = _root.EnhancedConfigProcessor  # type: ignore
    ConfigResult = _root.ConfigResult  # type: ignore
except Exception:  # pragma: no cover - import-time issues in tools
    # Provide minimal fallbacks used by core.merger during tests
    from dataclasses import dataclass, field
    from typing import Optional, Dict

    class EnhancedConfigProcessor:  # type: ignore
        pass

    @dataclass
    class ConfigResult:  # type: ignore
        config: str
        protocol: str
        host: Optional[str] = None
        port: Optional[int] = None
        ping_time: Optional[float] = None
        is_reachable: bool = False
        handshake_ok: Optional[bool] = None
        source_url: str = ""
        app_test_results: Dict[str, Optional[bool]] = field(default_factory=dict)
