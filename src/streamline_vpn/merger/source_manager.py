from __future__ import annotations

import asyncio
import json
import logging
import random
from pathlib import Path
from typing import Set, List

import aiohttp
from aiohttp import ClientSession
from tqdm import tqdm

from .config import Settings
from .utils import parse_configs_from_text
from .source_fetcher import fetch_text


async def check_and_update_sources(
    path: Path,
    concurrent_limit: int = 20,
    request_timeout: int = 10,
    *,
    retries: int = 3,
    base_delay: float = 1.0,
    failures_path: Path | None = None,
    max_failures: int = 3,
    prune: bool = True,
    disabled_path: Path | None = None,
    proxy: str | None = None,
    session: ClientSession | None = None,
) -> List[str]:
    if not path.exists():
        logging.warning("sources file not found: %s", path)
        return []

    if failures_path is None:
        failures_path = path.with_suffix(".failures.json")

    try:
        failures = json.loads(failures_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        logging.warning("Failed to load failures file: %s", exc)
        failures = {}

    with path.open() as f:
        seen = set()
        sources: List[str] = []
        for line in f:
            url = line.strip()
            if not url:
                continue
            if url not in seen:
                seen.add(url)
                sources.append(url)

    valid_sources: List[str] = []
    removed: List[str] = []
    semaphore = asyncio.Semaphore(concurrent_limit)

    async def check(sess: ClientSession, url: str) -> tuple[str, bool]:
        async with semaphore:
            text = await fetch_text(
                sess,
                url,
                request_timeout,
                retries=retries,
                base_delay=base_delay,
                proxy=proxy,
            )
        if not text or not parse_configs_from_text(text):
            return url, False
        return url, True

    async def run_checks(sess: ClientSession) -> None:
        tasks = [asyncio.create_task(check(sess, u)) for u in sources]
        for task in asyncio.as_completed(tasks):
            url, ok = await task
            if ok:
                failures.pop(url, None)
                valid_sources.append(url)
            else:
                failures[url] = failures.get(url, 0) + 1
                if prune and failures[url] >= max_failures:
                    removed.append(url)

    if session is None:
        connector = aiohttp.TCPConnector(limit=concurrent_limit)
        session_cm = aiohttp.ClientSession(connector=connector, proxy=proxy)
        async with session_cm as sess:
            await run_checks(sess)
    else:
        await run_checks(session)

    remaining = [u for u in sources if u not in removed]
    with path.open("w") as f:
        for url in remaining:
            f.write(f"{url}\n")

    if disabled_path and removed:
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat()
        with disabled_path.open("a") as f:
            for url in removed:
                f.write(f"{timestamp} {url}\n")
    for url in removed:
        failures.pop(url, None)

    failures_path.write_text(json.dumps(failures, indent=2))

    logging.info("Valid sources: %d", len(valid_sources))
    return valid_sources


async def fetch_and_parse_configs(
    sources: list[str],
    cfg: Settings,
    *,
    proxy: str | None = None,
    session: ClientSession | None = None,
) -> Set[str]:
    configs: Set[str] = set()

    if cfg.shuffle_sources:
        random.shuffle(sources)

    semaphore = asyncio.Semaphore(cfg.concurrent_limit)

    async def fetch_one(session: ClientSession, url: str) -> Set[str]:
        async with semaphore:
            text = await fetch_text(
                session,
                url,
                cfg.request_timeout,
                retries=cfg.retry_attempts,
                base_delay=cfg.retry_base_delay,
                proxy=proxy,
            )
        if not text:
            logging.warning("Failed to fetch %s", url)
            return set()
        return parse_configs_from_text(text)

    async def run_fetch(sess: ClientSession) -> None:
        tasks = [asyncio.create_task(fetch_one(sess, u)) for u in sources]
        for task in asyncio.as_completed(tasks):
            configs.update(await task)
            if cfg.enable_url_testing:
                progress.update(1)

    progress = tqdm(total=len(sources), desc="Sources", unit="src", leave=False)
    try:
        if session is None:
            connector = aiohttp.TCPConnector(limit=cfg.concurrent_limit)
            session_cm = aiohttp.ClientSession(connector=connector, proxy=proxy)
            async with session_cm as sess:
                await run_fetch(sess)
        else:
            await run_fetch(session)
    finally:
        progress.close()

    return configs
