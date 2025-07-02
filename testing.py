import asyncio
import base64
import json
import random
import re
import ssl
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import aiohttp

from config import CONFIG, Config
from protocols import categorize_protocol


@dataclass
class ConfigResult:
    """Enhanced config result with testing metrics."""

    config: str
    protocol: str
    host: Optional[str] = None
    port: Optional[int] = None
    ping_time: Optional[float] = None
    is_reachable: bool = False
    handshake_ok: Optional[bool] = None
    source_url: str = ""


class EnhancedConfigProcessor:
    """Process configs and perform connectivity testing."""

    MAX_DECODE_SIZE = 256 * 1024  # safety limit for base64 payloads

    def __init__(self, config: Config = CONFIG) -> None:
        self.config = config
        self.dns_cache = {}

    def extract_host_port(self, config: str) -> Tuple[Optional[str], Optional[int]]:
        """Extract host and port from configuration for testing."""
        try:
            if config.startswith(("vmess://", "vless://")):
                try:
                    json_part = config.split("://", 1)[1]
                    decoded_bytes = base64.b64decode(json_part)
                    if len(decoded_bytes) > self.MAX_DECODE_SIZE:
                        return None, None
                    decoded = decoded_bytes.decode("utf-8", "ignore")
                    data = json.loads(decoded)
                    host = data.get("add") or data.get("host")
                    port = data.get("port")
                    return host, int(port) if port else None
                except Exception:
                    pass

            parsed = urlparse(config)
            if parsed.hostname and parsed.port:
                return parsed.hostname, parsed.port

            match = re.search(r"@([^:/?#]+):(\d+)", config)
            if match:
                return match.group(1), int(match.group(2))
        except Exception:
            pass
        return None, None

    def create_semantic_hash(self, config: str) -> str:
        """Create semantic hash for intelligent deduplication."""
        host, port = self.extract_host_port(config)
        user_id = None

        if config.startswith(("vmess://", "vless://")):
            try:
                after_scheme = config.split("://", 1)[1]
                parsed = urlparse(config)
                if parsed.username:
                    user_id = parsed.username
                else:
                    padded = after_scheme + "=" * (-len(after_scheme) % 4)
                    decoded = base64.b64decode(padded).decode("utf-8", "ignore")
                    data = json.loads(decoded)
                    user_id = data.get("id") or data.get("uuid") or data.get("user")
            except Exception:
                pass

        if host and port:
            key = f"{host}:{port}"
            if user_id:
                key = f"{user_id}@{key}"
        else:
            normalized = re.sub(r'#.*$', '', config).strip()
            key = normalized
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    async def test_connection(self, host: str, port: int, protocol: str) -> Tuple[Optional[float], Optional[bool]]:
        """Test connection and optionally perform a TLS handshake."""
        if not self.config.enable_url_testing:
            return None, None

        start = time.time()
        ssl_ctx = None
        handshake = None
        if self.config.full_test and protocol in {
            "VMess", "VLESS", "Trojan", "Hysteria2", "Hysteria",
            "TUIC", "Reality", "Naive", "Juicity", "ShadowTLS",
            "WireGuard",
        }:
            ssl_ctx = ssl.create_default_context()
            handshake = False
        try:
            conn = await asyncio.wait_for(
                asyncio.open_connection(
                    host,
                    port,
                    ssl=ssl_ctx,
                    server_hostname=host if ssl_ctx else None,
                ),
                timeout=self.config.test_timeout,
            )
            reader, writer = conn
            if ssl_ctx:
                handshake = True
            writer.close()
            await writer.wait_closed()
            return time.time() - start, handshake
        except Exception:
            return None, handshake

    def categorize_protocol(self, config: str) -> str:
        """Categorize configuration by protocol."""
        return categorize_protocol(config)


class AsyncSourceFetcher:
    """Async source fetcher with comprehensive testing."""

    def __init__(self, processor: EnhancedConfigProcessor, config: Config = CONFIG) -> None:
        self.processor = processor
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def test_source_availability(self, url: str) -> bool:
        """Test if a source URL is available."""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with self.session.head(
                url,
                timeout=timeout,
                allow_redirects=True,
                proxy=self.config.proxy,
            ) as response:
                status = response.status
                if status == 200:
                    return True
                if 400 <= status < 500:
                    async with self.session.get(
                        url,
                        headers={**self.config.headers, "Range": "bytes=0-0"},
                        timeout=timeout,
                        allow_redirects=True,
                        proxy=self.config.proxy,
                    ) as get_resp:
                        return get_resp.status in (200, 206)
                return False
        except Exception:
            return False

    async def fetch_source(self, url: str) -> Tuple[str, List[ConfigResult]]:
        """Fetch single source with comprehensive testing."""
        for attempt in range(self.config.max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
                async with self.session.get(
                    url,
                    headers=self.config.headers,
                    timeout=timeout,
                    proxy=self.config.proxy,
                ) as response:
                    if response.status != 200:
                        continue

                    content = await response.text()
                    if not content.strip():
                        return url, []

                    try:
                        if not any(char in content for char in '\n\r') and len(content) > 100:
                            decoded = base64.b64decode(content).decode("utf-8", "ignore")
                            if decoded.count("://") > content.count("://"):
                                content = decoded
                    except Exception:
                        pass

                    lines = [line.strip() for line in content.splitlines() if line.strip()]
                    config_results = []

                    for line in lines:
                        if (
                            line.startswith(self.config.valid_prefixes)
                            and len(line) > 20
                            and len(line) < 2000
                            and len(config_results) < self.config.max_configs_per_source
                        ):
                            host, port = self.processor.extract_host_port(line)
                            protocol = self.processor.categorize_protocol(line)

                            result = ConfigResult(
                                config=line,
                                protocol=protocol,
                                host=host,
                                port=port,
                                source_url=url,
                            )

                            if self.config.enable_url_testing and host and port:
                                ping_time, hs = await self.processor.test_connection(host, port, protocol)
                                result.ping_time = ping_time
                                result.handshake_ok = hs
                                result.is_reachable = ping_time is not None and (hs is not False)

                            config_results.append(result)

                    return url, config_results

            except Exception:
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(min(3, 1.5 + random.random()))

        return url, []

