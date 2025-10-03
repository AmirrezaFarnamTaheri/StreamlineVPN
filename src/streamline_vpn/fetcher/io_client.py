"""
Asynchronous HTTP request execution helper.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional

import aiohttp

from ..utils.logging import get_logger

logger = get_logger(__name__)


async def execute_request(
    session: aiohttp.ClientSession,
    url: str,
    *,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Any] = None,
    params: Optional[Dict[str, Any]] = None,
    retry_attempts: int = 3,
    retry_delay: float = 1.0,
    rate_limiters: Optional[Dict[str, Any]] = None,
    get_domain=None,
) -> str:
    """
    Executes an HTTP request with retry logic using a provided session.
    """
    if session is None or session.closed:
        raise RuntimeError("Aiohttp session is closed or not provided.")

    last_exc: Optional[BaseException] = None
    for attempt in range(retry_attempts + 1):
        try:
            start = time.time()
            logger.debug("Fetching URL (attempt %d): %s %s", attempt + 1, method, url)

            async with session.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                params=params,
            ) as resp:
                logger.debug("Response for %s: %s", url, resp.status)
                resp.raise_for_status()
                content = await resp.text()

                # Record response time for adaptive rate limiting
                if rate_limiters and get_domain:
                    domain = get_domain(url)
                    if rl := rate_limiters.get(domain):
                        await rl.record_response_time(domain, time.time() - start)

                return content
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning("Attempt %d failed for %s: %s", attempt + 1, url, e)
            last_exc = e
            if attempt < retry_attempts:
                await asyncio.sleep(retry_delay * (2**attempt))
            else:
                break

    assert last_exc is not None
    raise last_exc