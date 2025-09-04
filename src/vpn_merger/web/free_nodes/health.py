from __future__ import annotations

import asyncio
import time
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import CONNECT_TIMEOUT, HEALTH_CONCURRENCY
from .db import NodeModel


async def tcp_latency(host: str, port: int) -> int | None:
    try:
        start = time.perf_counter()
        conn = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(conn, timeout=CONNECT_TIMEOUT)
        writer.close()
        if hasattr(writer, "wait_closed"):
            try:
                await writer.wait_closed()
            except Exception:
                pass
        return int((time.perf_counter() - start) * 1000)
    except Exception:
        return None


def score_node(proto: str, port: int, params: dict, latency_ms: int | None) -> float:
    score = 0.0
    if port in (443, 8443):
        score += 1.2
    tlsish = (proto == "vless" and (params.get("security") == "reality" or (params.get("reality") or {}).get("enabled"))) or (params.get("tls") == "tls")
    if tlsish:
        score += 1.0
    if latency_ms is not None:
        score += max(0.0, 1.0 - min(1000, latency_ms) / 1000.0)
    return round(score, 3)


async def apply_health(sess: AsyncSession, nodes: list[NodeModel]):
    sem = asyncio.Semaphore(HEALTH_CONCURRENCY)

    async def one(m: NodeModel):
        async with sem:
            lat = await tcp_latency(m.host, m.port)
            params = json_loads_safe(m.params_json)
            m.latency_ms = lat if lat is not None else None
            m.healthy = lat is not None
            m.score = score_node(m.proto, m.port, params, m.latency_ms)
            m.last_checked = datetime.utcnow()

    await asyncio.gather(*(one(m) for m in nodes))
    await sess.commit()


def json_loads_safe(s: str | None) -> dict:
    if not s:
        return {}
    try:
        import json

        return json.loads(s)
    except Exception:
        return {}


