from __future__ import annotations

import asyncio
import ssl
import time
from typing import Dict, Optional, Tuple, List
from .tunnel import SingBoxRunner, XrayRunner, app_check_via_proxy  # type: ignore


class TestingService:
    """Connection testing service with TLS handshake and app checks.

    Notes:
    - TLS handshake attempts only for TLS-like protocols
    - App checks verify outbound TLS reachability to public services; they are
      general environment checks (not routed through a VPN tunnel).
    - All operations are timeout-bound and concurrency-limited.
    """

    TLS_PROTOCOLS = {"vmess", "vless", "trojan", "reality", "xray"}
    APP_HOSTS = {
        "google": "www.google.com",
        "cloudflare": "www.cloudflare.com",
        "youtube": "www.youtube.com",
        "telegram": "core.telegram.org",
    }

    def __init__(self, timeout: float = 5.0, concurrency: int = 50):
        self.timeout = float(timeout)
        self.sem = asyncio.Semaphore(max(1, int(concurrency)))

    async def tcp_ping(self, host: str, port: int) -> Optional[float]:
        start = time.time()
        try:
            async with self.sem:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port), timeout=self.timeout
                )
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass
            return time.time() - start
        except Exception:
            return None

    async def tls_handshake(self, host: str, port: int) -> Optional[bool]:
        try:
            ctx = ssl.create_default_context()
            async with self.sem:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port, ssl=ctx, server_hostname=host),
                    timeout=self.timeout,
                )
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass
            return True
        except Exception:
            return False

    async def app_suite(self, apps: List[str]) -> Dict[str, bool]:
        results: Dict[str, bool] = {}

        async def _probe(name: str, host: str):
            ok = False
            try:
                ctx = ssl.create_default_context()
                async with self.sem:
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(host, 443, ssl=ctx, server_hostname=host),
                        timeout=self.timeout,
                    )
                    writer.close()
                    try:
                        await writer.wait_closed()
                    except Exception:
                        pass
                    ok = True
            except Exception:
                ok = False
            results[name] = ok

        tasks = []
        for name in apps:
            host = self.APP_HOSTS.get(name.lower())
            if host:
                tasks.append(asyncio.create_task(_probe(name.lower(), host)))
        if tasks:
            await asyncio.gather(*tasks)
        return results

    async def test_connection(self, host: str, port: int, protocol: str) -> Tuple[Optional[float], Optional[bool], Dict[str, bool]]:
        ping = await self.tcp_ping(host, port)
        hs: Optional[bool] = None
        if protocol.lower() in self.TLS_PROTOCOLS:
            hs = await self.tls_handshake(host, port)
        return ping, hs, {}

    async def test_via_tunnel(self, config_line: str, apps: List[str], timeout: float = 5.0, preferred: str = "auto") -> Dict[str, bool]:
        """Run app tests via a temporary local tunnel built from config_line.

        Currently supports ss:// and trojan:// via sing-box if available.
        """
        # Choose runner based on protocol or preference
        if preferred == "sing-box":
            runner = SingBoxRunner()
        elif preferred == "xray":
            runner = XrayRunner()
        else:
            # auto: prefer SingBox for ss/trojan; Xray for vmess/vless/reality
            if config_line.startswith(("ss://", "trojan://")):
                runner = SingBoxRunner()
            else:
                runner = XrayRunner()
        res = await runner.start(config_line)
        if not res.http_proxy:
            return {name: False for name in apps}
        try:
            out: Dict[str, bool] = {}
            tasks = [app_check_via_proxy(res.http_proxy, name, timeout=timeout) for name in apps]
            vals = await asyncio.gather(*tasks)
            for name, ok in zip(apps, vals):
                out[str(name).lower()] = bool(ok)
            return out
        finally:
            await runner.stop(res)


