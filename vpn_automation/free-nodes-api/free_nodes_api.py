# Free Nodes Aggregator API — FastAPI single‑file
# ------------------------------------------------
# What this service does
# - Accepts pasted/free links (vless://, vmess://, trojan://, ss://) and normalizes them
# - Optionally fetches links from simple HTTP sources you specify (plain text, one per line)
# - De‑dupes, lightly scores, & (optionally) health‑checks via TCP connect latency
# - Serves a clean JSON for your UI: GET /api/nodes.json
# - Exports outbounds‑only sing‑box JSON & raw subscription text
# - Simple in‑memory rate‑limit & CORS enabled (dev‑friendly)
#
# Run:
#   pip install fastapi uvicorn[standard] pydantic httpx
#   uvicorn free_nodes_api:app --host 0.0.0.0 --port 8000 --reload
#
# Then in the React helper, set API base to http://localhost:8000 and click "Fetch from API".

from __future__ import annotations

import asyncio
import base64
import json
import random
import re
import time
from urllib.parse import parse_qs, unquote, urlparse

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

# ------------------------------ Config ------------------------------------
RATE_LIMIT_REQUESTS_PER_MINUTE = 120
HEALTHCHECK_CONCURRENCY = 50
CONNECT_TIMEOUT = 2.5  # seconds
STORE_CAP = 5000  # max nodes kept

# ------------------------------ App ---------------------------------------
app = FastAPI(title="Free Nodes Aggregator API", version="1.0.0")

# ---- Observability: HTTP metrics and /metrics endpoint
Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    excluded_handlers={"/metrics"},
    inprogress_name="http_requests_in_progress",
    inprogress_labels=True,
).instrument(app).expose(app, include_in_schema=False)

# ---- Custom metrics
NODES_PROCESSED = Counter(
    "nodes_processed_total",
    "Total nodes parsed/merged by background workers",
    labelnames=("source", "result"),
)

FETCH_DURATION = Histogram(
    "node_fetch_duration_seconds",
    "Duration of source fetch and parse",
    labelnames=("source",),
    buckets=(0.1, 0.3, 0.5, 1, 2, 5, 10),
)

