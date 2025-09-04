#!/usr/bin/env python3
"""
Free Nodes Aggregator API — Simple In-Memory Version
====================================================
A lightweight, in-memory version of the Free Nodes Aggregator for development
and testing purposes. No database required.

Features:
- Accepts proxy share links (vless://, vmess://, trojan://, ss://)
- Fetches links from HTTP sources
- De-dupes and scores nodes
- Serves clean JSON for UI consumption
- Exports sing-box JSON and raw subscription text
- Rate limiting and CORS enabled

Usage:
    pip install fastapi uvicorn[standard] pydantic httpx
    uvicorn free_nodes_simple_api:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import asyncio
import base64
import json
import time
from urllib.parse import parse_qs, unquote

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ------------------------------ Config ------------------------------------
RATE_LIMIT_REQUESTS_PER_MINUTE = 120
HEALTHCHECK_CONCURRENCY = 50
CONNECT_TIMEOUT = 2.5  # seconds
STORE_CAP = 5000  # max nodes kept

# ------------------------------ App ---------------------------------------
app = FastAPI(title="Free Nodes Aggregator API (Simple)", version="1.0.0")
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

    async def get_all(self) -> list[Node]:
        async with self.lock:
            return list(self.map.values())

    async def add_sources(self, urls: list[str]):
        async with self.lock:
            for url in urls:
                if url not in self.sources:
                    self.sources.append(url)

    async def get_sources(self) -> list[str]:
        async with self.lock:
            return list(self.sources)


store = NodeStore()


# ------------------------------ Parsers -----------------------------------
def parse_vless(link: str) -> Node | None:
    """Parse VLESS:// links"""
    if not link.startswith("vless://"):
        return None

    try:
        # Remove vless:// prefix
        content = link[8:]

        # Split into uuid@host:port and query params
        if "@" not in content:
            return None

        uuid_part, rest = content.split("@", 1)
        uuid = uuid_part

        # Parse host:port and query params
        if "?" in rest:
            host_port, query_str = rest.split("?", 1)
            params = parse_qs(query_str)
        else:
            host_port = rest
            params = {}

        # Parse host:port
        if ":" not in host_port:
            return None

        host, port_str = host_port.rsplit(":", 1)
        port = int(port_str)

        # Extract name from params
        name = params.get("remarks", [f"VLESS-{host}"])[0]
        if name:
            name = unquote(name)

        return Node(
            proto="vless", host=host, port=port, name=name, link=link, uuid=uuid, params=params
        )
    except Exception:
        return None


def parse_vmess(link: str) -> Node | None:
    """Parse VMESS:// links"""
    if not link.startswith("vmess://"):
        return None

    try:
        # Remove vmess:// prefix and decode base64
        content = link[8:]
        decoded = base64.b64decode(content).decode("utf-8")
        data = json.loads(decoded)

        return Node(
            proto="vmess",
            host=data.get("add", ""),
            port=data.get("port", 0),
            name=data.get("ps", f"VMESS-{data.get('add', '')}"),
            link=link,
            uuid=data.get("id", ""),
            params=data,
        )
    except Exception:
        return None


def parse_trojan(link: str) -> Node | None:
    """Parse TROJAN:// links"""
    if not link.startswith("trojan://"):
        return None

    try:
        # Remove trojan:// prefix
        content = link[9:]

        # Split into password@host:port and query params
        if "@" not in content:
            return None

        password_part, rest = content.split("@", 1)
        password = password_part

        # Parse host:port and query params
        if "?" in rest:
            host_port, query_str = rest.split("?", 1)
            params = parse_qs(query_str)
        else:
            host_port = rest
            params = {}

        # Parse host:port
        if ":" not in host_port:
            return None

        host, port_str = host_port.rsplit(":", 1)
        port = int(port_str)

        # Extract name from params
        name = params.get("remarks", [f"TROJAN-{host}"])[0]
        if name:
            name = unquote(name)

        return Node(
            proto="trojan",
            host=host,
            port=port,
            name=name,
            link=link,
            password=password,
            params=params,
        )
    except Exception:
        return None


def parse_shadowsocks(link: str) -> Node | None:
    """Parse SS:// links"""
    if not link.startswith("ss://"):
        return None

    try:
        # Remove ss:// prefix
        content = link[5:]

        # Parse base64 encoded part
        if "#" in content:
            encoded, name = content.split("#", 1)
            name = unquote(name)
        else:
            encoded = content
            name = "Shadowsocks"

        # Decode base64
        decoded = base64.b64decode(encoded).decode("utf-8")

        # Parse method:password@host:port
        if "@" not in decoded:
            return None

        method_pass, host_port = decoded.split("@", 1)

        if ":" not in method_pass:
            return None

        method, password = method_pass.split(":", 1)

        if ":" not in host_port:
            return None

        host, port_str = host_port.rsplit(":", 1)
        port = int(port_str)

        return Node(
            proto="shadowsocks",
            host=host,
            port=port,
            name=name,
            link=link,
            password=password,
            params={"method": method},
        )
    except Exception:
        return None


def parse_link(link: str) -> Node | None:
    """Parse any supported link format"""
    link = link.strip()
    if not link:
        return None

    parsers = [parse_vless, parse_vmess, parse_trojan, parse_shadowsocks]

    for parser in parsers:
        node = parser(link)
        if node:
            return node

    return None


# ------------------------------ Health Checks -----------------------------
async def check_node_health(node: Node) -> tuple[bool, int]:
    """Check if a node is reachable via TCP connect"""
    try:
        start_time = time.time()
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(node.host, node.port), timeout=CONNECT_TIMEOUT
        )
        writer.close()
        await writer.wait_closed()

        latency = int((time.time() - start_time) * 1000)
        return True, latency
    except Exception:
        return False, 0


