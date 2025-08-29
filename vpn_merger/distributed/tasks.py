from __future__ import annotations

import asyncio
import os
from typing import Dict, List, Tuple

try:
    from celery import Celery  # type: ignore
except Exception as e:  # pragma: no cover
    Celery = None  # type: ignore


def _create_app() -> "Celery":  # type: ignore
    if Celery is None:  # pragma: no cover
        raise RuntimeError("Celery not installed")
    broker = os.environ.get('CELERY_BROKER_URL') or os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    backend = os.environ.get('CELERY_RESULT_BACKEND') or broker
    return Celery('vpn_merger', broker=broker, backend=backend)


app = _create_app() if Celery is not None else None  # type: ignore


if app is not None:
    @app.task(name='vpn_merger.process_sources_task')  # type: ignore
    def process_sources_task(urls: List[str]) -> Dict[str, List[str]]:
        from vpn_merger.services.fetcher_service import AsyncSourceFetcher  # type: ignore
        from vpn_merger.processing.parser import ProtocolParser  # type: ignore

        def _processor(text: str) -> List[str]:
            lines: List[str] = []
            for raw in text.splitlines():
                s = raw.strip()
                if not s:
                    continue
                if ProtocolParser.categorize(s) != 'Other':
                    lines.append(s)
            return lines

        async def run(urls: List[str]) -> Dict[str, List[str]]:
            fetcher = AsyncSourceFetcher(_processor, concurrency=20, per_host=5, use_pool=False)
            await fetcher.open()
            try:
                pairs: List[Tuple[str, List[str]]] = await fetcher.fetch_many(urls)
            finally:
                await fetcher.close()
            return {url: lst for url, lst in pairs}

        return asyncio.run(run(urls))

