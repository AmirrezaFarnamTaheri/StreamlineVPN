from __future__ import annotations

import asyncio
from collections import deque
from typing import Deque, List, Callable, Any, Awaitable


class PerformanceManager:
    """Bounded processor for memory- and concurrency-aware workloads.

    Not wired into the main flow by default; provided for targeted adoption
    in heavy loops (e.g., parsing/testing) when needed.
    """

    def __init__(self, max_workers: int = 50, max_memory_mb: int = 512):
        self.semaphore = asyncio.Semaphore(max_workers)
        self.memory_limit = max_memory_mb * 1024 * 1024
        self.task_queue: Deque = deque()

    async def process_bounded(self,
                              items: List[Any],
                              processor: Callable[[Any], Awaitable[Any]],
                              batch_size: int = 100) -> List[Any]:
        results: List[Any] = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            if self._get_memory_usage() > self.memory_limit:
                await self._free_memory()
            batch_results = await self._process_batch(batch, processor)
            results.extend(batch_results)
            if len(results) > 10000:
                # In real adoption, save checkpoint to disk here
                results = results[-1000:]  # keep tail
        return results

    async def _process_batch(self, batch: List[Any], processor: Callable[[Any], Awaitable[Any]]) -> List[Any]:
        async def run_one(item: Any):
            async with self.semaphore:
                return await processor(item)
        tasks = [asyncio.create_task(run_one(x)) for x in batch]
        out = await asyncio.gather(*tasks, return_exceptions=True)
        return [x for x in out if not isinstance(x, Exception)]

    def _get_memory_usage(self) -> int:
        try:
            import psutil  # type: ignore
            return psutil.Process().memory_info().rss
        except Exception:
            return 0

    async def _free_memory(self) -> None:
        try:
            import gc
            gc.collect()
        except Exception:
            pass

