from __future__ import annotations

import asyncio
import os
import re
from typing import List, Dict, Set, Tuple
from datetime import datetime, timezone

import aiohttp


class IntelligentSourceDiscovery:
    """Discover subscription sources on GitHub and rank them.

    Uses GitHub Search API when available (with optional GITHUB_TOKEN);
    gracefully degrades to empty results on rate limits or network errors.
    """

    def __init__(self):
        self.discovered_sources: Dict[str, float] = {}
        self.blacklist: Set[str] = set()
        self.source_scores: Dict[str, float] = {}

    async def discover_github_sources(self) -> List[str]:
        search_queries = [
            "v2ray subscription updated:>2024-01-01",
            "clash config stars:>10",
            "vmess vless trojan base64",
            "sing-box subscribe json",
            "hysteria2 config",
            "reality vless config",
        ]

        token = os.getenv("GITHUB_TOKEN", "").strip()
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if token:
            headers["Authorization"] = f"token {token}"

        discovered: Set[str] = set()
        async with aiohttp.ClientSession(headers=headers) as session:
            for q in search_queries:
                urls = await self._search_github(session, q)
                discovered.update(urls)

        # Score and rank sources; return top 100
        scored = await self._score_sources(list(discovered))
        return [u for (u, _) in scored[:100]]

    async def _search_github(self, session: aiohttp.ClientSession, query: str) -> Set[str]:
        urls: Set[str] = set()
        # Search code for candidate files
        search_url = f"https://api.github.com/search/code?q={query}+extension:txt+extension:yaml+extension:yml+extension:json"
        try:
            async with session.get(search_url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status != 200:
                    return urls
                data = await r.json()
        except Exception:
            return urls

        for item in data.get("items", []):
            repo = item.get("repository", {})
            full_name = repo.get("full_name")
            path = item.get("path")
            if not (full_name and path and isinstance(path, str)):
                continue
            # Derive raw URL (assume default branch main/master)
            for branch in ("main", "master"):
                raw = f"https://raw.githubusercontent.com/{full_name}/{branch}/{path}"
                if self._plausible(raw):
                    urls.add(raw)
                    break

        return urls

    async def _get_repo_metrics(self, session: aiohttp.ClientSession, full_name: str) -> Dict:
        url = f"https://api.github.com/repos/{full_name}"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status != 200:
                    return {}
                data = await r.json()
        except Exception:
            return {}
        try:
            updated_at = data.get("updated_at")
            dt = None
            if updated_at:
                dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00")).astimezone(timezone.utc)
            return {
                "stars": int(data.get("stargazers_count") or 0),
                "forks": int(data.get("forks_count") or 0),
                "updated_at": dt,
            }
        except Exception:
            return {}

    async def _score_sources(self, sources: List[str]) -> List[Tuple[str, float]]:
        scored: List[Tuple[str, float]] = []
        # Group by repo to avoid repeated metric fetches
        by_repo: Dict[str, List[str]] = {}
        for s in sources:
            m = re.search(r"githubusercontent\.com/([^/]+/[^/]+)/", s)
            key = m.group(1) if m else ""
            by_repo.setdefault(key, []).append(s)

        token = os.getenv("GITHUB_TOKEN", "").strip()
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"
        async with aiohttp.ClientSession(headers=headers) as session:
            metrics_cache: Dict[str, Dict] = {}
            for repo, urls in by_repo.items():
                repo_metrics = metrics_cache.get(repo)
                if repo and repo_metrics is None:
                    repo_metrics = await self._get_repo_metrics(session, repo)
                    metrics_cache[repo] = repo_metrics
                for url in urls:
                    score = 0.0
                    if url.endswith((".txt", ".yaml", ".yml", ".json")):
                        score += 3.0
                    if any(k in url.lower() for k in ("official", "verified", "trusted")):
                        score += 2.0
                    if any(k in url.lower() for k in ("temp", "test", "backup", "old")):
                        score -= 2.0
                    if repo_metrics:
                        stars = repo_metrics.get("stars", 0)
                        forks = repo_metrics.get("forks", 0)
                        score += min(stars / 100.0, 10.0)
                        score += min(forks / 10.0, 5.0)
                        dt = repo_metrics.get("updated_at")
                        if isinstance(dt, datetime):
                            days = max(0, (datetime.now(timezone.utc) - dt).days)
                            if days < 7:
                                score += 5.0
                            elif days < 30:
                                score += 3.0
                            elif days < 90:
                                score += 1.0
                    scored.append((url, max(0.0, score)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def _plausible(self, url: str) -> bool:
        u = url.lower()
        if any(k in u for k in ("license", "readme", "/rules", "acl4ssr")):
            return False
        return any(k in u for k in ("sub", "mix", "subscribe", "subscription", "clash", "v2ray", "vmess", "vless", "trojan", "sing", "hysteria"))
