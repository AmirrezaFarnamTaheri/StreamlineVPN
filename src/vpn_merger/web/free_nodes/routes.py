from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from .db import AsyncSessionLocal, NodeMetrics, NodeModel, SourceModel
from .exports import export_singbox, get_nodes_json, subscription_txt
from .health import apply_health, score_node, tcp_latency
from .metrics import FETCH_DURATION, NODES_PROCESSED
from .parsers import parse_any
from .schemas import IngestBody, Node, SourcesBody

router = APIRouter()
log = logging.getLogger("free-nodes")


@router.get("/health")
async def health():
    return {"ok": True}


@router.post("/api/ingest")
async def ingest(body: IngestBody):
    from .db import ensure_schema

    await ensure_schema()
    if not body.links:
        raise HTTPException(400, detail="No links provided")
    nodes = [parse_any(s) for s in body.links]
    nodes = [n for n in nodes if n]
    async with AsyncSessionLocal() as sess:
        await upsert_nodes(sess, nodes)  # type: ignore
        total = (await sess.execute(select(NodeModel))).scalars().all()
        return {"ingested": len(nodes), "total": len(total)}


async def upsert_nodes(sess, nodes: list[Node]):
    import json
    from .db import NodeModel

    for n in nodes:
        params_json = json.dumps(n.params)
        key = n.key()
        existing = (await sess.execute(select(NodeModel).where(NodeModel.key == key))).scalar_one_or_none()
        if existing:
            existing.proto = n.proto
            existing.host = n.host
            existing.port = n.port
            existing.name = n.name
            existing.link = n.link
            existing.uuid = n.uuid
            existing.password = n.password
            existing.params_json = params_json
            existing.updated_at = datetime.utcnow()
        else:
            sess.add(
                NodeModel(
                    key=key,
                    proto=n.proto,
                    host=n.host,
                    port=n.port,
                    name=n.name,
                    link=n.link,
                    uuid=n.uuid,
                    password=n.password,
                    params_json=params_json,
                )
            )
    await sess.commit()


@router.post("/api/sources")
async def add_sources(body: SourcesBody):
    from .db import ensure_schema

    await ensure_schema()
    if not body.urls:
        raise HTTPException(400, detail="No URLs provided")
    async with AsyncSessionLocal() as sess:
        for u in body.urls:
            if not (u.startswith("http://") or u.startswith("https://")):
                raise HTTPException(400, detail=f"Invalid URL: {u}")
            exists = (await sess.execute(select(SourceModel).where(SourceModel.url == u))).scalar_one_or_none()
            if not exists:
                sess.add(SourceModel(url=u))
        await sess.commit()
        cnt = (await sess.execute(select(SourceModel))).scalars().all()
        return {"sources": len(cnt)}


@router.post("/api/refresh")
async def refresh_sources(healthcheck: bool = True):
    from .db import ensure_schema

    await ensure_schema()
    async with AsyncSessionLocal() as sess:
        sources = (await sess.execute(select(SourceModel))).scalars().all()
        if not sources:
            return {"fetched": 0, "note": "No sources configured"}
        collected: list[Node] = []
        for src in sources:
            try:
                t0 = time.perf_counter()
                async with httpx.AsyncClient(timeout=10.0) as client:
                    r = await client.get(src.url)
                    r.raise_for_status()
                    text = r.text
                for line in text.splitlines():
                    n = parse_any(line)
                    if n:
                        collected.append(n)
                FETCH_DURATION.labels(source=src.url).observe(time.perf_counter() - t0)
                NODES_PROCESSED.labels(source=src.url, result="success").inc()
            except Exception as e:
                log.warning(f"fetch error {src.url}: {e}")
                NODES_PROCESSED.labels(source=src.url, result="error").inc()
        # de-dupe by key
        dedup: dict[str, Node] = {n.key(): n for n in collected}
        await upsert_nodes(sess, list(dedup.values()))
        # cap store
        all_nodes = (await sess.execute(select(NodeModel))).scalars().all()
        from .config import STORE_CAP

        if len(all_nodes) > STORE_CAP:
            all_nodes.sort(key=lambda m: (m.score or 0.0, m.last_checked or datetime.min))
            drop = len(all_nodes) - STORE_CAP
            for m in all_nodes[:drop]:
                await sess.delete(m)
            await sess.commit()
        if healthcheck:
            subset = (await sess.execute(select(NodeModel))).scalars().all()
            await apply_health(sess, subset)
        total = (await sess.execute(select(NodeModel))).scalars().all()
        return {"fetched": len(dedup), "total": len(total)}


