from __future__ import annotations

import base64
import json
import random
import re
from datetime import datetime, timedelta
from typing import Tuple

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import AsyncSessionLocal, NodeMetrics, NodeModel, SourceModel
from .health import apply_health
from .metrics import FETCH_DURATION, NODES_PROCESSED
from .parsers import parse_any


async def fetch_text(url: str, timeout: float = 10.0) -> str:
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text


async def get_nodes_json(limit: int = 200, proto: str | None = None, sort: str = "score"):
    async with AsyncSessionLocal() as sess:
        q = select(NodeModel)
        if proto:
            q = q.where(NodeModel.proto == proto)
        rows = (await sess.execute(q)).scalars().all()

        def to_dict(m: NodeModel):
            import json as _json

            return {
                "proto": m.proto,
                "host": m.host,
                "port": m.port,
                "name": m.name,
                "link": m.link,
                "uuid": m.uuid,
                "password": m.password,
                "params": _json.loads(m.params_json or "{}"),
                "latency_ms": m.latency_ms,
                "healthy": m.healthy,
                "score": m.score,
                "last_checked": m.last_checked.timestamp() if m.last_checked else None,
            }

        out = [to_dict(m) for m in rows]
        if sort == "latency":
            out.sort(key=lambda n: (n["latency_ms"] is None, n["latency_ms"] or 1e9))
        elif sort == "random":
            random.shuffle(out)
        else:
            out.sort(key=lambda n: (n.get("score") or 0.0), reverse=True)
        return out[: max(1, min(limit, 1000))]


def to_singbox_outbound(n: dict) -> dict:
    sni = (n.get("params") or {}).get("sni") or (n.get("params") or {}).get("server_name")
    proto = n.get("proto")
    params = n.get("params") or {}
    tag = re.sub(r"\s+", "-", n.get("name", "node")).lower()
    if proto == "vless":
        reality = params.get("security") == "reality" or (params.get("reality") or {}).get(
            "enabled"
        )
        ob = {
            "type": "vless",
            "tag": tag,
            "server": n["host"],
            "server_port": n["port"],
            "uuid": n.get("uuid"),
            "flow": params.get("flow") or ("xtls-rprx-vision" if reality else None),
            "tls": {
                "enabled": True,
                "server_name": sni or n["host"],
                "reality": (
                    {
                        "enabled": True,
                        "public_key": params.get("pbk") or params.get("public_key"),
                        "short_id": params.get("sid") or params.get("short_id"),
                    }
                    if reality
                    else None
                ),
                "utls": (
                    {"enabled": True, "fingerprint": params.get("fp")} if params.get("fp") else None
                ),
            },
            "transport": {
                "type": params.get("type") or params.get("net") or "tcp",
                "path": params.get("path"),
            },
        }
        return json.loads(json.dumps(ob))
    if proto == "trojan":
        return {
            "type": "trojan",
            "tag": tag,
            "server": n["host"],
            "server_port": n["port"],
            "password": n.get("password"),
            "tls": {"enabled": True, "server_name": sni or n["host"]},
            "transport": {"type": params.get("type") or params.get("net") or "tcp"},
        }
    if proto == "vmess":
        return {
            "type": "vmess",
            "tag": tag,
            "server": n["host"],
            "server_port": n["port"],
            "uuid": n.get("uuid"),
            "security": params.get("scy") or "auto",
            "tls": {"enabled": params.get("tls") == "tls", "server_name": sni or n["host"]},
            "transport": {"type": params.get("net") or "tcp", "path": params.get("path")},
        }
    if proto == "ss":
        return {
            "type": "shadowsocks",
            "tag": tag,
            "server": n["host"],
            "server_port": n["port"] or 8388,
            "method": (params or {}).get("method"),
            "password": n.get("password"),
        }
    return params


async def export_singbox(limit: int = 200):
    raw = await get_nodes_json(limit=limit)
    outbounds = [to_singbox_outbound(n) for n in raw]
    return {"log": {"level": "info"}, "outbounds": outbounds}


async def subscription_txt(limit: int = 200, base64out: bool = True):
    data = await get_nodes_json(limit=limit)
    text = "\n".join(n["link"] for n in data)
    if base64out:
        return {"base64": base64.b64encode(text.encode()).decode()}
    return {"raw": text}


