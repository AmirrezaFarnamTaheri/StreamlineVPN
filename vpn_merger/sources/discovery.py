from __future__ import annotations

"""Unified discovery facade combining baseline and intelligent mechanisms."""

from typing import List, Set


async def discover_all(limit: int | None = 200) -> List[str]:
    urls: Set[str] = set()
    # Baseline regex/HTML parser
    try:
        from vpn_merger.core.source_discovery import discover_sources  # type: ignore

        urls.update(await discover_sources())
    except Exception:
        pass
    # Intelligent GitHub API discovery
    try:
        from vpn_merger.discovery.intelligent_discovery import IntelligentSourceDiscovery  # type: ignore

        d = IntelligentSourceDiscovery()
        urls.update(await d.discover_github_sources())
    except Exception:
        pass
    out = list(dict.fromkeys(urls))
    if limit:
        return out[: int(limit)]
    return out

