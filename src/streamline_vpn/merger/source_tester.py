from __future__ import annotations

import asyncio
from typing import List, Optional

import aiohttp
from tqdm import tqdm

from .source_fetcher import fetch_text, parse_first_configs
from .result_processor import EnhancedConfigProcessor
from .utils import choose_proxy
from .config import CONFIG


class SourceTester:
    def __init__(self, fetcher):
        self.fetcher = fetcher

    async def test_and_filter_sources(self, sources: List[str]) -> List[str]:
        """Test all sources for availability and filter out dead links."""
        assert self.fetcher.session is not None

        try:
            # Test all sources concurrently
            semaphore = asyncio.Semaphore(CONFIG.concurrent_limit)

            async def test_single_source(url: str) -> Optional[str]:
                async with semaphore:
                    is_available = await self.fetcher.test_source_availability(url)
                    return url if is_available else None

            tasks = [test_single_source(url) for url in sources]

            completed = 0
            available_sources = []

            for coro in asyncio.as_completed(tasks):
                result = await coro
                completed += 1

                if result:
                    available_sources.append(result)
                    status = "✅ Available"
                else:
                    status = "❌ Dead link"

                print(f"  [{completed:03d}/{len(sources)}] {status}")

            removed_count = len(sources) - len(available_sources)
            print(f"\n   🗑️ Removed {removed_count} dead sources")
            print(f"   ✅ Keeping {len(available_sources)} available sources")

            return available_sources

        finally:
            # Don't close session here, we'll reuse it
            pass

    async def preflight_connectivity_check(
        self, available_sources: List[str], max_tests: int = 5
    ) -> bool:
        """Quickly test a handful of configs to verify connectivity."""
        if not available_sources:
            return False

        assert self.fetcher.session is not None
        tested = 0
        proc = EnhancedConfigProcessor()

        progress = tqdm(total=max_tests, desc="Testing", unit="cfg", leave=False)

        for url in available_sources:
            if tested >= max_tests:
                break

            text = await fetch_text(
                self.fetcher.session,
                url,
                int(CONFIG.request_timeout),
                retries=1,
                base_delay=0.5,
                proxy=choose_proxy(CONFIG),
            )
            if not text:
                continue

            configs = parse_first_configs(text, max_tests - tested)
            for cfg in configs:
                host, port = proc.extract_host_port(cfg)
                if host and port:
                    ping = await proc.test_connection(host, port)
                    tested += 1
                    progress.update(1)
                    if ping is not None:
                        progress.close()
                        return True
                    if tested >= max_tests:
                        break

        progress.close()

        return False
