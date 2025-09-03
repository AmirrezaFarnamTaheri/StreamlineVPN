#!/usr/bin/env python3
"""
Minimal Subscription Facade — FastAPI (single‑file)
===================================================
Purpose
  • Serve merged/cleaned VPN nodes (free/public or custom) via simple JSON/YAML endpoints
  • Export formats: raw list, Sing-Box outbounds JSON, Clash.Meta YAML
  • Optional health checks (TCP connect latency) and simple scoring/sorting
  • CORS-enabled so the React "Universal Client & QR" can fetch from it directly
  • Lightweight, in‑memory cache + per‑IP rate limiting; optional API key

Quick start
  pip install fastapi uvicorn
  python app.py  # (or) uvicorn app:app --host 0.0.0.0 --port 8000

Optional deps
  pip install pyyaml qrcode

Environment variables
  PORT=8000
  API_KEY=  (if set, required for mutating endpoints; supply via X-API-Key or ?key=)
  CORS_ALLOW_ORIGINS=*  (comma separated)
  CACHE_TTL_SECONDS=600
  RATE_LIMIT_REQUESTS=120
  RATE_LIMIT_WINDOW_SEC=60

Endpoints (all GET unless stated)
  /                        → HTML usage
  /health                  → service stats
  POST /api/ingest         → add links (body: {links: string|[string], replace?: bool})
  /api/nodes.txt           → raw links (limit, proto, sort, health)
  /api/nodes.json          → normalized nodes as JSON (limit, proto, sort, health)
  /api/sub/singbox.json    → { outbounds: [...] } (limit, proto, sort, health)
  /api/sub/clash.yaml      → Clash.Meta YAML (proxies + basic groups)

Notes
  • This is a demo-grade façade: it stores everything in memory. Persist/redisify if needed.
  • Health checks use TCP connect timing — cheap, not a full throughput test.
  • Scoring prefers :443, TLS/REALITY, and low measured latency (if any).
"""
from __future__ import annotations

import asyncio
import base64
import builtins
import os
import re
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from typing import Any

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

try:
    from prometheus_client import Counter, Histogram
    from prometheus_fastapi_instrumentator import Instrumentator
except Exception:  # pragma: no cover

    class _Noop:
        def __getattr__(self, *_):
            return self

        def __call__(self, *a, **k):
            return self

    Instrumentator = _Noop()  # type: ignore

    class Counter:  # type: ignore
        def __init__(self, *a, **k):
            pass

        def inc(self, *a, **k):
            pass

    class Histogram:  # type: ignore
        def __init__(self, *a, **k):
            pass

        def observe(self, *a, **k):
            pass


try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

# -------------------------------------------------------------
# Config
# -------------------------------------------------------------
PORT = int(os.getenv("PORT", "8000"))
API_KEY = os.getenv("API_KEY")
CORS_ALLOW = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if o.strip()]
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "600"))
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "120"))
RATE_LIMIT_WINDOW_SEC = int(os.getenv("RATE_LIMIT_WINDOW_SEC", "60"))


# -------------------------------------------------------------
# Models
# -------------------------------------------------------------
@dataclass
class Node:
    proto: str
    host: str
    port: int
    name: str
    raw: str
    uuid: str | None = None
    password: str | None = None
    params: dict[str, Any] | None = None
    latency_ms: float | None = None  # last measured
    healthy: bool | None = None

    @property
    def key(self) -> str:
        return f"{self.proto}|{self.host}|{self.port}|{self.uuid or self.password or self.name}"


# -------------------------------------------------------------
# Utilities — parsing & transforms (mirrors the React helper)
# -------------------------------------------------------------
B64_SAFE_RE = re.compile(r"[^A-Za-z0-9_\-=]")


def b64_decode_safe(b64: str) -> str:
    try:
        b64 = b64.replace("-", "+").replace("_", "/")
        pad = len(b64) % 4
        if pad:
            b64 += "=" * (4 - pad)
        return base64.b64decode(b64).decode("utf-8", "ignore")
    except Exception:
        return ""