async def health_check_nodes(nodes: list[Node]) -> list[Node]:
    """Health check multiple nodes concurrently"""
    semaphore = asyncio.Semaphore(HEALTHCHECK_CONCURRENCY)

    async def check_with_semaphore(node: Node) -> Node:
        async with semaphore:
            healthy, latency = await check_node_health(node)
            node.healthy = healthy
            node.latency_ms = latency
            node.last_checked = time.time()

            # Simple scoring based on health and latency
            if healthy:
                node.score = max(0.1, 1.0 - (latency / 1000.0))  # Lower latency = higher score
            else:
                node.score = 0.0

            return node

    tasks = [check_with_semaphore(node) for node in nodes]
    return await asyncio.gather(*tasks)


# ------------------------------ API Endpoints -----------------------------
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Free Nodes Aggregator API (Simple)",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "GET /api/nodes.json": "Get all nodes",
            "POST /api/ingest": "Add nodes from links",
            "POST /api/sources": "Add HTTP sources",
            "GET /api/sources": "Get current sources",
            "GET /api/export/singbox": "Export sing-box JSON",
            "GET /api/export/raw": "Export raw subscription",
            "GET /api/health": "Health check",
        },
    }


@app.get("/api/nodes.json")
async def get_nodes():
    """Get all nodes as JSON"""
    nodes = await store.get_all()
    return {"nodes": [node.dict() for node in nodes], "count": len(nodes), "timestamp": time.time()}


@app.post("/api/ingest")
async def ingest_nodes(body: IngestBody):
    """Ingest nodes from a list of links"""
    if not body.links:
        raise HTTPException(status_code=400, detail="No links provided")

    parsed_nodes = []
    for link in body.links:
        node = parse_link(link)
        if node:
            parsed_nodes.append(node)

    if parsed_nodes:
        await store.upsert_many(parsed_nodes)

    return {"ingested": len(parsed_nodes), "total": len(await store.get_all())}


@app.post("/api/sources")
async def add_sources(body: SourcesBody):
    """Add HTTP sources for automatic fetching"""
    if not body.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    await store.add_sources(body.urls)

    return {"added": len(body.urls), "total_sources": len(await store.get_sources())}


@app.get("/api/sources")
async def get_sources():
    """Get current HTTP sources"""
    sources = await store.get_sources()
    return {"sources": sources}


@app.get("/api/export/singbox")
async def export_singbox():
    """Export nodes as sing-box JSON outbounds"""
    nodes = await store.get_all()

    outbounds = []
    for node in nodes:
        if node.proto == "vless":
            outbound = {
                "type": "vless",
                "tag": node.name,
                "server": node.host,
                "server_port": node.port,
                "uuid": node.uuid,
                "flow": node.params.get("flow", ""),
                "network": node.params.get("type", "tcp"),
                "tls": (
                    {
                        "enabled": node.params.get("security") == "tls",
                        "server_name": node.params.get("sni", node.host),
                        "insecure": True,
                    }
                    if node.params.get("security") == "tls"
                    else None
                ),
            }
            outbounds.append(outbound)
        elif node.proto == "vmess":
            outbound = {
                "type": "vmess",
                "tag": node.name,
                "server": node.host,
                "server_port": node.port,
                "uuid": node.uuid,
                "security": node.params.get("security", "auto"),
                "alter_id": node.params.get("aid", 0),
            }
            outbounds.append(outbound)
        elif node.proto == "trojan":
            outbound = {
                "type": "trojan",
                "tag": node.name,
                "server": node.host,
                "server_port": node.port,
                "password": node.password,
                "tls": {
                    "enabled": True,
                    "server_name": node.params.get("sni", node.host),
                    "insecure": True,
                },
            }
            outbounds.append(outbound)
        elif node.proto == "shadowsocks":
            outbound = {
                "type": "shadowsocks",
                "tag": node.name,
                "server": node.host,
                "server_port": node.port,
                "method": node.params.get("method", "aes-256-gcm"),
                "password": node.password,
            }
            outbounds.append(outbound)

    return {"outbounds": outbounds, "count": len(outbounds)}


@app.get("/api/export/raw")
async def export_raw():
    """Export nodes as raw subscription text"""
    nodes = await store.get_all()

    links = []
    for node in nodes:
        links.append(node.link)

    return {"links": links, "count": len(links), "subscription": "\n".join(links)}


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    nodes = await store.get_all()
    healthy_nodes = [n for n in nodes if n.healthy]

    return {
        "status": "healthy",
        "total_nodes": len(nodes),
        "healthy_nodes": len(healthy_nodes),
        "health_ratio": len(healthy_nodes) / len(nodes) if nodes else 0,
    }


# ------------------------------ Background Tasks --------------------------
async def fetch_from_sources():
    """Fetch nodes from configured HTTP sources"""
    sources = await store.get_sources()
    if not sources:
        return

    async with httpx.AsyncClient(timeout=10.0) as client:
        for source_url in sources:
            try:
                response = await client.get(source_url)
                response.raise_for_status()

                content = response.text
                links = [line.strip() for line in content.split("\n") if line.strip()]

                parsed_nodes = []
                for link in links:
                    node = parse_link(link)
                    if node:
                        parsed_nodes.append(node)

                if parsed_nodes:
                    await store.upsert_many(parsed_nodes)
                    print(f"Fetched {len(parsed_nodes)} nodes from {source_url}")

            except Exception as e:
                print(f"Error fetching from {source_url}: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    print("Free Nodes Aggregator API (Simple) starting up...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
