from __future__ import annotations
import asyncio, base64, json, os, random, re, time, logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs, unquote

import httpx
from fastapi import FastAPI, HTTPException, Request
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    from prometheus_client import Counter, Histogram, Gauge
except Exception:  # pragma: no cover
    class _Noop:
        def __getattr__(self, *_):
            return self
        def __call__(self, *a, **k):
            return self
    Instrumentator = _Noop()  # type: ignore
    class Counter:  # type: ignore
        def __init__(self, *a, **k): pass
        def labels(self, *a, **k): return self
        def inc(self, *a, **k): pass
    class Histogram:  # type: ignore
        def __init__(self, *a, **k): pass
        def labels(self, *a, **k): return self
        def observe(self, *a, **k): pass
    class Gauge:  # type: ignore
        def __init__(self, *a, **k): pass
        def labels(self, *a, **k): return self
        def set(self, *a, **k): pass
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import (Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey, select)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ------------------------------ Config ------------------------------------
DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///./data/free-nodes.db")
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "120"))
HEALTH_CONCURRENCY = int(os.getenv("HEALTH_CONCURRENCY", "60"))
CONNECT_TIMEOUT = float(os.getenv("CONNECT_TIMEOUT", "2.5"))
STORE_CAP = int(os.getenv("STORE_CAP", "8000"))
REFRESH_EVERY_MIN = int(os.getenv("REFRESH_EVERY_MIN", "20"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("free-nodes")

# ------------------------------ App ---------------------------------------
app = FastAPI(title="Free Nodes Aggregator API", version="2.0.0")

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
    allow_origins=[o.strip() for o in CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------ DB ----------------------------------------
# Ensure data directory exists before creating engine (important for tests)
try:
    os.makedirs("./data", exist_ok=True)
except Exception:
    pass

Base = declarative_base()
engine = create_async_engine(DB_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Ensure schema exists (helpful for tests that don't trigger startup events)
_SCHEMA_READY = False

async def _ensure_schema():
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    _SCHEMA_READY = True

class NodeModel(Base):
    __tablename__ = "nodes"
    id = Column(Integer, primary_key=True)
    key = Column(String(256), unique=True, index=True)  # proto|host|port|token
    proto = Column(String(16), index=True)
    host = Column(String(255), index=True)
    port = Column(Integer, index=True)
    name = Column(String(255))
    link = Column(Text)
    uuid = Column(String(64), nullable=True)
    password = Column(String(256), nullable=True)
    params_json = Column(Text, default="{}")
    latency_ms = Column(Integer, nullable=True)
    healthy = Column(Boolean, nullable=True)
    score = Column(Float, nullable=True)
    last_checked = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SourceModel(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True)
    url = Column(String(1024), unique=True, index=True)
    added_at = Column(DateTime, default=datetime.utcnow)

class NodeMetrics(Base):
    __tablename__ = "node_metrics"
    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), unique=True, index=True)
    region = Column(String(128), nullable=True)  # e.g., US-West, EU, Asia
    latency_ms = Column(Integer, nullable=True)
    throughput_mbps = Column(Float, nullable=True)
    packet_loss = Column(Float, nullable=True)  # 0.0 - 1.0
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ------------------------------ Schemas -----------------------------------
class Node(BaseModel):
    proto: str; host: str; port: int; name: str; link: str
    uuid: Optional[str] = None; password: Optional[str] = None
    params: Dict = Field(default_factory=dict)
    latency_ms: Optional[int] = None; healthy: Optional[bool] = None
    score: Optional[float] = None; last_checked: Optional[float] = None
    def key(self) -> str:
        token = self.uuid or self.password or self.name
        return f"{self.proto}|{self.host}|{self.port}|{token}"

class IngestBody(BaseModel):
    links: List[str] = Field(default_factory=list)

class SourcesBody(BaseModel):
    urls: List[str] = Field(default_factory=list)

# --------------------------- Rate limiting ---------------------------------
class RateBucket:
    def __init__(self):
        self.count = 0; self.reset_at = time.time() + 60
RATE: Dict[str, RateBucket] = {}

def rate_limit_ok(ip: str) -> bool:
    b = RATE.get(ip); now = time.time()
    if not b or now >= b.reset_at:
        RATE[ip] = RateBucket(); return True
    return b.count < RATE_LIMIT_RPM

@app.middleware("http")
async def ratelimit_mw(request: Request, call_next):
    ip = request.client.host if request.client else "0.0.0.0"
    if not rate_limit_ok(ip):
        raise HTTPException(429, detail="Too many requests; slow down")
    RATE[ip].count += 1
    return await call_next(request)

# ------------------------------ Utils -------------------------------------

def _b64decode_safe(b64: str) -> str:
    try:
        b64 = b64.replace("-", "+").replace("_", "/"); pad = len(b64) % 4
        if pad: b64 += "=" * (4 - pad)
        return base64.b64decode(b64).decode("utf-8", errors="ignore")
    except Exception:
        return ""

def _parse_params(q: Dict[str, List[str]]):
    return {k: v[0] for k, v in q.items()}

# ---- Parsers
from urllib.parse import urlparse, parse_qs, unquote

def parse_vless(link: str) -> Optional[Node]:
    try:
        u = urlparse(link); qp = _parse_params(parse_qs(u.query))
        name = unquote(u.fragment) or f"VLESS {u.hostname}"
        return Node(proto="vless", host=u.hostname or "", port=int(u.port or 443), name=name, link=link, uuid=unquote(u.username) if u.username else None, params=qp)
    except: return None

def parse_vmess(link: str) -> Optional[Node]:
    try:
        raw = _b64decode_safe(link.split("vmess://", 1)[1]); obj = json.loads(raw)
        name = obj.get("ps") or f"VMESS {obj.get('add')}"; sni = obj.get("sni") or obj.get("host")
        return Node(proto="vmess", host=obj.get("add", ""), port=int(obj.get("port", 443)), name=name, link=link, uuid=obj.get("id"), params={"net": obj.get("net"),"type": obj.get("type"),"tls": obj.get("tls"),"sni": sni,"path": obj.get("path"),"alpn": obj.get("alpn"),"scy": obj.get("scy")})
    except: return None

def parse_trojan(link: str) -> Optional[Node]:
    try:
        u = urlparse(link); qp = _parse_params(parse_qs(u.query)); name = unquote(u.fragment) or f"TROJAN {u.hostname}"
        return Node(proto="trojan", host=u.hostname or "", port=int(u.port or 443), name=name, link=link, password=unquote(u.username) if u.username else None, params=qp)
    except: return None

def parse_ss(link: str) -> Optional[Node]:
    try:
        raw = link.split("ss://", 1)[1]
        if "@" in raw:
            creds, tail = raw.split("@", 1)
        else:
            decoded = _b64decode_safe(raw.split("#", 1)[0])
            if "@" not in decoded: return None
            creds, tail = decoded.split("@", 1)
        method, password = creds.split(":", 1)
        host = tail.split(":", 1)[0]; port = re.split(r"[:/?#]", tail)[1]
        name = unquote(raw.split("#", 1)[1]) if "#" in raw else f"SS {host}"
        return Node(proto="ss", host=host, port=int(port or 8388), name=name, link=link, password=password, params={"method": method})
    except: return None

def parse_any(line: str) -> Optional[Node]:
    s = line.strip()
    if not s: return None
    if s.startswith("vless://"): return parse_vless(s)
    if s.startswith("vmess://"): return parse_vmess(s)
    if s.startswith("trojan://"): return parse_trojan(s)
    if s.startswith("ss://"): return parse_ss(s)
    try:
        obj = json.loads(s)
        if isinstance(obj, dict) and obj.get("type") and obj.get("server"):
            host = obj.get("server"); port = int(obj.get("server_port") or obj.get("port") or 443)
            tag = obj.get("tag") or f"{obj['type'].upper()} {host}"
            link = f"{obj['type']}://{host}:{port}#{tag}"
            return Node(proto=obj.get("type"), host=host, port=port, name=tag, link=link, uuid=obj.get("uuid"), params=obj)
    except: pass
    return None

# ---- Health
async def tcp_latency(host: str, port: int) -> Optional[int]:
    try:
        start = time.perf_counter()
        conn = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(conn, timeout=CONNECT_TIMEOUT)
        writer.close();
        if hasattr(writer, "wait_closed"):
            try: await writer.wait_closed()
            except: pass
        return int((time.perf_counter() - start) * 1000)
    except: return None

def score_node(proto: str, port: int, params: Dict, latency_ms: Optional[int]) -> float:
    score = 0.0
    if port in (443, 8443): score += 1.2
    tlsish = (proto == "vless" and (params.get("security") == "reality" or (params.get("reality") or {}).get("enabled"))) or (params.get("tls") == "tls")
    if tlsish: score += 1.0
    if latency_ms is not None: score += max(0.0, 1.0 - min(1000, latency_ms) / 1000.0)
    return round(score, 3)

# ---- DB helpers
async def upsert_nodes(sess: AsyncSession, nodes: List[Node]):
    # enforce cap by dropping lowest scores if needed
    for n in nodes:
        params_json = json.dumps(n.params)
        key = n.key()
        existing = (await sess.execute(select(NodeModel).where(NodeModel.key == key))).scalar_one_or_none()
        if existing:
            existing.proto = n.proto; existing.host = n.host; existing.port = n.port
            existing.name = n.name; existing.link = n.link; existing.uuid = n.uuid; existing.password = n.password
            existing.params_json = params_json; existing.updated_at = datetime.utcnow()
            # keep existing latency/score if not set on n
        else:
            sess.add(NodeModel(key=key, proto=n.proto, host=n.host, port=n.port, name=n.name, link=n.link,
                               uuid=n.uuid, password=n.password, params_json=params_json))
    await sess.commit()

async def apply_health(sess: AsyncSession, nodes: List[NodeModel]):
    sem = asyncio.Semaphore(HEALTH_CONCURRENCY)
    async def one(m: NodeModel):
        async with sem:
            lat = await tcp_latency(m.host, m.port)
            params = json.loads(m.params_json or "{}")
            m.latency_ms = lat if lat is not None else None
            m.healthy = lat is not None
            m.score = score_node(m.proto, m.port, params, m.latency_ms)
            m.last_checked = datetime.utcnow()
    await asyncio.gather(*(one(m) for m in nodes))
    await sess.commit()

# ------------------------------ Routes -------------------------------------
@app.get("/health")
async def health(): return {"ok": True}

@app.post("/api/ingest")
async def ingest(body: IngestBody):
    await _ensure_schema()
    if not body.links: raise HTTPException(400, detail="No links provided")
    nodes = [parse_any(s) for s in body.links]
    nodes = [n for n in nodes if n]
    async with AsyncSessionLocal() as sess:
        await upsert_nodes(sess, nodes)  # type: ignore
        total = (await sess.execute(select(NodeModel))).scalars().all()
        return {"ingested": len(nodes), "total": len(total)}

@app.post("/api/sources")
async def add_sources(body: SourcesBody):
    await _ensure_schema()
    if not body.urls: raise HTTPException(400, detail="No URLs provided")
    async with AsyncSessionLocal() as sess:
        for u in body.urls:
            if not (u.startswith("http://") or u.startswith("https://")):
                raise HTTPException(400, detail=f"Invalid URL: {u}")
            exists = (await sess.execute(select(SourceModel).where(SourceModel.url == u))).scalar_one_or_none()
            if not exists: sess.add(SourceModel(url=u))
        await sess.commit()
        cnt = (await sess.execute(select(SourceModel))).scalars().all()
        return {"sources": len(cnt)}

async def _fetch_text(url: str, timeout: float = 10.0) -> str:
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url); r.raise_for_status(); return r.text

@app.post("/api/refresh")
async def refresh_sources(healthcheck: bool = True):
    await _ensure_schema()
    async with AsyncSessionLocal() as sess:
        sources = (await sess.execute(select(SourceModel))).scalars().all()
        if not sources: return {"fetched": 0, "note": "No sources configured"}
        collected: List[Node] = []
        for src in sources:
            try:
                t0 = time.perf_counter()
                text = await _fetch_text(src.url)
                for line in text.splitlines():
                    n = parse_any(line)
                    if n: collected.append(n)
                FETCH_DURATION.labels(source=src.url).observe(time.perf_counter() - t0)
                NODES_PROCESSED.labels(source=src.url, result="success").inc()
            except Exception as e:
                log.warning(f"fetch error {src.url}: {e}")
                NODES_PROCESSED.labels(source=src.url, result="error").inc()
        # de‑dupe by key
        dedup: Dict[str, Node] = {n.key(): n for n in collected}
        await upsert_nodes(sess, list(dedup.values()))
        # cap store
        all_nodes = (await sess.execute(select(NodeModel))).scalars().all()
        if len(all_nodes) > STORE_CAP:
            all_nodes.sort(key=lambda m: (m.score or 0.0, m.last_checked or datetime.min))
            drop = len(all_nodes) - STORE_CAP
            for m in all_nodes[:drop]: await sess.delete(m)
            await sess.commit()
        if healthcheck:
            subset = (await sess.execute(select(NodeModel))).scalars().all()
            await apply_health(sess, subset)
        total = (await sess.execute(select(NodeModel))).scalars().all()
        return {"fetched": len(dedup), "total": len(total)}

# --------------------------- Metrics/Region ---------------------------------
async def _geoip_region(host: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"http://ip-api.com/json/{host}?fields=status,country,regionName,city")
            if r.status_code == 200:
                j = r.json()
                if j.get("status") == "success":
                    parts = [p for p in [j.get("country"), j.get("regionName"), j.get("city")] if p]
                    return ", ".join(parts)
    except Exception:
        return None
    return None

async def _measure_packet_loss(host: str, port: int, attempts: int = 5) -> Tuple[Optional[int], Optional[float]]:
    successes = 0
    latencies: List[int] = []
    for _ in range(attempts):
        lat = await tcp_latency(host, port)
        if lat is not None:
            successes += 1
            latencies.append(lat)
        await asyncio.sleep(0.05)
    loss = 1.0 - (successes / attempts)
    median_lat = None
    if latencies:
        latencies.sort()
        median_lat = latencies[len(latencies)//2]
    return median_lat, loss

async def update_metrics_for_all_nodes():
    async with AsyncSessionLocal() as sess:
        rows = (await sess.execute(select(NodeModel))).scalars().all()
        for m in rows:
            median_lat, loss = await _measure_packet_loss(m.host, m.port)
            # simple region cache via metrics table
            metrics = (await sess.execute(select(NodeMetrics).where(NodeMetrics.node_id == m.id))).scalar_one_or_none()
            if not metrics:
                metrics = NodeMetrics(node_id=m.id)
                sess.add(metrics)
            if metrics.region is None:
                metrics.region = await _geoip_region(m.host)
            metrics.latency_ms = median_lat
            metrics.packet_loss = round(loss, 3) if loss is not None else None
            # Throughput measurement placeholder (requires external tooling); leave None for now
            await sess.commit()

# --------------------------- Selection API ----------------------------------
def _rank_score(latency_ms: Optional[int], throughput_mbps: Optional[float]) -> float:
    score = 0.0
    if latency_ms is not None:
        score += max(0.0, 1.0 - min(1500, latency_ms) / 1500.0) * 0.7
    if throughput_mbps is not None:
        # normalize up to 100 Mbps
        score += min(throughput_mbps, 100.0) / 100.0 * 0.3
    return round(score, 3)

@app.get("/api/select")
async def select_node(region: Optional[str] = None, proto: Optional[str] = None):
    async with AsyncSessionLocal() as sess:
        q = select(NodeModel)
        if proto:
            q = q.where(NodeModel.proto == proto)
        nodes = (await sess.execute(q)).scalars().all()
        if not nodes:
            raise HTTPException(404, detail="No nodes available")
        out: List[Dict] = []
        for n in nodes:
            metrics = (await sess.execute(select(NodeMetrics).where(NodeMetrics.node_id == n.id))).scalar_one_or_none()
            if region and metrics and metrics.region and region.lower() not in metrics.region.lower():
                continue
            s = _rank_score(metrics.latency_ms if metrics else None, metrics.throughput_mbps if metrics else None)
            out.append({
                "id": n.id,
                "proto": n.proto,
                "host": n.host,
                "port": n.port,
                "name": n.name,
                "region": metrics.region if metrics else None,
                "latency_ms": metrics.latency_ms if metrics else None,
                "throughput_mbps": metrics.throughput_mbps if metrics else None,
                "packet_loss": metrics.packet_loss if metrics else None,
                "score": s,
            })
        if not out:
            raise HTTPException(404, detail="No nodes match criteria")
        out.sort(key=lambda x: x["score"], reverse=True)
        primary = out[0]
        backup = out[1] if len(out) > 1 else None
        return {"primary": primary, "backup": backup}

@app.get("/api/metrics")
async def list_metrics():
    await _ensure_schema()
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

@app.get("/api/metrics/{node_id}")
async def get_metrics(node_id: int):
    await _ensure_schema()
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

@app.get("/api/nodes.json")
async def get_nodes(limit: int = 200, proto: Optional[str] = None, sort: str = "score"):
    async with AsyncSessionLocal() as sess:
        q = select(NodeModel)
        if proto: q = q.where(NodeModel.proto == proto)
        rows = (await sess.execute(q)).scalars().all()
        def to_dict(m: NodeModel):
            return {
                "proto": m.proto, "host": m.host, "port": m.port, "name": m.name,
                "link": m.link, "uuid": m.uuid, "password": m.password,
                "params": json.loads(m.params_json or "{}"),
                "latency_ms": m.latency_ms, "healthy": m.healthy, "score": m.score,
                "last_checked": m.last_checked.timestamp() if m.last_checked else None,
            }
        out = [to_dict(m) for m in rows]
        if sort == "latency": out.sort(key=lambda n: (n["latency_ms"] is None, n["latency_ms"] or 1e9))
        elif sort == "random": random.shuffle(out)
        else: out.sort(key=lambda n: (n.get("score") or 0.0), reverse=True)
        return out[: max(1, min(limit, 1000))]

@app.get("/api/subscription.txt")
async def subscription_txt(limit: int = 200, base64out: bool = True):
    data = await get_nodes(limit=limit)
    text = "\n".join(n["link"] for n in data)
    if base64out:
        return {"base64": base64.b64encode(text.encode()).decode()}
    return {"raw": text}

# -- sing-box export reuses converter from v1 for brevity
def to_singbox_outbound(n: Dict) -> Dict:
    sni = (n.get("params") or {}).get("sni") or (n.get("params") or {}).get("server_name")
    proto = n.get("proto"); params = n.get("params") or {}
    tag = re.sub(r"\s+", "-", n.get("name", "node")).lower()
    if proto == "vless":
        reality = params.get("security") == "reality" or (params.get("reality") or {}).get("enabled")
        ob = {
            "type": "vless", "tag": tag, "server": n["host"], "server_port": n["port"], "uuid": n.get("uuid"),
            "flow": params.get("flow") or ("xtls-rprx-vision" if reality else None),
            "tls": {"enabled": True, "server_name": sni or n["host"],
                     "reality": {"enabled": True, "public_key": params.get("pbk") or params.get("public_key"), "short_id": params.get("sid") or params.get("short_id")} if reality else None,
                     "utls": {"enabled": True, "fingerprint": params.get("fp")} if params.get("fp") else None},
            "transport": {"type": params.get("type") or params.get("net") or "tcp", "path": params.get("path")}
        }
        return json.loads(json.dumps(ob))
    if proto == "trojan":
        return {"type": "trojan", "tag": tag, "server": n["host"], "server_port": n["port"], "password": n.get("password"),
                "tls": {"enabled": True, "server_name": sni or n["host"]}, "transport": {"type": params.get("type") or params.get("net") or "tcp"}}
    if proto == "vmess":
        return {"type": "vmess", "tag": tag, "server": n["host"], "server_port": n["port"], "uuid": n.get("uuid"),
                "security": params.get("scy") or "auto", "tls": {"enabled": params.get("tls") == "tls", "server_name": sni or n["host"]},
                "transport": {"type": params.get("net") or "tcp", "path": params.get("path")}}
    if proto == "ss":
        return {"type": "shadowsocks", "tag": tag, "server": n["host"], "server_port": n["port"] or 8388, "method": (params or {}).get("method"), "password": n.get("password")}
    return params

@app.get("/api/export/singbox.json")
async def export_singbox(limit: int = 200):
    raw = await get_nodes(limit=limit)
    outbounds = [to_singbox_outbound(n) for n in raw]
    return {"log": {"level": "info"}, "outbounds": outbounds}

@app.post("/api/ping")
async def ping_nodes(body: IngestBody):
    targets = [parse_any(s) for s in body.links]; targets = [n for n in targets if n]
    sem = asyncio.Semaphore(HEALTH_CONCURRENCY)
    async def one(n: Node):
        async with sem: n.latency_ms = await tcp_latency(n.host, n.port)
        n.healthy = n.latency_ms is not None
        n.score = score_node(n.proto, n.port, n.params, n.latency_ms)
        n.last_checked = time.time()
        return n
    out = await asyncio.gather(*(one(n) for n in targets))
    return [n.dict() for n in out]

# --------------------------- Scheduler -------------------------------------
scheduler = AsyncIOScheduler()

async def scheduled_refresh():
    try:
        log.info("scheduled refresh: start")
        await refresh_sources(healthcheck=True)
        log.info("scheduled refresh: done")
    except Exception as e:
        log.exception(f"scheduled refresh failed: {e}")

async def nightly_prune():
    try:
        async with AsyncSessionLocal() as sess:
            rows = (await sess.execute(select(NodeModel))).scalars().all()
            # drop nodes never seen healthy in the last 7 days
            cutoff = datetime.utcnow() - timedelta(days=7)
            for m in rows:
                if (not m.healthy) and (not m.last_checked or m.last_checked < cutoff):
                    await sess.delete(m)
            await sess.commit()
    except Exception as e:
        log.exception(f"nightly prune failed: {e}")

@app.on_event("startup")
async def on_start():
    os.makedirs("./data", exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # seed a tiny sample once
    async with AsyncSessionLocal() as sess:
        count = (await sess.execute(select(NodeModel))).scalars().first()
        if not count:
            sample = [
                "vless://11111111-2222-3333-4444-555555555555@example.com:443?security=reality&pbk=PUBKEY&sid=abcdef&sni=www.microsoft.com&type=tcp#Sample-REALITY",
                "vmess://" + base64.b64encode(json.dumps({
                    "v":"2","ps":"Sample-VMESS","add":"vmess.example.com","port":"443","id":"aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee","net":"tcp","type":"none","tls":"tls","sni":"www.cloudflare.com","path":"/"}).encode()).decode(),
                "trojan://pass123@trojan.example.com:443#Sample-Trojan",
                "ss://" + base64.b64encode("chacha20-ietf-poly1305:passw0rd@ss.example.com:8388".encode()).decode() + "#Sample-SS",
            ]
            await upsert_nodes(sess, [n for n in (parse_any(s) for s in sample) if n])
    # schedule jobs
    scheduler.add_job(scheduled_refresh, "interval", minutes=REFRESH_EVERY_MIN, jitter=60, id="refresh")
    scheduler.add_job(nightly_prune, "cron", hour=3, minute=15, id="prune")
    scheduler.add_job(update_metrics_for_all_nodes, "interval", minutes=5, id="metrics")
    scheduler.start()

@app.on_event("shutdown")
async def on_stop():
    scheduler.shutdown(wait=False)

# For direct execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
