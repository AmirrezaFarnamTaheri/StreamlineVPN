from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Tuple, Optional


class DistributedCoordinator:
    """Coordinator facade for distributed processing (Phase 3 bootstrap).

    This implementation is dependency-light. It exposes an interface compatible
    with celery/redis setups, but degrades to local processing when those
    packages are unavailable. Actual distributed execution must be wired by the
    operator (workers, broker).
    """

    def __init__(self, redis_url: str | None = None, worker_count: int = 4):
        self.redis_url = redis_url
        self.worker_count = int(worker_count)

    async def distribute_sources(self, sources: List[str]) -> Dict[str, Any]:
        parts = self._partition_sources(sources, max(1, self.worker_count))
        # Attempt celery-based dispatch if celery available, else local
        try:
            from .tasks import process_sources_task  # type: ignore
            task_ids = [process_sources_task.delay(chunk).id for chunk in parts]
            return {"mode": "celery", "tasks": task_ids}
        except Exception:
            # Local fallback: parallel processing per chunk
            results: Dict[str, Any] = {}
            for chunk in parts:
                r = await self._local_process(chunk)
                results.update(r)
            return {"mode": "local", "results": results}

    async def collect_results(self, task_ids: List[str], timeout: float = 60.0) -> Dict[str, List[str]]:
        """Collect Celery results for given task IDs. Returns merged mapping.

        If Celery is not available, returns empty mapping.
        """
        try:
            from celery.result import AsyncResult  # type: ignore
        except Exception:
            return {}
        import time
        start = time.time()
        merged: Dict[str, List[str]] = {}
        remaining = set(task_ids)
        while remaining and (time.time() - start) < timeout:
            done_now: List[str] = []
            for tid in list(remaining):
                try:
                    res = AsyncResult(tid)
                    if res.ready():
                        data = res.get(timeout=0) or {}
                        if isinstance(data, dict):
                            for k, v in data.items():
                                if isinstance(v, list):
                                    merged[k] = v
                        done_now.append(tid)
                except Exception:
                    done_now.append(tid)
            for tid in done_now:
                remaining.discard(tid)
            if remaining:
                await asyncio.sleep(0.5)
        return merged

    def _partition_sources(self, sources: List[str], n: int) -> List[List[str]]:
        chunk = max(1, len(sources) // n + (1 if len(sources) % n else 0))
        return [sources[i:i + chunk] for i in range(0, len(sources), chunk)]

    async def _local_process(self, chunk: List[str]) -> Dict[str, Any]:
        """Local fallback using service fetcher and protocol parsing."""
        try:
            from vpn_merger.services.fetcher_service import AsyncSourceFetcher  # type: ignore
            from vpn_merger.processing.parser import ProtocolParser  # type: ignore
        except Exception:
            # Degrade to empty results if services are not available
            return {url: [] for url in chunk}

        def _processor(text: str) -> List[str]:
            lines: List[str] = []
            for raw in text.splitlines():
                s = raw.strip()
                if not s:
                    continue
                if ProtocolParser.categorize(s) != 'Other':
                    lines.append(s)
            return lines

        fetcher = AsyncSourceFetcher(_processor, concurrency=20, per_host=5, use_pool=False)
        await fetcher.open()
        try:
            pairs: List[Tuple[str, List[str]]] = await fetcher.fetch_many(chunk)
        finally:
            await fetcher.close()
        return {url: lst for url, lst in pairs}
