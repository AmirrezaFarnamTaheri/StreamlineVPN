from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, Iterable, List, Any


async def gather_limited(fn: Callable[[Any], Awaitable[Any]], items: Iterable[Any], concurrency: int = 10) -> List[Any]:
    sem = asyncio.Semaphore(concurrency)

    async def run(item: Any) -> Any:
        async with sem:
            return await fn(item)

    return await asyncio.gather(*[run(i) for i in items])