def parse_qs(qs: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if qs.startswith("?"):
        qs = qs[1:]
    for kv in qs.split("&"):
        if not kv:
            continue
        if "=" in kv:
            k, v = kv.split("=", 1)
        else:
            k, v = kv, ""
        try:
            out[
                re.sub(
                    r"\+", " ", re.sub(r"%([0-9A-Fa-f]{2})", lambda m: chr(int(m.group(1), 16)), k)
                )
            ] = re.sub(
                r"\+", " ", re.sub(r"%([0-9A-Fa-f]{2})", lambda m: chr(int(m.group(1), 16)), v)
            )
        except Exception:
            out[k] = v
    return out


def parse_vless(url: str) -> Node | None:
    try:
        from urllib.parse import urlparse

        u = urlparse(url)
        qp = parse_qs(u.query)
        name = u.fragment or f"VLESS {u.hostname}"
        return Node(
            proto="vless",
            uuid=(u.username or ""),
            host=u.hostname or "",
            port=int(u.port or 443),
            name=name,
            params=qp,
            raw=url,
        )
    except Exception:
        return None


def parse_vmess(url: str) -> Node | None:
    try:
        raw = url.replace("vmess://", "", 1)
        doc = b64_decode_safe(raw)
        j = {}
        import json

        j = json.loads(doc)
        name = j.get("ps") or f"VMESS {j.get('add')}"
        return Node(
            proto="vmess",
            uuid=j.get("id"),
            host=j.get("add"),
            port=int(j.get("port") or 443),
            name=name,
            params={
                "net": j.get("net"),
                "type": j.get("type"),
                "tls": j.get("tls"),
                "sni": j.get("sni") or j.get("host"),
                "path": j.get("path"),
                "alpn": j.get("alpn"),
                "scy": j.get("scy"),
            },
            raw=url,
        )
    except Exception:
        return None


def parse_trojan(url: str) -> Node | None:
    try:
        from urllib.parse import unquote, urlparse

        u = urlparse(url)
        name = unquote(u.fragment) if u.fragment else f"TROJAN {u.hostname}"
        return Node(
            proto="trojan",
            password=(unquote(u.username or "")),
            host=u.hostname or "",
            port=int(u.port or 443),
            name=name,
            params=parse_qs(u.query),
            raw=url,
        )
    except Exception:
        return None


def parse_ss(url: str) -> Node | None:
    try:
        from urllib.parse import unquote

        s = url.replace("ss://", "", 1)
        if "@" in s:
            creds, hostpart = s.split("@", 1)
        else:
            # ss://base64(method:pass)@host:port
            before_hash = s.split("#", 1)[0]
            decoded = b64_decode_safe(before_hash)
            if "@" not in decoded:
                return None
            creds, hostpart = decoded.split("@", 1)
        method, password = creds.split(":", 1)
        host = re.split(r"[:/?#]", hostpart)[0]
        import re as _re

        port_search = _re.search(r":(\d+)", hostpart)
        port = int(port_search.group(1)) if port_search else 8388
        name = unquote(s.split("#", 1)[1]) if "#" in s else f"SS {host}"
        return Node(
            proto="ss",
            host=host,
            port=port,
            name=name,
            raw=url,
            params={"method": method},
            password=password,
        )
    except Exception:
        return None


def parse_any(line: str) -> Node | None:
    s = line.strip()
    if not s:
        return None
    if s.startswith("vless://"):
        return parse_vless(s)
    if s.startswith("vmess://"):
        return parse_vmess(s)
    if s.startswith("trojan://"):
        return parse_trojan(s)
    if s.startswith("ss://"):
        return parse_ss(s)
    # Attempt to accept simple sing-box outbound JSON
    try:
        import json

        obj = json.loads(s)
        if isinstance(obj, dict) and obj.get("type") and obj.get("server"):
            return Node(
                proto=obj.get("type"),
                host=obj.get("server"),
                port=int(obj.get("server_port") or obj.get("port") or 443),
                name=obj.get("tag") or f"{obj.get('type').upper()} {obj.get('server')}",
                raw=s,
                uuid=obj.get("uuid"),
                params=obj,
            )
    except Exception:
        pass
    return None


# -------------------------------------------------------------
# Transforms — Sing-Box & Clash
# -------------------------------------------------------------


def to_singbox_outbound(n: Node) -> dict[str, Any]:
    sni = (n.params or {}).get("sni") or (n.params or {}).get("server_name")
    import re as _re

    tag = _re.sub(r"\s+", "-", n.name or "node").lower()
    if n.proto == "vless":
        is_reality = ((n.params or {}).get("security") == "reality") or (
            (n.params or {}).get("reality", {}).get("enabled")
        )
        out = {
            "type": "vless",
            "tag": tag,
            "server": n.host,
            "server_port": n.port or 443,
            "uuid": n.uuid,
            "flow": (n.params or {}).get("flow") or ("xtls-rprx-vision" if is_reality else None),
            "tls": {
                "enabled": True,
                "server_name": sni or n.host,
                "reality": (
                    {
                        "enabled": True,
                        "public_key": (n.params or {}).get("pbk")
                        or (n.params or {}).get("public_key"),
                        "short_id": (n.params or {}).get("sid") or (n.params or {}).get("short_id"),
                    }
                    if is_reality
                    else None
                ),
                "utls": (
                    {"enabled": True, "fingerprint": (n.params or {}).get("fp")}
                    if (n.params or {}).get("fp")
                    else None
                ),
            },
            "transport": {
                "type": (n.params or {}).get("type") or (n.params or {}).get("net") or "tcp",
                "path": (n.params or {}).get("path"),
            },
        }
        return {k: v for k, v in out.items() if v is not None}
    if n.proto == "trojan":
        return {
            "type": "trojan",
            "tag": tag,
            "server": n.host,
            "server_port": n.port or 443,
            "password": n.password,
            "tls": {"enabled": True, "server_name": sni or n.host},
            "transport": {
                "type": (n.params or {}).get("type") or (n.params or {}).get("net") or "tcp"
            },
        }
    if n.proto == "vmess":
        return {
            "type": "vmess",
            "tag": tag,
            "server": n.host,
            "server_port": n.port or 443,
            "uuid": n.uuid,
            "security": (n.params or {}).get("scy") or "auto",
            "tls": {
                "enabled": ((n.params or {}).get("tls") == "tls"),
                "server_name": sni or n.host,
            },
            "transport": {
                "type": (n.params or {}).get("net") or "tcp",
                "path": (n.params or {}).get("path"),
            },
        }
    if n.proto == "ss":
        return {
            "type": "shadowsocks",
            "tag": tag,
            "server": n.host,
            "server_port": n.port or 8388,
            "method": (n.params or {}).get("method") or "chacha20-ietf-poly1305",
            "password": n.password,
        }
    return n.params or {}


def to_clash_proxy(n: Node) -> dict[str, Any]:
    base = {"name": n.name, "server": n.host, "port": n.port}
    if n.proto == "vmess":
        p = {
            **base,
            "type": "vmess",
            "uuid": n.uuid,
            "security": (n.params or {}).get("scy") or "auto",
            "tls": ((n.params or {}).get("tls") == "tls"),
            "servername": (n.params or {}).get("sni") or n.host,
            "network": (n.params or {}).get("net") or "tcp",
            "ws-opts": {"path": (n.params or {}).get("path")},
        }
        return p
    if n.proto == "vless":
        is_reality = (n.params or {}).get("security") == "reality"
        p = {
            **base,
            "type": "vless",
            "uuid": n.uuid,
            "tls": True,
            "servername": (n.params or {}).get("sni") or n.host,
            "network": (n.params or {}).get("net") or (n.params or {}).get("type") or "tcp",
        }
        if is_reality:
            p["flow"] = (n.params or {}).get("flow") or "xtls-rprx-vision"
            p["reality-opts"] = {
                "public-key": (n.params or {}).get("pbk"),
                "short-id": (n.params or {}).get("sid"),
            }
        if (n.params or {}).get("path"):
            p["ws-opts"] = {"path": (n.params or {}).get("path")}
        return p
    if n.proto == "trojan":
        return {
            **base,
            "type": "trojan",
            "password": n.password,
            "sni": (n.params or {}).get("sni") or (n.params or {}).get("server_name") or n.host,
        }
    if n.proto == "ss":
        return {
            **base,
            "type": "ss",
            "cipher": (n.params or {}).get("method") or "chacha20-ietf-poly1305",
            "password": n.password,
        }
    return {**base, "type": n.proto}


# -------------------------------------------------------------
# Scoring & latency
# -------------------------------------------------------------


def score_node(n: Node) -> float:
    score = 0.0
    if n.port in (443, 8443):
        score += 1.2
    if n.proto == "vless" and (
        ((n.params or {}).get("security") == "reality") or (n.params or {}).get("reality")
    ):
        score += 1.4
    if (n.params or {}).get("tls") == "tls":
        score += 0.6
    if n.latency_ms is not None:
        score += max(0.0, 1.0 - min(1000.0, n.latency_ms) / 1000.0)
    return score


async def tcp_ping(host: str, port: int, timeout: float = 2.0) -> float | None:
    start = time.perf_counter()
    try:
        await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
        return (time.perf_counter() - start) * 1000.0
    except Exception:
        return None


# -------------------------------------------------------------
# Store, cache, rate limit, metrics
# -------------------------------------------------------------
class Store:
    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.last_health_ts: float = 0.0

    def ingest(self, links: builtins.list[str], replace: bool = False) -> int:
        if replace:
            self.nodes.clear()
        count = 0
        for line in links:
            n = parse_any(line)
            if n and n.host:
                self.nodes[n.key] = n
                count += 1
        return count

    def list(self) -> builtins.list[Node]:
        return list(self.nodes.values())


STORE = Store()


class RateLimiter:
    def __init__(self, max_req: int, window_sec: int):
        self.max_req = max_req
        self.window = window_sec
        self._hits: dict[str, deque] = defaultdict(deque)

    def check(self, ip: str) -> bool:
        now = time.time()
        dq = self._hits[ip]
        while dq and now - dq[0] > self.window:
            dq.popleft()
        if len(dq) >= self.max_req:
            return False
        dq.append(now)
        return True


limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SEC)


