from __future__ import annotations

import asyncio
from typing import Dict, List, Optional
from datetime import datetime

import aiohttp


class SourceValidator:
    """Validates and monitors source health.

    This is a standalone utility that can be used before
    adding a source into the fetch pipeline or periodically
    to measure the health of known sources.
    """

    def __init__(self):
        self.health_history: Dict[str, List[bool]] = {}
        self.last_check: Dict[str, datetime] = {}

    async def validate_source(self, url: str, timeout: int = 30) -> Dict:
        """Comprehensive source validation returning metrics and a score."""
        result: Dict[str, object] = {
            "url": url,
            "accessible": False,
            "response_time": None,
            "content_type": None,
            "size_bytes": 0,
            "estimated_configs": 0,
            "protocols_found": [],
            "last_modified": None,
            "reliability_score": 0.0,
        }

        try:
            async with aiohttp.ClientSession() as session:
                start = datetime.now()
                async with session.get(url, timeout=timeout) as response:
                    result["accessible"] = response.status == 200
                    result["response_time"] = (datetime.now() - start).total_seconds()
                    result["content_type"] = response.headers.get("Content-Type", "")

                    text = await response.text()
                    result["size_bytes"] = len(text.encode())
                    result["estimated_configs"] = self._estimate_configs(text)
                    result["protocols_found"] = self._detect_protocols(text)

                    # Optional: capture Last-Modified if present
                    lm = response.headers.get("Last-Modified")
                    if lm:
                        result["last_modified"] = lm

                    result["reliability_score"] = self._calculate_reliability(url, result)  # type: ignore[arg-type]

        except Exception as e:  # pragma: no cover - network errors not unit-tested
            result["error"] = str(e)

        return result

    def _estimate_configs(self, content: str) -> int:
        """Estimate number of configs in content by prefix scanning."""
        lines = content.strip().split("\n")
        valid_prefixes = (
            "vmess://",
            "vless://",
            "trojan://",
            "ss://",
            "ssr://",
            "hysteria://",
            "hysteria2://",
            "tuic://",
            "wg://",
            "openvpn://",
            "outline://",
            "brook://",
            "naive://",
            "snell://",
            "sspanel://",
            "clash://",
            "surge://",
        )
        return sum(1 for line in lines if any(line.strip().startswith(p) for p in valid_prefixes))

    def _detect_protocols(self, content: str) -> List[str]:
        """Detect which protocols are present via substring search."""
        protocols = set()
        protocol_map = {
            "vmess://": "vmess",
            "vless://": "vless",
            "trojan://": "trojan",
            "ss://": "shadowsocks",
            "ssr://": "shadowsocksr",
            "hysteria://": "hysteria",
            "hysteria2://": "hysteria2",
            "tuic://": "tuic",
            "wg://": "wireguard",
            "openvpn://": "openvpn",
            "outline://": "outline",
            "brook://": "brook",
            "naive://": "naive",
            "snell://": "snell",
            "sspanel://": "sspanel",
            "clash://": "clash",
            "surge://": "surge",
        }

        # Enhanced detection for protocols that might not have URL schemes
        enhanced_detection = {
            "wireguard": ["[Interface]", "PrivateKey", "PublicKey", "Address"],
            "openvpn": ["<ca>", "<cert>", "<key>", "client", "remote"],
            "clash": ["proxies:", "proxy-groups:", "rules:"],
            "surge": ["[Proxy]", "[Proxy Group]", "[Rule]"],
            "naive": ["naive", "proxy"],
            "brook": ["brook", "server"],
            "snell": ["snell", "server"],
            "outline": ["outline", "server"],
        }

        # Check URL scheme protocols
        for prefix, proto in protocol_map.items():
            if prefix in content:
                protocols.add(proto)

        # Check enhanced detection patterns
        for proto, patterns in enhanced_detection.items():
            if any(pattern in content for pattern in patterns):
                protocols.add(proto)

        return list(protocols)

    def _calculate_reliability(self, url: str, result: Dict) -> float:
        """Calculate source reliability score based on simple heuristics."""
        score = 0.0

        # Base score from accessibility
        if result.get("accessible"):
            score += 0.3

        # Response time factor
        rt = result.get("response_time")
        if isinstance(rt, (int, float)):
            if rt < 2:
                score += 0.2
            elif rt < 5:
                score += 0.1

        # Content quality
        est = int(result.get("estimated_configs") or 0)
        if est > 100:
            score += 0.2
        if est > 1000:
            score += 0.1

        # Protocol diversity
        protos = result.get("protocols_found") or []
        if isinstance(protos, list) and len(protos) >= 3:
            score += 0.1

        # Historical reliability (last 10 checks)
        if url in self.health_history:
            recent = self.health_history[url][-10:]
            if recent:
                success_rate = sum(1 for v in recent if v) / len(recent)
                score += success_rate * 0.1

        return float(min(1.0, score))

