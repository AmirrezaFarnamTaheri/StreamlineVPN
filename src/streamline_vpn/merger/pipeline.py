from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import List, Set, Tuple

import aiohttp

from .config import Settings
from .source_manager import check_and_update_sources, fetch_and_parse_configs
from .telegram_scraper import scrape_telegram_configs
from .output_generator import deduplicate_and_filter, output_files
from .utils import choose_proxy


class AggregationPipeline:
    def __init__(self, cfg: Settings):
        self.cfg = cfg
        self.stats: Dict[str, int] = {
            "valid_sources": 0,
            "fetched_configs": 0,
            "written_configs": 0,
        }

    async def run(
        self,
        protocols: List[str] | None = None,
        sources_file: Path,
        channels_file: Path,
        last_hours: int = 24,
        *,
        failure_threshold: int = 3,
        prune: bool = True,
    ) -> Tuple[Path, List[Path]]:
        out_dir = Path(self.cfg.output_dir)
        start = time.time()

        proxy = choose_proxy(self.cfg)
        connector = aiohttp.TCPConnector(limit=self.cfg.concurrent_limit)
        session = aiohttp.ClientSession(connector=connector, proxy=proxy)

        configs: Set[str] = set()
        try:
            sources = await check_and_update_sources(
                sources_file,
                self.cfg.concurrent_limit,
                self.cfg.request_timeout,
                retries=self.cfg.retry_attempts,
                base_delay=self.cfg.retry_base_delay,
                failures_path=sources_file.with_suffix(".failures.json"),
                max_failures=failure_threshold,
                prune=prune,
                disabled_path=(
                    sources_file.with_name("sources_disabled.txt") if prune else None
                ),
                proxy=proxy,
                session=session,
            )
            self.stats["valid_sources"] = len(sources)

            http_configs = await fetch_and_parse_configs(
                sources, self.cfg, proxy=proxy, session=session
            )
            configs.update(http_configs)

            telegram_configs = await scrape_telegram_configs(
                self.cfg, channels_file, last_hours
            )
            configs.update(telegram_configs)

            self.stats["fetched_configs"] = len(configs)
            logging.info("Fetched configs count: %d", self.stats["fetched_configs"])

        except KeyboardInterrupt:
            logging.warning("Interrupted. Writing partial results...")
        finally:
            final_configs = deduplicate_and_filter(configs, self.cfg, protocols)
            self.stats["written_configs"] = len(final_configs)
            logging.info("Final configs count: %d", self.stats["written_configs"])

            files = output_files(final_configs, out_dir, self.cfg)
            await session.close()

            elapsed = time.time() - start
            summary = (
                f"Sources checked: {self.stats['valid_sources']} | "
                f"Configs fetched: {self.stats['fetched_configs']} | "
                f"Unique configs: {self.stats['written_configs']} | "
                f"Elapsed: {elapsed:.1f}s"
            )
            print(summary)
            logging.info(summary)

        return out_dir, files


async def run_pipeline(
    cfg: Settings,
    protocols: List[str] | None = None,
    sources_file: Path,
    channels_file: Path,
    last_hours: int = 24,
    *,
    failure_threshold: int = 3,
    prune: bool = True,
) -> Tuple[Path, List[Path]]:
    """Run the aggregation pipeline and return output directory and files."""
    pipeline = AggregationPipeline(cfg)
    return await pipeline.run(
        protocols,
        sources_file,
        channels_file,
        last_hours,
        failure_threshold=failure_threshold,
        prune=prune,
    )
