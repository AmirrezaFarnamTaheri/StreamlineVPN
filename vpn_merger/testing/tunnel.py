from __future__ import annotations

import asyncio
import json
import os
import shutil
import socket
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple


def _find_free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    _, port = s.getsockname()
    try:
        s.close()
    except Exception:
        pass
    return int(port)


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


@dataclass
class TunnelResult:
    http_proxy: Optional[str]
    process: Optional[asyncio.subprocess.Process]
    temp_config: Optional[Path]


class TunnelRunner:
    async def start(self, config_line: str) -> TunnelResult:
        raise NotImplementedError

    async def stop(self, res: TunnelResult) -> None:
        try:
            if res.process and res.process.returncode is None:
                res.process.terminate()
                try:
                    await asyncio.wait_for(res.process.wait(), timeout=1.5)
                except Exception:
                    res.process.kill()
        except Exception:
            pass
        if res.temp_config:
            try:
                res.temp_config.unlink(missing_ok=True)  # type: ignore[arg-type]
            except Exception:
                pass


class SingBoxRunner(TunnelRunner):
    def __init__(self, bin_path: Optional[str] = None):
        self.bin = bin_path or os.environ.get("SING_BOX_BIN") or _which("sing-box")

    def _parse_ss(self, uri: str) -> Optional[Dict]:
        # ss://method:password@host:port or ss://base64(method:password@host:port)
        try:
            from urllib.parse import urlparse, unquote
            u = urlparse(uri)
            if u.netloc and ":" in u.netloc:
                auth_host = u.netloc
            else:
                # base64 case
                import base64
                raw = uri.split("ss://", 1)[1]
                raw = raw.split("#", 1)[0]
                auth_host = base64.b64decode(raw + ("=" * (-len(raw) % 4))).decode("utf-8")
            creds, hostport = auth_host.rsplit("@", 1)
            method, password = creds.split(":", 1)
            host, port = hostport.split(":", 1)
            return {
                "type": "shadowsocks",
                "server": host,
                "server_port": int(port),
                "method": method,
                "password": password,
            }
        except Exception:
            return None

    def _parse_trojan(self, uri: str) -> Optional[Dict]:
        # trojan://password@host:port
        try:
            from urllib.parse import urlparse, parse_qs
            u = urlparse(uri)
            password = u.username or ""
            host = u.hostname or ""
            port = int(u.port or 443)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            sni = q.get("sni") or host
            alpn_raw = q.get("alpn") or ""
            alpn = [a.strip() for a in alpn_raw.split(",") if a.strip()] if alpn_raw else ["h2", "http/1.1"]
            fp = q.get("fp") or q.get("fingerprint")
            return {
                "type": "trojan",
                "server": host,
                "server_port": port,
                "password": password,
                "tls": {
                    "enabled": True,
                    "server_name": sni,
                    "alpn": alpn,
                    **({"utls": {"enabled": True, "fingerprint": fp}} if fp else {}),
                },
            }
        except Exception:
            return None

    def _build_config(self, outbound: Dict, port: int) -> Dict:
        return {
            "log": {"level": "error"},
            "inbounds": [
                {"type": "mixed", "listen": "127.0.0.1", "listen_port": port}
            ],
            "outbounds": [outbound],
        }

    async def start(self, config_line: str) -> TunnelResult:
        if not self.bin:
            return TunnelResult(None, None, None)
        ob: Optional[Dict] = None
        if config_line.startswith("ss://"):
            ob = self._parse_ss(config_line)
        elif config_line.startswith("trojan://"):
            ob = self._parse_trojan(config_line)
        else:
            return TunnelResult(None, None, None)
        if not ob:
            return TunnelResult(None, None, None)
        port = _find_free_port()
        cfg = self._build_config(ob, port)
        tmp = Path(tempfile.mkstemp(prefix="sbx_", suffix=".json")[1])
        tmp.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
        try:
            proc = await asyncio.create_subprocess_exec(
                self.bin, "run", "-c", str(tmp),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except Exception:
            try:
                tmp.unlink()
            except Exception:
                pass
            return TunnelResult(None, None, None)
        # Give it a brief moment to initialize
        try:
            await asyncio.sleep(0.5)
        except Exception:
            pass
        return TunnelResult(f"http://127.0.0.1:{port}", proc, tmp)


class XrayRunner(TunnelRunner):
    def __init__(self, bin_path: Optional[str] = None):
        self.bin = bin_path or os.environ.get("XRAY_BIN") or _which("xray") or _which("xray.exe")

    def _parse_vmess(self, uri: str) -> Optional[Dict]:
        # vmess://base64(JSON)
        try:
            import base64, json as _json
            raw = uri.split("vmess://", 1)[1]
            payload = base64.b64decode(raw + ("=" * (-len(raw) % 4))).decode("utf-8")
            obj = _json.loads(payload)
            host = obj.get("add")
            port = int(obj.get("port") or 443)
            uuid = obj.get("id")
            alterId = int(obj.get("aid") or 0)
            tls = obj.get("tls") == "tls"
            sni = obj.get("sni") or obj.get("host") or host
            alpn_raw = obj.get("alpn") or ""
            alpn = [a.strip() for a in alpn_raw.split(",") if a.strip()] if alpn_raw else []
            fp = obj.get("fp") or obj.get("fingerprint")
            out = {
                "protocol": "vmess",
                "settings": {
                    "vnext": [
                        {"address": host, "port": port, "users": [{"id": uuid, "alterId": alterId, "security": "auto"}]}
                    ]
                },
                "streamSettings": {
                    "network": obj.get("net") or "tcp",
                    "security": "tls" if tls else "none",
                    **({"tlsSettings": {"serverName": sni}} if tls else {}),
                },
            }
            net = (obj.get("net") or "").lower()
            path = obj.get("path") or "/"
            host_header = obj.get("host") or sni
            host_list = [h.strip() for h in str(host_header).split(",") if h.strip()]
            if net == "ws":
                out["streamSettings"]["wsSettings"] = {"path": path, "headers": {"Host": host_header}}
            elif net in ("h2", "http"):
                out["streamSettings"]["httpSettings"] = {"path": path, "host": host_list or [sni]}
            elif net == "grpc":
                out["streamSettings"]["grpcSettings"] = {"serviceName": (obj.get("path") or "grpc").lstrip("/")}
            if tls:
                if alpn:
                    out["streamSettings"].setdefault("tlsSettings", {}).update({"alpn": alpn})
                if fp:
                    out["streamSettings"].setdefault("tlsSettings", {}).update({"fingerprint": fp})
                # default ALPN if none provided
                if not alpn:
                    out["streamSettings"].setdefault("tlsSettings", {}).update({"alpn": ["h2", "http/1.1"]})
            return out
        except Exception:
            return None

    def _parse_vless(self, uri: str) -> Optional[Dict]:
        # vless://uuid@host:port?encryption=none&security=tls|reality&...&flow=xtls-rprx-vision
        try:
            from urllib.parse import urlparse, parse_qs
            u = urlparse(uri)
            uuid = (u.username or "").strip()
            host = u.hostname or ""
            port = int(u.port or 443)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            sec = (q.get("security") or "none").lower()
            flow = q.get("flow")
            sni = q.get("sni") or host
            out: Dict = {
                "protocol": "vless",
                "settings": {
                    "vnext": [
                        {"address": host, "port": port, "users": [{"id": uuid, "encryption": q.get("encryption") or "none", **({"flow": flow} if flow else {})}]}
                    ]
                },
                "streamSettings": {
                    "network": q.get("type") or "tcp",
                },
            }
            if sec == "reality":
                out["streamSettings"].update({
                    "security": "reality",
                    "realitySettings": {
                        "serverName": q.get("sni") or host,
                        "publicKey": q.get("pbk") or "",
                        "shortId": q.get("sid") or "",
                        "spiderX": q.get("spx") or "",
                        **({"fingerprint": q.get("fp")} if q.get("fp") else {}),
                    },
                })
            elif sec == "tls":
                out["streamSettings"].update({
                    "security": "tls",
                    "tlsSettings": {"serverName": sni},
                })
            else:
                out["streamSettings"]["security"] = "none"
            # Transport tuning
            net = (out["streamSettings"].get("network") or "").lower()
            path = q.get("path") or "/"
            host_header = q.get("host") or sni
            host_list = [h.strip() for h in str(host_header).split(",") if h.strip()]
            alpn_raw = q.get("alpn") or ""
            alpn = [a.strip() for a in alpn_raw.split(",") if a.strip()] if alpn_raw else []
            fp = q.get("fp") or q.get("fingerprint")
            if net == "ws":
                out["streamSettings"]["wsSettings"] = {"path": path, "headers": {"Host": host_header}}
            elif net in ("h2", "http"):
                out["streamSettings"]["httpSettings"] = {"path": path, "host": host_list or [sni]}
            elif net == "grpc":
                out["streamSettings"]["grpcSettings"] = {"serviceName": (q.get("serviceName") or "grpc").lstrip("/")}
            if out["streamSettings"].get("security") == "tls":
                if alpn:
                    out["streamSettings"].setdefault("tlsSettings", {}).update({"alpn": alpn})
                if fp:
                    out["streamSettings"].setdefault("tlsSettings", {}).update({"fingerprint": fp})
                if not alpn:
                    out["streamSettings"].setdefault("tlsSettings", {}).update({"alpn": ["h2", "http/1.1"]})
            return out
        except Exception:
            return None

    def _build_config(self, outbound: Dict, port: int) -> Dict:
        return {
            "log": {"loglevel": "error"},
            "inbounds": [
                {"tag": "in", "listen": "127.0.0.1", "port": port, "protocol": "socks", "settings": {"udp": False}}
            ],
            "outbounds": [
                {"tag": "out", **outbound}
            ],
        }

    async def start(self, config_line: str) -> TunnelResult:
        if not self.bin:
            return TunnelResult(None, None, None)
        ob: Optional[Dict] = None
        if config_line.startswith("vmess://"):
            ob = self._parse_vmess(config_line)
        elif config_line.startswith("vless://"):
            ob = self._parse_vless(config_line)
        else:
            return TunnelResult(None, None, None)
        if not ob:
            return TunnelResult(None, None, None)
        port = _find_free_port()
        cfg = self._build_config(ob, port)
        tmp = Path(tempfile.mkstemp(prefix="xray_", suffix=".json")[1])
        tmp.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
        try:
            # Prefer "xray run -c" but fallback to "xray -c"
            try:
                proc = await asyncio.create_subprocess_exec(
                    self.bin, "run", "-c", str(tmp),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
            except Exception:
                proc = await asyncio.create_subprocess_exec(
                    self.bin, "-c", str(tmp),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
        except Exception:
            try:
                tmp.unlink()
            except Exception:
                pass
            return TunnelResult(None, None, None)
        try:
            await asyncio.sleep(0.5)
        except Exception:
            pass
        # Xray inbound is socks; use HTTP via http://127.0.0.1:port if supported by clients; here stick to socks via scheme
        return TunnelResult(f"socks5://127.0.0.1:{port}", proc, tmp)


async def app_check_via_proxy(http_proxy: str, app: str, timeout: float = 5.0) -> bool:
    try:
        import aiohttp
        from .testing import TestingService  # type: ignore
    except Exception:
        pass
    hosts = {
        "google": "https://www.google.com/",
        "cloudflare": "https://www.cloudflare.com/",
        "youtube": "https://www.youtube.com/",
        "telegram": "https://core.telegram.org/",
    }
    url = hosts.get(app.lower())
    if not url:
        return False
    try:
        timeout_cfg = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=timeout_cfg) as s:
            async with s.get(url, proxy=http_proxy, allow_redirects=True) as r:
                return 200 <= r.status < 400
    except Exception:
        return False