async def require_api_key(x_api_key: str | None = Header(None), request: Request = None):
    if API_KEY:
        provided = x_api_key or request.query_params.get("key")
        if provided != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")


def require_rate_limit(request: Request):
    ip = request.client.host if request.client else "anon"
    if not limiter.check(ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


# -------------------------------------------------------------
# App & Middleware
# -------------------------------------------------------------
app = FastAPI(title="Minimal Subscription Facade")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW if CORS_ALLOW != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus /metrics and HTTP metrics
Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    excluded_handlers={"/metrics"},
    inprogress_name="http_requests_in_progress",
    inprogress_labels=True,
).instrument(app).expose(app, include_in_schema=False)

NODES_INGESTED = Counter(
    "facade_nodes_ingested_total",
    "Total nodes ingested",
)
HEALTH_DURATION = Histogram(
    "facade_health_latency_seconds",
    "Latency to run health checks on a batch",
    buckets=(0.05, 0.1, 0.3, 0.5, 1, 2, 5),
)


# -------------------------------------------------------------
# Helpers for formatting responses
# -------------------------------------------------------------
async def maybe_health(nodes: list[Node], do_health: bool, max_probe: int = 50):
    if not do_health:
        return nodes
    sample = nodes[:max_probe]
    t0 = time.perf_counter()
    tasks = [tcp_ping(n.host, n.port) for n in sample]
    results = await asyncio.gather(*tasks)
    for n, lat in zip(sample, results, strict=False):
        n.latency_ms = lat if lat is not None else None
        n.healthy = lat is not None
    HEALTH_DURATION.observe(time.perf_counter() - t0)
    return nodes