QUALITY_SCORE = Gauge(
    "node_quality_score",
    "Latest quality score for a node",
    labelnames=("proto", "region"),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------ Models ------------------------------------
class Node(BaseModel):
    proto: str
    host: str
    port: int
    name: str
    link: str
    uuid: str | None = None
    password: str | None = None
    params: dict = Field(default_factory=dict)
    latency_ms: int | None = None
    healthy: bool | None = None
    score: float | None = None
    last_checked: float | None = None

    def key(self) -> str:
        token = self.uuid or self.password or self.name
        return f"{self.proto}|{self.host}|{self.port}|{token}"


class IngestBody(BaseModel):
    links: list[str] = Field(default_factory=list, description="List of proxy share links")


class SourcesBody(BaseModel):
    urls: list[str] = Field(
        default_factory=list, description="List of http(s) URLs; each returns text lines of links"
    )


# ------------------------------ Store -------------------------------------
class NodeStore:
    def __init__(self):
        self.map: dict[str, Node] = {}
        self.sources: list[str] = []
        self.lock = asyncio.Lock()

    def _evict_if_needed(self):
        if len(self.map) <= STORE_CAP:
            return
        # drop lowest-score / oldest first
        items = list(self.map.items())
        items.sort(key=lambda kv: (kv[1].score or 0.0, kv[1].last_checked or 0.0))
        to_drop = len(self.map) - STORE_CAP
        for k, _ in items[:to_drop]:
            self.map.pop(k, None)

    async def upsert_many(self, nodes: list[Node]):
        async with self.lock:
            for n in nodes:
                self.map[n.key()] = n
            self._evict_if_needed()

    async def all(self) -> list[Node]:
        async with self.lock:
            return list(self.map.values())

    async def add_sources(self, urls: list[str]):
        async with self.lock:
            for u in urls:
                if u not in self.sources:
                    self.sources.append(u)


STORE = NodeStore()


# --------------------------- Rate limiting ---------------------------------
class RateBucket:
    def __init__(self):
        self.count = 0
        self.reset_at = time.time() + 60


RATE: dict[str, RateBucket] = {}


def rate_limit_ok(ip: str) -> bool:
    b = RATE.get(ip)
    now = time.time()
    if not b or now >= b.reset_at:
        RATE[ip] = RateBucket()
        return True
    if b.count >= RATE_LIMIT_REQUESTS_PER_MINUTE:
        return False
    return True


@app.middleware("http")
async def ratelimit_mw(request: Request, call_next):
    ip = request.client.host if request.client else "0.0.0.0"
    if not rate_limit_ok(ip):
        raise HTTPException(status_code=429, detail="Too many requests; slow down")
    # increment after check
    RATE[ip].count += 1
    return await call_next(request)


# ------------------------------ Parsing -----------------------------------


def _b64decode_safe(b64: str) -> str:
    try:
        b64 = b64.replace("-", "+").replace("_", "/")
        pad = len(b64) % 4
        if pad:
            b64 += "=" * (4 - pad)
        return base64.b64decode(b64).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def parse_vless(link: str) -> Node | None:
    try:
        u = urlparse(link)
        qp = {k: v[0] for k, v in parse_qs(u.query).items()}
        name = unquote(u.fragment) or f"VLESS {u.hostname}"
        return Node(
            proto="vless",
            host=u.hostname or "",
            port=int(u.port or 443),
            name=name,
            link=link,
            uuid=unquote(u.username) if u.username else None,
            params=qp,
        )
    except Exception:
        return None


def parse_vmess(link: str) -> Node | None:
    try:
        b64 = link.split("vmess://", 1)[1]
        raw = _b64decode_safe(b64)
        obj = json.loads(raw)
        sni = obj.get("sni") or obj.get("host")
        name = obj.get("ps") or f"VMESS {obj.get('add')}"
        return Node(
            proto="vmess",
            host=obj.get("add", ""),
            port=int(obj.get("port", 443)),
            name=name,
            link=link,
            uuid=obj.get("id"),
            params={
                "net": obj.get("net"),
                "type": obj.get("type"),
                "tls": obj.get("tls"),
                "sni": sni,
                "path": obj.get("path"),
                "alpn": obj.get("alpn"),
                "scy": obj.get("scy"),
            },
        )
    except Exception:
        return None


def parse_trojan(link: str) -> Node | None:
    try:
        u = urlparse(link)
        qp = {k: v[0] for k, v in parse_qs(u.query).items()}
        name = unquote(u.fragment) or f"TROJAN {u.hostname}"
        pwd = unquote(u.username) if u.username else None
        return Node(
            proto="trojan",
            host=u.hostname or "",
            port=int(u.port or 443),
            name=name,
            link=link,
            password=pwd,
            params=qp,
        )
    except Exception:
        return None


def parse_ss(link: str) -> Node | None:
    try:
        raw = link.split("ss://", 1)[1]
        if "@" in raw:
            creds, tail = raw.split("@", 1)
        else:
            # base64 credentials then @host:port
            before_hash = raw.split("#", 1)[0]
            decoded = _b64decode_safe(before_hash)
            if "@" not in decoded:
                return None
            creds, tail = decoded.split("@", 1)
        method, password = creds.split(":", 1)
        host = tail.split(":", 1)[0]
        port = re.split(r"[:/?#]", tail)[1]
        name = unquote(raw.split("#", 1)[1]) if "#" in raw else f"SS {host}"
        return Node(
            proto="ss",
            host=host,
            port=int(port or 8388),
            name=name,
            link=link,
            password=password,
            params={"method": method},
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
    # Basic sing-box outbound JSON line support
    try:
        obj = json.loads(s)
        if isinstance(obj, dict) and obj.get("type") and obj.get("server"):
            host = obj.get("server")
            port = int(obj.get("server_port") or obj.get("port") or 443)
            tag = obj.get("tag") or f"{obj['type'].upper()} {host}"
            # Craft a pseudo-link for QR/export parity
            link = f"{obj['type']}://{host}:{port}#{tag}"
            return Node(
                proto=obj.get("type"),
                host=host,
                port=port,
                name=tag,
                link=link,
                uuid=obj.get("uuid"),
                params=obj,
            )
    except Exception:
        pass
    return None


# ---------------------------- Scoring/Health -------------------------------


def score_node(n: Node) -> float:
    score = 0.0
    if n.port in (443, 8443):
        score += 1.2
    tlsish = (
        n.proto == "vless"
        and (n.params.get("security") == "reality" or n.params.get("reality", {}).get("enabled"))
    ) or (n.params.get("tls") == "tls")
    if tlsish:
        score += 1.0
    if n.latency_ms is not None:
        score += max(0.0, 1.0 - min(1000, n.latency_ms) / 1000.0)
    return round(score, 3)


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
        dur = (time.perf_counter() - start) * 1000
        return int(dur)
    except Exception:
        return None


async def healthcheck_nodes(nodes: list[Node]):
    sem = asyncio.Semaphore(HEALTHCHECK_CONCURRENCY)

    async def one(n: Node):
        async with sem:
            lat = await tcp_latency(n.host, n.port)
            n.latency_ms = lat
            n.healthy = lat is not None
            n.last_checked = time.time()
            n.score = score_node(n)

    await asyncio.gather(*(one(n) for n in nodes))


# ----------------------------- Converters ----------------------------------


def to_singbox_outbound(n: Node) -> dict:
    sni = n.params.get("sni") or n.params.get("server_name")
    tag = re.sub(r"\s+", "-", n.name).lower()
    if n.proto == "vless":
        reality = n.params.get("security") == "reality" or (n.params.get("reality") or {}).get(
            "enabled"
        )
        outbound = {
            "type": "vless",
            "tag": tag,
            "server": n.host,
            "server_port": n.port or 443,
            "uuid": n.uuid,
            "flow": n.params.get("flow") or ("xtls-rprx-vision" if reality else None),
            "tls": {
                "enabled": True,
                "server_name": sni or n.host,
                "reality": (
                    {
                        "enabled": True,
                        "public_key": n.params.get("pbk") or n.params.get("public_key"),
                        "short_id": n.params.get("sid") or n.params.get("short_id"),
                    }
                    if reality
                    else None
                ),
                "utls": (
                    {"enabled": True, "fingerprint": n.params.get("fp")}
                    if n.params.get("fp")
                    else None
                ),
            },
            "transport": {
                "type": n.params.get("type") or n.params.get("net") or "tcp",
                "path": n.params.get("path"),
            },
        }
        # remove Nones
        return json.loads(json.dumps(outbound))
    if n.proto == "trojan":
        return {
            "type": "trojan",
            "tag": tag,
            "server": n.host,
            "server_port": n.port or 443,
            "password": n.password,
            "tls": {"enabled": True, "server_name": sni or n.host},
            "transport": {"type": n.params.get("type") or n.params.get("net") or "tcp"},
        }
    if n.proto == "vmess":
        return {
            "type": "vmess",
            "tag": tag,
            "server": n.host,
            "server_port": n.port or 443,
            "uuid": n.uuid,
            "security": n.params.get("scy") or "auto",
            "tls": {"enabled": n.params.get("tls") == "tls", "server_name": sni or n.host},
            "transport": {"type": n.params.get("net") or "tcp", "path": n.params.get("path")},
        }
    if n.proto == "ss":
        return {
            "type": "shadowsocks",
            "tag": tag,
            "server": n.host,
            "server_port": n.port or 8388,
            "method": (n.params or {}).get("method"),
            "password": n.password,
        }
    return n.params or {}


# ------------------------------ Helpers ------------------------------------
async def _fetch_text(url: str, timeout: float = 10.0) -> str:
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text


def _normalize_lines_to_nodes(text: str) -> list[Node]:
    nodes: list[Node] = []
    for line in text.splitlines():
        n = parse_any(line)
        if n:
            n.score = score_node(n)
            nodes.append(n)
    return nodes


# ------------------------------ Routes -------------------------------------
@app.get("/health")
async def health():
    return {"ok": True, "service": "free-nodes-api"}


@app.post("/api/ingest")
async def ingest(body: IngestBody):
    if not body.links:
        raise HTTPException(400, detail="No links provided")
    nodes = []
    for s in body.links:
        n = parse_any(s)
        if n:
            n.score = score_node(n)
            nodes.append(n)
    await STORE.upsert_many(nodes)
    return {"ingested": len(nodes), "total": len(await STORE.all())}


@app.post("/api/sources")
async def add_sources(body: SourcesBody):
    if not body.urls:
        raise HTTPException(400, detail="No URLs provided")
    # Very light validation
    for u in body.urls:
        if not u.startswith("http://") and not u.startswith("https://"):
            raise HTTPException(400, detail=f"Invalid URL: {u}")
    await STORE.add_sources(body.urls)
    return {"sources": len(STORE.sources)}


@app.post("/api/refresh")
async def refresh_sources(healthcheck: bool = True):
    if not STORE.sources:
        return {"fetched": 0, "note": "No sources configured"}
    collected: list[Node] = []
    for url in STORE.sources:
        try:
            t0 = time.perf_counter()
            text = await _fetch_text(url)
            collected.extend(_normalize_lines_to_nodes(text))
            FETCH_DURATION.labels(source=url).observe(time.perf_counter() - t0)
            NODES_PROCESSED.labels(source=url, result="success").inc()
        except Exception as e:
            # best-effort: skip failures
            print(f"fetch error {url}: {e}")
            NODES_PROCESSED.labels(source=url, result="error").inc()
    # de-dupe by key (latest wins)
    by_key: dict[str, Node] = {}
    for n in collected:
        by_key[n.key()] = n
    nodes = list(by_key.values())
    if healthcheck and nodes:
        await healthcheck_nodes(nodes)
    await STORE.upsert_many(nodes)
    return {"fetched": len(nodes), "total": len(await STORE.all())}


@app.get("/api/nodes.json")
async def get_nodes(limit: int = 200, proto: str | None = None, sort: str = "score"):
    nodes = await STORE.all()
    if proto:
        nodes = [n for n in nodes if n.proto == proto]
    # compute score if missing
    for n in nodes:
        if n.score is None:
            n.score = score_node(n)
    if sort == "latency":
        nodes.sort(key=lambda n: (n.latency_ms is None, n.latency_ms or 1e9))
    elif sort == "random":
        random.shuffle(nodes)
    else:
        nodes.sort(key=lambda n: (n.score or 0.0), reverse=True)
    out = [n.dict() for n in nodes[: max(1, min(limit, 1000))]]
    return out


@app.get("/api/subscription.txt")
async def subscription_txt(limit: int = 200, base64out: bool = True):
    nodes = await get_nodes(limit=limit)
    text = "\n".join(n["link"] for n in nodes)  # type: ignore
    if base64out:
        b = base64.b64encode(text.encode()).decode()
        return {"base64": b}
    return {"raw": text}


@app.get("/api/export/singbox.json")
async def export_singbox(limit: int = 200):
    raw = await get_nodes(limit=limit)
    outbounds = [to_singbox_outbound(Node(**n)) for n in raw]  # type: ignore
    conf = {"log": {"level": "info"}, "outbounds": outbounds}
    return conf


@app.post("/api/ping")
async def ping_nodes(body: IngestBody):
    # Measure TCP connect latency for provided links (not stored, unless you ingest separately)
    targets: list[Node] = []
    for s in body.links:
        n = parse_any(s)
        if n:
            targets.append(n)
    await healthcheck_nodes(targets)
    return [n.dict() for n in targets]


# --------------------------- Dev bootstrap ---------------------------------
@app.on_event("startup")
async def bootstrap_sample():
    # Seed with a tiny sample so the UI has something to show
    sample = [
        "vless://11111111-2222-3333-4444-555555555555@example.com:443?security=reality&pbk=PUBKEY&sid=abcdef&sni=www.microsoft.com&type=tcp#Sample-REALITY",
        "vmess://"
        + base64.b64encode(
            json.dumps(
                {
                    "v": "2",
                    "ps": "Sample-VMESS",
                    "add": "vmess.example.com",
                    "port": "443",
                    "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "net": "tcp",
                    "type": "none",
                    "tls": "tls",
                    "sni": "www.cloudflare.com",
                    "path": "/",
                }
            ).encode()
        ).decode(),
        "trojan://pass123@trojan.example.com:443#Sample-Trojan",
        "ss://"
        + base64.b64encode(b"chacha20-ietf-poly1305:passw0rd@ss.example.com:8388").decode()
        + "#Sample-SS",
    ]
    await ingest(IngestBody(links=sample))
