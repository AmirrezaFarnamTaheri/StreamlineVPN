from __future__ import annotations

import asyncio
import json
import re
from typing import List, Set

import aiohttp


SEARCH_PAGES = [
    "https://github.com/topics/v2ray",
    "https://github.com/topics/clash",
    "https://github.com/search?q=clash+subscription+extension%3Ayaml&type=code",
    "https://github.com/search?q=v2ray+subscribe+extension%3Atxt&type=code",
    "https://github.com/search?q=sing-box+subscribe+extension%3Ajson&type=code",
    "https://github.com/mermeroo/V2RAY-CLASH-BASE64-Subscription.Links",
]

RAW_RE = re.compile(
    r"https://raw\.githubusercontent\.com/[^\s\"'<>]+?\.(?:txt|ya?ml|json)", re.I
)


async def _fetch(session: aiohttp.ClientSession, url: str) -> str:
    for attempt in range(3):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=12)) as r:
                if r.status == 200:
                    return await r.text()
        except Exception:
            await asyncio.sleep(0.5 * (attempt + 1))
    return ""


def _plausible(u: str) -> bool:
    if any(k in u for k in ("license", "readme", "/rules", "acl4ssr")):
        return False
    return any(
        t in u.lower()
        for t in (
            "sub",
            "mix",
            "subscribe",
            "subscription",
            "clash",
            "v2ray",
            "vmess",
            "vless",
            "trojan",
            "sing",
        )
    )


FALLBACK_SOURCES: List[str] = [
    "https://raw.githubusercontent.com/barry-far/V2ray-config/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-config/main/Sub2.txt",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/mix",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/vless",
    "https://raw.githubusercontent.com/yebekhe/V2Hub/main/merged",
    "https://raw.githubusercontent.com/taheri79/V2rayCollector/main/sub/normal/mix",
    "https://raw.githubusercontent.com/Mahdi0024/ProxyCollector/main/subscriptions/mix",
    "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/vless",
    "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/vmess",
    "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/trojan",
    "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/shadowsocks",
    "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/reality",
    "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/hysteria",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
    "https://raw.githubusercontent.com/hiddify/hiddify-config/main/sub.txt",
    "https://raw.githubusercontent.com/hiddify/hiddify-config/main/sub_base64.txt",
    "https://raw.githubusercontent.com/pojiezhiyuanjun/freev2/master/0709.txt",
    "https://raw.githubusercontent.com/FaNat1q/V2ray/main/Mix",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/zusuk8/ClashRule/main/sublist.txt",
    "https://raw.githubusercontent.com/Youths-Lab/Rules/master/Rules/Clash/Sub/Proxy.txt",
    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mix.txt",
    "https://raw.githubusercontent.com/tbbatbb/Proxy/master/README.md",
    "https://raw.githubusercontent.com/xiyaowong/subscribe/main/README.md",
]


async def discover_sources() -> List[str]:
    try:
        async with aiohttp.ClientSession(headers={"user-agent": "submerger/1.0"}) as s:
            htmls = await asyncio.gather(*[_fetch(s, u) for u in SEARCH_PAGES])
        cands: Set[str] = set()
        for html in htmls:
            for m in RAW_RE.finditer(html or ""):
                url = m.group(0)
                if _plausible(url):
                    cands.add(url)
        ordered = sorted(
            cands,
            key=lambda u: ("refs/heads" in u, "/main/" in u, u.count("/")),
            reverse=True,
        )
        results = list(ordered)
    except Exception:
        results = []
    # Fallback to bundled list if network-restricted or low yield
    if len(results) < 20:
        merged = list(dict.fromkeys(results + FALLBACK_SOURCES))
        return merged[:50]
    return results


if __name__ == "__main__":
    print(json.dumps(asyncio.run(discover_sources()), indent=2, ensure_ascii=False))
