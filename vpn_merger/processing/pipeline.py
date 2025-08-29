from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, List


@dataclass
class PipelineStage:
    name: str
    processor: Callable[[Any], Awaitable[Any]]
    concurrency: int = 10


class AsyncPipeline:
    """Composable async pipeline with per-stage concurrency.

    Example:
        p = AsyncPipeline()
        p.add_stage("fetch", fetch, 50).add_stage("parse", parse, 100)
        results = await p.process(inputs)
    """

    def __init__(self) -> None:
        self.stages: List[PipelineStage] = []

    def add_stage(self, name: str, processor: Callable[[Any], Awaitable[Any]], concurrency: int = 10) -> "AsyncPipeline":
        self.stages.append(PipelineStage(name, processor, concurrency))
        return self

    async def process(self, items: List[Any]) -> List[Any]:
        current = items
        for stage in self.stages:
            sem = asyncio.Semaphore(max(1, stage.concurrency))

            async def run_one(item: Any):
                async with sem:
                    return await stage.processor(item)

            results = await asyncio.gather(*[run_one(i) for i in current], return_exceptions=True)
            # Drop exceptions, keep successful results only
            current = [r for r in results if not isinstance(r, Exception)]
        return current

