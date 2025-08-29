from __future__ import annotations

"""Placeholder middleware definitions for REST server."""

from typing import Callable, Awaitable


def simple_logger(handler: Callable[..., Awaitable]):  # pragma: no cover - demo
    async def _inner(*args, **kwargs):
        return await handler(*args, **kwargs)

    return _inner