def filter_sort(nodes: list[Node], proto: str, limit: int, sort: str) -> list[Node]:
    filtered = [n for n in nodes if (proto == "all" or n.proto == proto)]
    if sort == "score":
        filtered.sort(key=lambda n: score_node(n), reverse=True)
    elif sort == "latency":
        filtered.sort(key=lambda n: (n.latency_ms if n.latency_ms is not None else 1e9))
    else:
        filtered.sort(key=lambda n: n.name)
    return filtered[: max(1, min(limit, 500))]


# -------------------------------------------------------------
# Routes
# -------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return (
        "<h1>Minimal Subscription Facade</h1>"
        "<p>Use <code>/api/ingest</code> to POST links, then fetch <code>/api/nodes.json</code> or subscriptions."
        " See <code>/health</code> for status.</p>"
    )


@app.get("/health")
async def health(request: Request):
    require_rate_limit(request)
    return {
        "status": "ok",
        "count": len(STORE.nodes),
        "rate_limit": {"max": RATE_LIMIT_REQUESTS, "window_sec": RATE_LIMIT_WINDOW_SEC},
        "cache_ttl_sec": CACHE_TTL_SECONDS,
        "time": int(time.time()),
    }


@app.post("/api/ingest")
async def ingest(
    request: Request,
    payload: dict[str, Any] = Body(...),
    _auth: None = Depends(require_api_key),
):
    require_rate_limit(request)
    links: list[str]
    body_links = payload.get("links")
    if isinstance(body_links, str):
        import re as _re

        links = [s for s in _re.split(r"\r?\n", body_links) if s.strip()]
    elif isinstance(body_links, list):
        links = [str(x) for x in body_links if str(x).strip()]
    else:
        raise HTTPException(status_code=400, detail="links must be string or array")
    replace = bool(payload.get("replace", False))
    count = STORE.ingest(links, replace=replace)
    if count:
        NODES_INGESTED.inc(count)
    return {"ingested": count, "total": len(STORE.nodes)}


