from __future__ import annotations

import base64
import json
import re
from urllib.parse import parse_qs, unquote, urlparse

from .schemas import Node


def _b64decode_safe(b64: str) -> str:
    try:
        b64 = b64.replace("-", "+").replace("_", "/")
        pad = len(b64) % 4
        if pad:
            b64 += "=" * (4 - pad)
        return base64.b64decode(b64).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _parse_params(q: dict[str, list[str]]):
    return {k: v[0] for k, v in q.items()}


def parse_vless(link: str) -> Node | None:
    try:
        u = urlparse(link)
        qp = _parse_params(parse_qs(u.query))
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
        raw = _b64decode_safe(link.split("vmess://", 1)[1])
        obj = json.loads(raw)
        name = obj.get("ps") or f"VMESS {obj.get('add')}"
        sni = obj.get("sni") or obj.get("host")
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
        qp = _parse_params(parse_qs(u.query))
        name = unquote(u.fragment) or f"TROJAN {u.hostname}"
        return Node(
            proto="trojan",
            host=u.hostname or "",
            port=int(u.port or 443),
            name=name,
            link=link,
            password=unquote(u.username) if u.username else None,
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
            decoded = _b64decode_safe(raw.split("#", 1)[0])
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
    try:
        obj = json.loads(s)
        if isinstance(obj, dict) and obj.get("type") and obj.get("server"):
            host = obj.get("server")
            port = int(obj.get("server_port") or obj.get("port") or 443)
            tag = obj.get("tag") or f"{obj['type'].upper()} {host}"
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


