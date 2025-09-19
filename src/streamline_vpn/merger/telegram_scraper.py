from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Set

import aiohttp
from telethon import TelegramClient, events, errors
from telethon.tl.custom.message import Message
from tqdm import tqdm

from .config import Settings
from .utils import parse_configs_from_text, choose_proxy
from .source_fetcher import fetch_text, extract_subscription_urls


async def scrape_telegram_configs(
    cfg: Settings, channels_path: Path, last_hours: int
) -> Set[str]:
    if cfg.telegram_api_id is None or cfg.telegram_api_hash is None:
        logging.info("Telegram credentials not provided; skipping Telegram scrape")
        return set()
    if not channels_path.exists():
        logging.warning("channels file missing: %s", channels_path)
        return set()

    prefix = "https://t.me/"
    with channels_path.open() as f:
        channels = [
            (
                line.strip()[len(prefix) :]
                if line.strip().startswith(prefix)
                else line.strip()
            )
            for line in f
            if line.strip()
        ]

    if not channels:
        logging.info("No channels specified in %s", channels_path)
        return set()

    since = datetime.utcnow() - timedelta(hours=last_hours)
    client = TelegramClient(
        cfg.session_path, cfg.telegram_api_id, cfg.telegram_api_hash
    )
    progress = tqdm(total=len(channels), desc="Channels", unit="chan", leave=False)
    configs: Set[str] = set()

    try:
        await client.start()
        async with aiohttp.ClientSession(proxy=choose_proxy(cfg)) as session:
            for channel in channels:
                count_before = len(configs)
                success = False
                for _ in range(2):
                    try:
                        async for msg in client.iter_messages(
                            channel, offset_date=since
                        ):
                            if isinstance(msg, Message) and msg.message:
                                text = msg.message
                                configs.update(parse_configs_from_text(text))
                                for sub in extract_subscription_urls(text):
                                    text2 = await fetch_text(
                                        session,
                                        sub,
                                        cfg.request_timeout,
                                        retries=cfg.retry_attempts,
                                        base_delay=cfg.retry_base_delay,
                                        proxy=choose_proxy(cfg),
                                    )
                                    if text2:
                                        configs.update(
                                            parse_configs_from_text(text2)
                                        )
                        success = True
                        break
                    except (errors.RPCError, OSError) as e:
                        logging.warning("Error scraping %s: %s", channel, e)
                        try:
                            await client.disconnect()
                            await client.connect()
                        except (errors.RPCError, OSError) as rexc:
                            logging.warning("Reconnect failed: %s", rexc)
                            break
                if not success:
                    logging.warning("Skipping %s due to repeated errors", channel)
                    progress.update(1)
                    continue
                logging.info(
                    "Channel %s -> %d new configs",
                    channel,
                    len(configs) - count_before,
                )
                progress.update(1)
        await client.disconnect()
    except (errors.RPCError, OSError, aiohttp.ClientError) as e:
        logging.warning("Telegram connection failed: %s", e)
        try:
            await client.disconnect()
        except (errors.RPCError, OSError):
            pass
        return set()
    finally:
        progress.close()

    logging.info("Telegram configs found: %d", len(configs))
    return configs


async def telegram_bot_mode(
    cfg: Settings,
    sources_file: Path,
    channels_file: Path,
    last_hours: int,
    run_pipeline_func,
) -> None:
    """Launch Telegram bot for on-demand updates."""
    if not all(
        [
            cfg.telegram_api_id,
            cfg.telegram_api_hash,
            cfg.telegram_bot_token,
            cfg.allowed_user_ids,
        ]
    ):
        logging.info("Telegram credentials not provided; skipping bot mode")
        return

    bot = await TelegramClient(
        cfg.session_path, cfg.telegram_api_id, cfg.telegram_api_hash
    ).start(bot_token=cfg.telegram_bot_token)
    last_update = None

    @bot.on(events.NewMessage(pattern="/help"))
    async def help_handler(event: events.NewMessage.Event) -> None:
        if event.sender_id not in cfg.allowed_user_ids:
            return
        await event.respond("/update - run aggregation\n/status - last update time")

    @bot.on(events.NewMessage(pattern="/update"))
    async def update_handler(event: events.NewMessage.Event) -> None:
        nonlocal last_update
        if event.sender_id not in cfg.allowed_user_ids:
            return
        await event.respond("Running update...")

        out_dir, files = await run_pipeline_func(
            cfg,
            None,
            sources_file,
            channels_file,
            last_hours,
        )

        for path in files:
            await event.respond(file=str(path))
        last_update = datetime.utcnow()

    @bot.on(events.NewMessage(pattern="/status"))
    async def status_handler(event: events.NewMessage.Event) -> None:
        if event.sender_id not in cfg.allowed_user_ids:
            return
        msg = "Never" if not last_update else last_update.isoformat()
        await event.respond(f"Last update: {msg}")

    logging.info("Bot running. Press Ctrl+C to exit.")
    await bot.run_until_disconnected()