@app.get("/api/nodes.txt")
async def nodes_txt(
    request: Request,
    proto: str = Query("all", pattern=r"^(all|vless|vmess|trojan|ss)$"),
    limit: int = Query(100),
    sort: str = Query("score", pattern=r"^(score|latency|name)$"),
    health: bool = Query(False),
):
    require_rate_limit(request)
    nodes = STORE.list()
    if health:
        nodes = await maybe_health(nodes, True)
    nodes = filter_sort(nodes, proto, limit, sort)
    text = "\n".join([n.raw for n in nodes])
    return PlainTextResponse(text)


@app.get("/api/nodes.json")
async def nodes_json(
    request: Request,
    proto: str = Query("all", pattern=r"^(all|vless|vmess|trojan|ss)$"),
    limit: int = Query(100),
    sort: str = Query("score", pattern=r"^(score|latency|name)$"),
    health: bool = Query(False),
):
    require_rate_limit(request)
    nodes = STORE.list()
    if health:
        nodes = await maybe_health(nodes, True)
    nodes = filter_sort(nodes, proto, limit, sort)
    data = []
    for n in nodes:
        d = asdict(n)
        d["score"] = score_node(n)
        data.append(d)
    return JSONResponse(data)


@app.get("/api/sub/singbox.json")
async def sub_singbox(
    request: Request,
    proto: str = Query("all", pattern=r"^(all|vless|vmess|trojan|ss)$"),
    limit: int = Query(50),
    sort: str = Query("score", pattern=r"^(score|latency|name)$"),
    health: bool = Query(False),
):
    require_rate_limit(request)
    nodes = STORE.list()
    if health:
        nodes = await maybe_health(nodes, True)
    nodes = filter_sort(nodes, proto, limit, sort)
    outbounds = [to_singbox_outbound(n) for n in nodes]
    payload = {"log": {"level": "info"}, "outbounds": outbounds}
    return JSONResponse(payload)


def to_clash_yaml(nodes: list[Node]) -> str:
    proxies = [to_clash_proxy(n) for n in nodes]
    proxy_names = [p.get("name") for p in proxies]
    doc = {
        "proxies": proxies,
        "proxy-groups": [
            {
                "name": "Auto",
                "type": "url-test",
                "url": "https://www.gstatic.com/generate_204",
                "interval": 600,
                "tolerance": 50,
                "proxies": proxy_names,
            },
            {"name": "Manual", "type": "select", "proxies": proxy_names},
        ],
    }
    if yaml:
        return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True)
    import json

    return (
        "proxies:\n"
        + "\n".join(["  - " + json.dumps(p) for p in proxies])
        + "\nproxy-groups:\n  - name: Auto\n    type: url-test\n    url: https://www.gstatic.com/generate_204\n    interval: 600\n    tolerance: 50\n    proxies:\n"
        + "\n".join([f"      - {name}" for name in proxy_names])
        + "\n  - name: Manual\n    type: select\n    proxies:\n"
        + "\n".join([f"      - {name}" for name in proxy_names])
        + "\n"
    )


@app.get("/api/sub/clash.yaml")
async def sub_clash(
    request: Request,
    proto: str = Query("all", pattern=r"^(all|vless|vmess|trojan|ss)$"),
    limit: int = Query(50),
    sort: str = Query("score", pattern=r"^(score|latency|name)$"),
    health: bool = Query(False),
):
    require_rate_limit(request)
    nodes = STORE.list()
    if health:
        nodes = await maybe_health(nodes, True)
    nodes = filter_sort(nodes, proto, limit, sort)
    yaml_text = to_clash_yaml(nodes)
    return PlainTextResponse(yaml_text, media_type="text/yaml")


# -------------------------------------------------------------
# Bootstrap with optional seed file (./seed.txt)
# -------------------------------------------------------------
seed_path = os.getenv("SEED_FILE", "seed.txt")
if os.path.isfile(seed_path):
    try:
        with open(seed_path, encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        if lines:
            STORE.ingest(lines, replace=True)
            print(f"[Boot] Seeded {len(STORE.nodes)} nodes from {seed_path}")
    except Exception as e:
        print("[Boot] Seed failed:", e)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=False)