@router.get("/api/metrics")
async def list_metrics():
    async with AsyncSessionLocal() as sess:
        rows = (await sess.execute(select(NodeMetrics))).scalars().all()

        def to_dict(m: NodeMetrics):
            return {
                "node_id": m.node_id,
                "region": m.region,
                "latency_ms": m.latency_ms,
                "throughput_mbps": m.throughput_mbps,
                "packet_loss": m.packet_loss,
                "updated_at": m.updated_at.timestamp() if m.updated_at else None,
            }

        return [to_dict(m) for m in rows]


@router.get("/api/metrics/{node_id}")
async def get_metrics(node_id: int):
    async with AsyncSessionLocal() as sess:
        m = (await sess.execute(select(NodeMetrics).where(NodeMetrics.node_id == node_id))).scalar_one_or_none()
        if not m:
            raise HTTPException(404, detail="metrics not found")
        return {
            "node_id": m.node_id,
            "region": m.region,
            "latency_ms": m.latency_ms,
            "throughput_mbps": m.throughput_mbps,
            "packet_loss": m.packet_loss,
            "updated_at": m.updated_at.timestamp() if m.updated_at else None,
        }


@router.get("/api/nodes.json")
async def get_nodes(limit: int = 200, proto: str | None = None, sort: str = "score"):
    return await get_nodes_json(limit=limit, proto=proto, sort=sort)


@router.get("/api/export/singbox.json")
async def export_singbox_json(limit: int = 200):
    return await export_singbox(limit=limit)


@router.get("/api/subscription.txt")
async def subscription_text(limit: int = 200, base64out: bool = True):
    return await subscription_txt(limit=limit, base64out=base64out)


@router.get("/api/select")
async def select_primary():
    """Select a primary node with simple scoring heuristic for tests.

    Preference order: healthy desc, score desc, last_checked desc.
    Returns minimal info required by tests.
    """
    from .db import ensure_schema

    await ensure_schema()
    async with AsyncSessionLocal() as sess:
        rows = (await sess.execute(select(NodeModel))).scalars().all()
        if not rows:
            raise HTTPException(404, detail="no nodes")
        # compute effective score if missing
        def rank(m: NodeModel):
            s = m.score or 0.0
            ts = m.last_checked.timestamp() if getattr(m, "last_checked", None) else 0.0
            return (1 if getattr(m, "healthy", False) else 0, s, ts)

        rows.sort(key=rank, reverse=True)
        m = rows[0]
        return {
            "primary": {
                "host": m.host,
                "port": m.port,
                "proto": m.proto,
                "name": m.name,
            }
        }


@router.post("/api/ping")
async def ping_nodes(body: IngestBody):
    targets = [parse_any(s) for s in body.links]
    targets = [n for n in targets if n]
    sem = asyncio.Semaphore(60)

    async def one(n: Node):
        async with sem:
            n.latency_ms = await tcp_latency(n.host, n.port)
        n.healthy = n.latency_ms is not None
        n.score = score_node(n.proto, n.port, n.params, n.latency_ms)
        n.last_checked = time.time()
        return n

    out = await asyncio.gather(*(one(n) for n in targets))
    return [n.dict() for n in out]


