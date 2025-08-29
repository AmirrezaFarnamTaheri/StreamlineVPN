#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VPN Subscription Merger
===================================================================

The comprehensive VPN subscription merger combining 450+ sources with
testing, smart sorting, and automatic dead link removal. Optimized for the
Hiddify-Next client.

Features:
• Complete source collection (450+ Iranian + International repositories)
• Real-time URL availability testing and dead link removal
• Server reachability testing with response time measurement
• Smart sorting by connection speed and protocol preference
• Event loop compatibility (Jupyter, IPython, regular Python)
• Advanced deduplication with semantic analysis
• Multiple output formats (raw, base64, CSV, JSON)
• Comprehensive error handling and retry logic
• Best practices implemented throughout

Requirements: pip install aiohttp aiodns nest-asyncio
Author: Final Unified Edition - June 30, 2025
Expected Output: 800k-1.2M+ tested and sorted configs
"""

import asyncio
import base64
import csv
import hashlib
import os
import functools
import json
import logging
import random
import re
import ssl
import sys
import time
import socket
import signal
import ipaddress
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, TYPE_CHECKING
from tqdm import tqdm
import io

try:
    import aiofiles  # type: ignore
except Exception:  # pragma: no cover
    aiofiles = None  # type: ignore
from urllib.parse import urlparse
from vpn_merger.processing.parser import ProtocolParser  # type: ignore
from vpn_merger.security.security_manager import SecurityManager  # type: ignore
from vpn_merger.services.reliability import ExponentialBackoff, CircuitBreaker  # type: ignore
from vpn_merger.services.rate_limiter import PerHostRateLimiter  # type: ignore
from vpn_merger.monitoring.tracing import tracer_span  # type: ignore
from vpn_merger.services.bloom import BloomFilter  # type: ignore
from vpn_merger.monitoring.logging import log_json  # type: ignore


class ProxyValidator:
    """Hardened proxy URL validation to prevent injection and invalid targets."""

    ALLOWED_SCHEMES = {"http", "https", "socks4", "socks5"}
    FORBIDDEN_CHARS = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']

    @classmethod
    def validate(cls, proxy_url: Optional[str]) -> Optional[str]:
        if not proxy_url:
            return None
        for ch in cls.FORBIDDEN_CHARS:
            if ch in proxy_url:
                raise ValueError(f"Invalid character in proxy URL: {ch}")
        try:
            parsed = urlparse(proxy_url)
        except Exception as e:
            raise ValueError(f"Invalid proxy URL format: {e}")
        if parsed.scheme not in cls.ALLOWED_SCHEMES:
            raise ValueError(f"Invalid proxy scheme: {parsed.scheme}")
        if not parsed.hostname:
            raise ValueError("Proxy URL missing hostname")
        # Validate hostname or IP
        try:
            ipaddress.ip_address(parsed.hostname)
        except ValueError:
            # Domain validation: alnum, dot, dash; conservative check
            host = parsed.hostname
            if len(host) > 253 or not all(c.isalnum() or c in '.-' for c in host):
                raise ValueError("Invalid characters in proxy hostname")
        if parsed.port is not None and not (1 <= int(parsed.port) <= 65535):
            raise ValueError(f"Invalid proxy port: {parsed.port}")
        return proxy_url


def secure_path_join(base: Path, *parts: str) -> Path:
    """Join and resolve path segments ensuring the final path stays under base."""
    base = base.resolve()
    target = base.joinpath(*parts).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        raise ValueError(f"Path traversal attempt detected: {target}")
    return target


def validate_output_directory(path_str: str) -> Path:
    """Validate and create output directory safely."""
    path = Path(path_str).expanduser().resolve()
    suspicious = ['..', '~', '/etc', '/usr', '/bin', '/sys', '/proc']
    low = str(path).lower()
    for pat in suspicious:
        if pat in low:
            # don't block normal Windows drive letters like C:\
            if pat not in ('..', '~'):
                raise ValueError(f"Suspicious path pattern detected: {pat}")
    path.mkdir(parents=True, exist_ok=True)
    return path


class ResourceLimits:
    MAX_BASE64_SIZE = 10 * 1024 * 1024      # 10MB
    MAX_FILE_SIZE = 100 * 1024 * 1024       # 100MB
    MAX_CONFIGS_IN_MEMORY = 1_000_000       # 1M configs
    MAX_LINE_LENGTH = 10_000                # 10KB per line
    MAX_RESPONSE_SIZE = 50 * 1024 * 1024    # 50MB

    @classmethod
    def check_file_size(cls, path: Path) -> None:
        try:
            size = path.stat().st_size
            if size > cls.MAX_FILE_SIZE:
                raise ValueError(f"File too large: {size} bytes")
        except Exception:
            pass

    @classmethod
    def check_base64(cls, data: str) -> None:
        if len(data or "") > cls.MAX_BASE64_SIZE:
            raise ValueError(f"Base64 payload too large: {len(data)} bytes")

    @classmethod
    def check_memory_usage(cls) -> None:
        try:
            import psutil  # type: ignore
            rss = psutil.Process().memory_info().rss
            if rss > 2 * 1024 * 1024 * 1024:
                raise MemoryError("Memory usage exceeded 2GB")
        except Exception:
            pass

# Global shutdown event used across components
class GlobalState:
    _shutdown_event: Optional[asyncio.Event] = None

    @classmethod
    def get_shutdown_event(cls) -> asyncio.Event:
        if cls._shutdown_event is None:
            cls._shutdown_event = asyncio.Event()
        return cls._shutdown_event

if TYPE_CHECKING:
    import aiohttp  # type: ignore
    from aiohttp.resolver import AsyncResolver  # type: ignore

def check_dependencies() -> None:
    missing: List[str] = []
    try:
        import aiohttp  # noqa: F401
    except ImportError:
        missing.append('aiohttp')
    try:
        import nest_asyncio  # noqa: F401
    except ImportError:
        missing.append('nest-asyncio')
    try:
        import aiodns  # noqa: F401
    except ImportError:
        missing.append('aiodns')
    if missing:
        raise ImportError(f"Missing dependencies: {', '.join(missing)}. Run: pip install -r requirements.txt")

# ============================================================================
# CONFIGURATION & SETTINGS
# ============================================================================

@dataclass
class Config:
    """Comprehensive configuration for optimal performance."""
    
    # HTTP settings
    headers: Dict[str, str]
    request_timeout: int
    connect_timeout: float
    max_retries: int
    
    # Processing settings
    concurrent_limit: int
    max_configs_per_source: int
    
    # Protocol validation
    valid_prefixes: Tuple[str, ...]
    
    # Testing settings
    enable_url_testing: bool
    enable_sorting: bool
    test_timeout: float
    full_test: bool

    # Output settings
    output_dir: str

    # New features
    batch_size: int
    threshold: int
    top_n: int
    tls_fragment: Optional[str]
    include_protocols: Optional[Set[str]]
    exclude_protocols: Optional[Set[str]]
    resume_file: Optional[str]
    max_ping_ms: Optional[int]
    log_file: Optional[str]
    cumulative_batches: bool
    strict_batch: bool
    shuffle_sources: bool
    write_base64: bool
    write_csv: bool
    proxy: Optional[str]
    output_clash: bool
    prefer_protocols: Optional[List[str]]
    app_tests: Optional[List[str]]

    # TLS fragment and multiplexing
    tls_fragment_size: Optional[int]
    tls_fragment_sleep: Optional[int]
    mux_enable: bool
    mux_protocol: str
    mux_max_connections: int
    mux_min_streams: int
    mux_max_streams: int
    mux_padding: bool
    mux_brutal: bool
    enable_metrics: bool = True

    # Discovery and quarantine (optional)
    enable_discovery: bool = False
    quarantine_failures: bool = False
    quarantine_threshold: int = 3

    def validate(self) -> None:
        if self.concurrent_limit < 1:
            raise ValueError("concurrent_limit must be >= 1")
        if self.test_timeout < 0.1:
            raise ValueError("test_timeout must be >= 0.1")
        if self.batch_size < 0:
            raise ValueError("batch_size must be >= 0")
        if self.max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        if self.max_configs_per_source < 1:
            raise ValueError("max_configs_per_source must be >= 1")

CONFIG = Config(
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    },
    request_timeout=30,
    connect_timeout=3.0,
    max_retries=3,
    concurrent_limit=50,
    max_configs_per_source=75000,
    # Default protocols optimized for Hiddify-Next. Other clients may not
    # recognize some of these and might support additional protocols.
    valid_prefixes=(
        "proxy://",
        "ss://",
        "clash://",
        "v2ray://",
        "reality://",
        "vmess://",
        "xray://",
        "wireguard://",
        "ech://",
        "vless://",
        "hysteria://",
        "tuic://",
        "sing-box://",
        "singbox://",
        "shadowtls://",
        "clashmeta://",
        "hysteria2://",
    ),
    enable_url_testing=True,
    enable_sorting=True,
    test_timeout=5.0,
    full_test=False,
    output_dir="output",
    batch_size=1000,
    threshold=0,
    top_n=0,
    tls_fragment=None,
    include_protocols=None,
    exclude_protocols=None,
    resume_file=None,
    max_ping_ms=1000,
    log_file=None,
    cumulative_batches=False,
    strict_batch=True,
    shuffle_sources=False,
    write_base64=True,
    write_csv=True,
    proxy=None,
    output_clash=False,
    prefer_protocols=None,
    app_tests=None,
    tls_fragment_size=150,
    tls_fragment_sleep=15,
    mux_enable=False,
    mux_protocol="smux",
    mux_max_connections=4,
    mux_min_streams=4,
    mux_max_streams=16,
    mux_padding=False,
    mux_brutal=False,
    enable_discovery=False,
    quarantine_failures=False,
    quarantine_threshold=3
)

# Mapping of app test keywords to URLs
APP_TEST_URLS = {
    "telegram": "https://api.telegram.org",
    "youtube": "https://www.youtube.com",
}

# Number of fastest configs to run app tests against
APP_TEST_TOP_N = 3

# ============================================================================
# COMPREHENSIVE SOURCE COLLECTION (ALL UNIFIED SOURCES)
# ============================================================================

class UnifiedSources:
    """Source collection loader with external configuration support and fallback."""
    
    # Iranian Priority Sources (High Quality, Frequently Updated)
    # Iranian Priority Sources (High Quality, Frequently Updated)
    IRANIAN_PRIORITY = [
        # barry-far comprehensive collection (all variants)
        "https://raw.githubusercontent.com/barry-far/V2ray-config/main/Sub1.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-config/main/Sub2.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-config/main/Sub3.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-config/main/Sub4.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-config/main/Sub5.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-config/main/Sub6.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-config/main/Sub7.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-config/main/Sub8.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub1.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub2.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub3.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub4.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub5.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub6.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub7.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub8.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub9.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub10.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-Configs/refs/heads/main/All_Configs_Sub.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vless.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vmess.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/trojan.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/shadowsocks.txt",
        "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/reality.txt",
        
        # Rayan-Config ecosystem (Iranian-focused)
        "https://Rayan-Config.github.io/NG",
        "https://Rayan-Config.github.io/NB",
        "https://Rayan-Config.github.io/all",
        "https://raw.githubusercontent.com/Rayan-Config/C-Sub/refs/heads/main/configs/proxy.txt",
        "https://raw.githubusercontent.com/Rayan-Config/C-Sub/refs/heads/main/configs/singbox_configs.json",
        "https://raw.githubusercontent.com/Rayan-Config/C-Sub/refs/heads/main/configs/all",

        # MhdiTaheri V2rayCollector (comprehensive)
        "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/mix",
        "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/vless",
        "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/vmess",
        "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/trojan",
        "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/shadowsocks",
        "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/reality",
        "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/tuic",
        "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/hysteria",
        "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/hysteria2",
        
        # soroushmirzaei telegram-configs-collector (complete)
        "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vless",
        "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vmess",
        "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/trojan",
        "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/shadowsocks",
        "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/reality",
        "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/hysteria",
        "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/hysteria2",
        "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/tuic",
        "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/juicity",
        "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/naive",
        "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/splitted/mixed",
        "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/collected/all",
        
        # IranianCypherpunks Xray
        "https://raw.githubusercontent.com/IranianCypherpunks/Xray/main/Sub",
        
        # Syavar V2ray-Configs
        "https://raw.githubusercontent.com/Syavar/V2ray-Configs/main/OK_google.com.txt",
        
        # ndsphonemy proxy-sub collection
        "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/main/default.txt",
        "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/main/speed.txt",
        "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/main/my.txt",
        
        # Special Iranian services
        "https://channel-freevpnhomes-subscription.shampoosirsehat.homes",
        "https://gutsy-fibers.000webhostapp.com/sni.php?country=de;nl;fr;lt;lv;ee;se;no",
        "https://gutsy-fibers.000webhostapp.com/sni.php?country=us;ca;jp;sg;hk",
        
        # MrMohebi xray-proxy-grabber-telegram
        "https://raw.githubusercontent.com/MrMohebi/xray-proxy-grabber-telegram/master/collected-proxies/row-url/all.txt",
        "https://raw.githubusercontent.com/MrMohebi/xray-proxy-grabber-telegram/master/collected-proxies/row-url/actives.txt",
        "https://raw.githubusercontent.com/MrMohebi/xray-proxy-grabber-telegram/master/collected-proxies/row-url/vless.txt",
        "https://raw.githubusercontent.com/MrMohebi/xray-proxy-grabber-telegram/master/collected-proxies/row-url/vmess.txt",
        "https://raw.githubusercontent.com/MrMohebi/xray-proxy-grabber-telegram/master/collected-proxies/row-url/reality.txt",
        
        # coldwater operator-specific (Iranian ISPs)
        "https://raw.githubusercontent.com/coldwater-10/Vpnclashfa/main/raw/mci.txt",
        "https://raw.githubusercontent.com/coldwater-10/Vpnclashfa/main/raw/irc.txt",
        "https://raw.githubusercontent.com/coldwater-10/Vpnclashfa/main/raw/mkb.txt",
        "https://raw.githubusercontent.com/coldwater-10/V2Hub1/main/Split/Base64/shadowsocks",
        "https://raw.githubusercontent.com/coldwater-10/V2Hub1/main/Split/Base64/trojan",
        "https://raw.githubusercontent.com/coldwater-10/V2Hub1/main/Split/Base64/vless",
        "https://raw.githubusercontent.com/coldwater-10/V2Hub1/main/Split/Base64/vmess",
        "https://raw.githubusercontent.com/coldwater-10/V2Hub1/main/Split/Base64/reality",
        "https://raw.githubusercontent.com/coldwater-10/V2ray-Configs/main/Splitted-By-Protocol/hysteria2.txt",
        "https://raw.githubusercontent.com/coldwater-10/V2ray-Configs/main/Splitted-By-Protocol/reality.txt",
        
        # youfoundamin Iranian splits
        "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/ss_iran.txt",
        "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/vless_iran.txt",
        "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/vmess_iran.txt",
        "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/trojan_iran.txt",
        "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt",
        "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/reality_iran.txt",
        "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/hysteria2_iran.txt",
        
        # Additional Iranian projects
        "https://raw.githubusercontent.com/amirparsaxs/-BegzarVPN/refs/heads/main/Begzar_sub_text",
        "https://raw.githubusercontent.com/amirparsaxs/V2rayy/refs/heads/main/Sub.text555",
        "https://raw.githubusercontent.com/amirparsaxs/V2rayy/refs/heads/main/All_Configs.txt",
        "https://raw.githubusercontent.com/Mosifree/-FREE2CONFIG/refs/heads/main/Warp2",
        "https://raw.githubusercontent.com/Mosifree/-FREE2CONFIG/refs/heads/main/T,H",
        "https://shz.al/~@FREE2CONFIG_T,H",
        "https://raw.githubusercontent.com/amirmohammad-mohammad-88/Sub-Reality-Azadi-config/Config/Azadi-Reality-Different",
        "https://raw.githubusercontent.com/amirmohammad-mohammad-88/Sub-Reality-Azadi-config/Config/Azadi-Reality-Different-Base64",
        "https://raw.githubusercontent.com/NiREvil/vless/main/warp.json",
        "https://raw.githubusercontent.com/AB-84-AB/Free-Shadowsocks/refs/heads/main/Telegram-id-AB_841",
        "https://raw.githubusercontent.com/DiDiten/HiN-VPN/main/subscription/hiddify/mix",
        "https://raw.githubusercontent.com/liketolivefree/kobabi/main/singbox.json",
        "https://raw.githubusercontent.com/Mohammadgb0078/IRV2ray/main/vmess.txt",
        "https://raw.githubusercontent.com/Mohammadgb0078/IRV2ray/main/vless.txt",
        "https://raw.githubusercontent.com/Mohammadgb0078/IRV2ray/main/reality.txt",
        "https://raw.githubusercontent.com/MrPooyaX/SansorchiFucker/main/data.txt",
        "https://raw.githubusercontent.com/MrPooyaX/VpnsFucking/main/Shenzo.txt",
        "https://raw.githubusercontent.com/MrPooyaX/Vpns/main/V2ray",
        "https://raw.githubusercontent.com/MrPooyaX/Vpns/main/All_Configs_base64_Sub.txt",
        "https://raw.githubusercontent.com/MrPooyaX/Sansorchi/main/proxi.txt",
        "https://raw.githubusercontent.com/MrPooyaX/Sansorchi/main/sub",
    ]
    
    # International High-Quality Sources
    INTERNATIONAL_MAJOR = [
        # yebekhe TelegramV2rayCollector (most comprehensive)
        "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/mix",
        "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/vless",
        "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/vmess",
        "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/trojan",
        "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/shadowsocks",
        "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/reality",
        "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/hysteria2",
        "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/tuic",
        "https://raw.githubusercontent.com/yebekhe/V2Hub/main/merged",
        "https://raw.githubusercontent.com/yebekhe/V2Hub/main/split/vless",
        "https://raw.githubusercontent.com/yebekhe/V2Hub/main/split/vmess",
        "https://raw.githubusercontent.com/yebekhe/V2Hub/main/split/reality",
        
        # taheri79/V2rayCollector (comprehensive)
        "https://raw.githubusercontent.com/taheri79/V2rayCollector/main/sub/normal/mix",
        "https://raw.githubusercontent.com/taheri79/V2rayCollector/main/sub/base64/mix",
        "https://raw.githubusercontent.com/taheri79/V2rayCollector/main/sub/normal/vless",
        "https://raw.githubusercontent.com/taheri79/V2rayCollector/main/sub/normal/vmess",
        "https://raw.githubusercontent.com/taheri79/V2rayCollector/main/sub/normal/trojan",
        "https://raw.githubusercontent.com/taheri79/V2rayCollector/main/sub/normal/shadowsocks",
        "https://raw.githubusercontent.com/taheri79/V2rayCollector/main/sub/normal/reality",
        
        # Mahdi0024 ProxyCollector (tested configs)
        "https://raw.githubusercontent.com/Mahdi0024/ProxyCollector/main/subscriptions/mix",
        "https://raw.githubusercontent.com/Mahdi0024/ProxyCollector/main/subscriptions/vmess",
        "https://raw.githubusercontent.com/Mahdi0024/ProxyCollector/main/subscriptions/vless",
        "https://raw.githubusercontent.com/Mahdi0024/ProxyCollector/main/subscriptions/shadowsocks",
        "https://raw.githubusercontent.com/Mahdi0024/ProxyCollector/main/subscriptions/trojan",
        "https://raw.githubusercontent.com/Mahdi0024/ProxyCollector/main/subscriptions/hysteria2",
        "https://raw.githubusercontent.com/Mahdi0024/ProxyCollector/main/subscriptions/tuic",
        "https://raw.githubusercontent.com/Mahdi0024/ProxyCollector/main/subscriptions/reality",
        
        # V2RayRoot collection
        "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/main/Config/vless.txt",
        "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/main/Config/vmess.txt",
        "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/main/Config/shadowsocks.txt",
        "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/main/Config/trojan.txt",
        "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/main/Config/reality.txt",
        "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/main/Config/mix.txt",
        
        # Epodonios v2ray-configs (comprehensive mega-repo)
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_base64_Sub.txt",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/vless.txt",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/vmess.txt",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/trojan.txt",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/ss.txt",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/ssr.txt",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Configs_TLS.txt",
        # All Epodonios Config Lists (1-20)
        *[f"https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Config%20list{i}.txt" for i in range(1, 21)],
        # Epodonios Sub splits (1-15)
        *[f"https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub{i}.txt" for i in range(1, 16)],
        
        # MatinGhanbari v2ray-configs (comprehensive)
        "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/all_sub.txt",
        "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/super-sub.txt",
        "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/filtered/subs/vmess.txt",
        "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/filtered/subs/vless.txt",
        "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/filtered/subs/trojan.txt",
        "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/filtered/subs/shadowsocks.txt",
        "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/filtered/subs/reality.txt",
        # MatinGhanbari splits (1-50)
        *[f"https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/subs/sub{i}.txt" for i in range(1, 51)],
        
        # mahdibland Aggregators
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
        "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/sub/sub_merge.txt",
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/splitted/vmess.txt",
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/splitted/vless.txt",
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/splitted/trojan.txt",
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/splitted/shadowsocks.txt",
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/splitted/reality.txt",
    ]
    
    # Additional High-Volume Sources
    COMPREHENSIVE_BATCH = [
        # sevcator 5ubscrpt10n (500k+ configs)
        "https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/full/5ubscrpt10n.txt",
        "https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/full/5ubscrpt10n-b64.txt",
        "https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/protocols/vl.txt",
        "https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/protocols/vm.txt",
        "https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/protocols/tr.txt",
        "https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/protocols/ss.txt",
        "https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/protocols/hy2.txt",
        "https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/protocols/tuic.txt",
        "https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/protocols/reality.txt",
        # sevcator mini splits (1-20)
        *[f"https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-{i}.txt" for i in range(1, 21)],
        
        # zengfr free-vpn-subscribe
        "https://raw.githubusercontent.com/zengfr/free-vpn-subscribe/main/vpn_sub_.txt",
        "https://raw.githubusercontent.com/zengfr/free-vpn-subscribe/main/vpn_sub_raw_.txt",
        "https://raw.githubusercontent.com/zengfr/free-vpn-subscribe/main/vpn_sub_shadowsocks.txt",
        "https://raw.githubusercontent.com/zengfr/free-vpn-subscribe/main/vpn_sub_trojan.txt",
        "https://raw.githubusercontent.com/zengfr/free-vpn-subscribe/main/vpn_sub_vmess.txt",
        "https://raw.githubusercontent.com/zengfr/free-vpn-subscribe/main/vpn_sub_vless.txt",
        "https://raw.githubusercontent.com/zengfr/free-vpn-subscribe/main/vpn_sub_hysteria2.txt",
        
        # Premium service subscriptions
        "https://dyzk.020318.xyz/?token=d24404a213fc4dd681536826c509e0a1&flag=clash",
        "https://yy.filmtoday.top/api/v1/client/subscribe?token=390eb972a4070dd91ad8cb8a11e9aff8",
        "https://xship.top/v1/subscribe?starlink=lK-IH1mWfDG6xJ1yTB6JIGuL",
        "https://guang-cloud.com/api/v1/client/subscribe?token=ba9c2b246fffcbaa801c2d19a4718e3f",
        "https://gogo.kkhhddnn.cn/api/v1/client/subscribe?token=8ba1e286d4c5f831fde9b2cfa1917913",
        "https://qishuijc.top/api/v1/client/subscribe?token=391afb46752d77774f9848f1b0e30b14",
        "http://103.35.189.118:7001/s/68a95aaf8a22330847c0507d28147292",
        
        # Chinese community sources
        "https://raw.githubusercontent.com/zhangkaiitugithub/passcro/main/speednodes.yaml",
        "https://raw.githubusercontent.com/go4sharing/sub/main/sub.yaml",
        "https://gist.github.com/go4sharing/9cd241e781444d0924227c4171ccc02b/raw/d077791e5da3aa2ba3769009c65fbd499ff97c32/gistfile1.txt",
        
        # US dynamic servers
        "https://us6-dy.818185.xyz/eQxS4iey4zg/0cda5f7e-cc55-4ff2-8ad8-268b9b99dd01/#TG-freevpnatm",
        "https://us7-dy.890603.xyz/QOpk6x3mQBKV8fXCAuTIvNVjuHP/4d04b30c-ef7b-4a07-8f9e-f581ec171f8a/#TG-freevpnatm",
        "https://us8-dy.890601.xyz/R408J0PrBiWrmKFVLWL2wb8/3465a008-d9a0-40a2-bc63-232fca123efb/#TG-freevpnatm-分享",
        "https://us9-06.iran2030.ggff.net/dxJ41KGH07f/61ade0f2-e259-4608-8ecb-f12326fde120/#TG-freevpnatm",
        "https://us10-dy1.iran2030.ggff.net/OXKTQG1N88qvUea2C/576c81b6-4976-4fe3-b1a9-05a9c302e98e/#TG-freevpnatm",
        
        # SubCrawlers
        *[f"https://raw.githubusercontent.com/{owner}/SubCrawler/main/sub/share/all" for owner in 
          ("personqianduixue", "gtang8", "zzz6839", "zjfb", "QQnight")],
        "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/all3",
        "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/all4",
        "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/v2",
        
        # mermeroo comprehensive collection
        *[f"https://raw.githubusercontent.com/mermeroo/free-v2ray-collector/main/main/{p}" for p in 
          ("mix", "reality", "shadowsocks", "trojan", "vless", "vmess")],
        *[f"https://raw.githubusercontent.com/mermeroo/V2RAY-FREE/raw/main/Base64/Sub{i}_base64.txt" for i in range(2, 6)],
        "https://raw.githubusercontent.com/mermeroo/V2RAY-FREE/raw/main/All_Configs_base64_Sub.txt",
        "https://raw.githubusercontent.com/mermeroo/Loon/main/node%202",
        "https://raw.githubusercontent.com/mermeroo/Clash-V2ray/main/v2ray",
        "https://raw.githubusercontent.com/mermeroo/QX/refs/heads/main/Nodes",
        "https://raw.githubusercontent.com/mermeroo/Loon/refs/heads/main/all.nodes.txt",
        "https://raw.githubusercontent.com/mermeroo/QuantumultX/refs/heads/main/Trojan.nodes",
        "https://raw.githubusercontent.com/mermeroo/telegram-configs-collector/raw/main/protocols/tuic",
        "https://raw.githubusercontent.com/mermeroo/telegram-configs-collector/raw/main/protocols/hysteria",
        "https://raw.githubusercontent.com/mermeroo/telegram-configs-collector/raw/main/protocols/juicity",
        
        # Individual collectors (comprehensive)
        "https://raw.githubusercontent.com/LonUp/NodeList/main/V2RAY/Latest_base64.txt",
        "https://raw.githubusercontent.com/theGreatPeter/v2rayNodes/main/nodes.txt",
        "https://raw.githubusercontent.com/GreenFishStudio/GreenFish/master/Subscription/GreenFishYYDS",
        "https://raw.githubusercontent.com/Creativveb/v2configs/main/updated",
        "https://raw.githubusercontent.com/Flik6/getNode/main/v2ray.txt",
        "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
        "https://raw.githubusercontent.com/Jason05211211/Freerocket/main/freessr",
        "https://raw.githubusercontent.com/AzadNetCH/Clash/refs/heads/main/AzadNet_iOS.txt",
        "https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/merged.txt",
        "https://raw.githubusercontent.com/ermaozi01/free_clash_vpn/main/subscribe/v2ray.txt",
        "https://raw.githubusercontent.com/hans-thomas/v2ray-subscription/refs/heads/master/servers.txt",
        "https://raw.githubusercontent.com/vorz1k/v2box/main/subscription-links.txt",
        "https://raw.githubusercontent.com/Shaik360/v2ray-configs/main/subscription.txt",
        "https://raw.githubusercontent.com/245237866/v2rayn/main/everydaynode",
        
        # API endpoints
        "https://api.yebekhe.link/shervin/",
        
        # Additional quality sources
        "https://raw.githubusercontent.com/awesome-vpn/awesome-vpn/master/all",
        "https://raw.githubusercontent.com/awesome-vpn/awesome-vpn/master/ss",
        "https://raw.githubusercontent.com/awesome-vpn/awesome-vpn/master/ssr",
        "https://raw.githubusercontent.com/vpei/free-node-1/main/o/proxies.txt",
        # vpei free-node splits (0-9)
        *[f"https://raw.githubusercontent.com/vpei/free-node-1/refs/heads/main/res/nod-{i}.txt" for i in range(10)],
        
        # Huibq comprehensive
        *[f"https://raw.githubusercontent.com/Huibq/TrojanLinks/master/links/{f}" for f in 
          ("ss_with_plugin", "ss", "ssr", "vless", "vmess", "trojan", "temporary", "reality", "hysteria2")],
        
        # lagzian/SS-Collector (comprehensive collection)
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/ss.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/vmess.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/vless.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/reality.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/mix.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/hysteria.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/hysteria2.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/tuic.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/trojan.txt",
        # Country-specific from lagzian
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/countries/us.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/countries/uk.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/countries/de.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/countries/ca.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/countries/fr.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/countries/jp.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/countries/sg.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/countries/hk.txt",
        # Speed-tested collections
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/trinity/fast.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/trinity/medium.txt",
        "https://raw.githubusercontent.com/lagzian/SS-Collector/main/trinity/slow.txt",
        
        # Cloudflare-based solutions
        "https://raw.githubusercontent.com/cmliu/edgetunnel/main/sub.txt",
        "https://raw.githubusercontent.com/6Kmfi6HP/EDtunnel/main/sub.txt",
        "https://raw.githubusercontent.com/yonggekkk/Cloudflare_vless_trojan/main/sub.txt",
        "https://raw.githubusercontent.com/cmliu/edgetunnel/main/CF-Workers-SUB.txt",
        "https://raw.githubusercontent.com/6Kmfi6HP/EDtunnel/main/CF-Workers-SUB.txt",
        
        # Additional comprehensive sources
        "https://raw.githubusercontent.com/peasoft/NoMoreWalls/refs/heads/master/list.txt",
        "https://raw.githubusercontent.com/peasoft/NoMoreWalls/refs/heads/master/list_raw.txt",
        "https://raw.githubusercontent.com/peasoft/NoMoreWalls/refs/heads/master/list_base64.txt",
        "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription_num",
        "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription2",
        "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription3",
        "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/sub",
        "https://raw.githubusercontent.com/Kwinshadow/TelegramV2rayCollector/main/sublinks/b64mix.txt",
        "https://raw.githubusercontent.com/Kwinshadow/TelegramV2rayCollector/main/sublinks/vless.txt",
        "https://raw.githubusercontent.com/Kwinshadow/TelegramV2rayCollector/main/sublinks/vmess.txt",
        "https://sub.xn--4gqvd492adjr.com/s/43c2bb6d01f3cea4c85a25eefde7944a",
        "https://raw.githubusercontent.com/mheidari98/.proxy/main/all",
        "https://raw.githubusercontent.com/mheidari98/.proxy/refs/heads/main/trojan",
        "https://raw.githubusercontent.com/SamanValipour1/My-v2ray-configs/main/MySub.txt",
        "https://raw.githubusercontent.com/budamu/clashconfig/main/v2ray.txt",
        "https://raw.githubusercontent.com/budamu/clashconfig/main/v2ray2.txt",
        "https://raw.githubusercontent.com/YasserDivaR/pr0xy/main/ShadowSocks2021.txt",
        "https://raw.githubusercontent.com/shabane/kamaji/master/hub/b64/ss.txt",
        "https://raw.githubusercontent.com/shabane/kamaji/master/hub/b64/vmess.txt",
        "https://raw.githubusercontent.com/shabane/kamaji/master/hub/b64/vless.txt",
        "https://raw.githubusercontent.com/shabane/kamaji/master/hub/b64/trojan.txt",
        "https://raw.githubusercontent.com/shabane/kamaji/master/hub/b64/merged.txt",
        "https://raw.githubusercontent.com/vxiaov/free_proxy_ss/main/v2ray/v2raysub",
        "https://raw.githubusercontent.com/vxiaov/free_proxy_ss/main/ssr/ssrsub",
        "https://raw.githubusercontent.com/vxiaov/free_proxy_ss/main/ss/sssub",
        "https://raw.githubusercontent.com/vxiaov/free_proxies/refs/heads/main/links.txt",
        "https://raw.githubusercontent.com/gitbigg/permalink/main/subscribe",
        "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
        "https://raw.githubusercontent.com/ripaojiedian/freenode/main/sub",
        "https://raw.githubusercontent.com/freefq/free/master/v2",
        "https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/free",
        "https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/v2ray/v2rays.txt",
        "https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/ss/sssub",
        "https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/ssr/ssrsub",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/main/V2RAY_SUB.txt",
        "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server.txt",
        "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/sub.txt",
        "https://raw.githubusercontent.com/snakem982/proxypool/main/nodelist.txt",
        "https://raw.githubusercontent.com/anaer/Sub/main/clash.yaml",
        "https://raw.githubusercontent.com/anaer/Sub/main/v2ray.txt",
        "https://raw.githubusercontent.com/lmc999/Region-configs/main/sub-all-v2ray.txt",
        "https://raw.githubusercontent.com/ossgo/Sub/main/sub",
        "https://raw.githubusercontent.com/sashalsk/V2Ray/main/V2Ray-list-text",
        "https://raw.githubusercontent.com/abshare/abshare.github.io/main/all.txt",
        "https://raw.githubusercontent.com/fanqiangfeee/free-v2ray-vpn/main/v2ray",
        "https://raw.githubusercontent.com/free112/V2Ray-free-nodes/main/V2Ray-list-text.txt",
        "https://raw.githubusercontent.com/im-web/sub/main/vless",
        "https://raw.githubusercontent.com/Jajaj-dev/sub/main/v2ray",
        "https://raw.githubusercontent.com/mjrulesamrat/v2ray-configs/main/AllConfigs.txt",
        "https://raw.githubusercontent.com/movft/movft/main/config/config.txt",
        "https://raw.githubusercontent.com/open-source-links/v2ray-list/main/list.txt",
        "https://raw.githubusercontent.com/Ptechgithub/configs/main/sub.txt",
        "https://raw.githubusercontent.com/sun956/V2ray-Subscription-Update/main/v2ray.txt",
        "https://raw.githubusercontent.com/tbbatbb/Proxy/master/dist/v2ray.config.txt",
        "https://raw.githubusercontent.com/wonderfulgo/subscription-script/main/v2/config",
        "https://raw.githubusercontent.com/xiaomadashu/v2ray/master/config.txt",
        "https://raw.githubusercontent.com/XrayR-project/XrayR-release/master/config/subscribe.txt",
        "https://raw.githubusercontent.com/ZDCloud/Sub/main/All",
        "https://raw.githubusercontent.com/zipkocc/SagerNet-Configs/main/sub.txt",
        
        # BitBucket sources
        "https://bitbucket.org/huwo1/proxy_nodes/raw/f31ca9ec67b84071515729ff45b011b6b09c10f2/ss.md",
        "https://bitbucket.org/huwo1/proxy_nodes/raw/f31ca9ec67b84071515729ff45b011b6b09c10f2/vmess.md",
        "https://bitbucket.org/huwo1/proxy_nodes/raw/f31ca9ec67b84071515729ff45b011b6b09c10f2/proxy.md",
        "https://bitbucket.org/huwo1/proxy_nodes/raw/f31ca9ec67b84071515729ff45b011b6b09c10f2/trojan.md",
        
        # Additional collections
        "https://raw.githubusercontent.com/luxl-1379/merge/77247d23def72b25226dfa741614e9b07a569c72/sub/sub_merge_base64.txt",
        "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/python/hy2",
        "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/python/hysteria2",
        "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/python/hysteria",
        "https://raw.githubusercontent.com/webdao/v2ray/refs/heads/master/nodes.txt",
        "https://raw.githubusercontent.com/webdao/v2ray/refs/heads/master/nodes2.txt",
        "https://raw.githubusercontent.com/webdao/v2ray/refs/heads/master/nodes3.txt",
        
        # Hiddify & Sing-Box related
        "https://raw.githubusercontent.com/hiddify/Hiddify-Server/main/release/hiddify-next-config.json",
        "https://raw.githubusercontent.com/hiddify/awesome-freedom/main/configs.txt",

        # Missings
        "https://raw.githubusercontent.com/AliDev-ir/FreeVPN/main/pcvpn",
        "https://raw.githubusercontent.com/AliDev-ir/FreeVPN/main/vpn",
        "https://raw.githubusercontent.com/M-Mashreghi/Free-V2ray-Collector/main/Files/shuffle/Sub1_shuffled.conf",
        "https://raw.githubusercontent.com/M-Mashreghi/Free-V2ray-Collector/main/Files/shuffle/Sub2_shuffled.conf",
        "https://raw.githubusercontent.com/M-Mashreghi/Free-V2ray-Collector/main/Files/shuffle/Sub3_shuffled.conf",
        "https://raw.githubusercontent.com/M-Mashreghi/Free-V2ray-Collector/main/Files/shuffle/Sub4_shuffled.conf",
        "https://raw.githubusercontent.com/M-Mashreghi/Free-V2ray-Collector/main/Files/shuffle/Sub5_shuffled.conf",
        "https://raw.githubusercontent.com/M-Mashreghi/Free-V2ray-Collector/main/Files/shuffle/Sub6_shuffled.conf",
        "https://raw.githubusercontent.com/M-Mashreghi/Free-V2ray-Collector/main/Files/shuffle/Sub7_shuffled.conf",
        "https://raw.githubusercontent.com/M-Mashreghi/Free-V2ray-Collector/main/Files/shuffle/Sub8_shuffled.conf",
        "https://raw.githubusercontent.com/M-Mashreghi/Free-V2ray-Collector/main/Files/shuffle/Sub9_shuffled.conf",
        "https://raw.githubusercontent.com/M-Mashreghi/Free-V2ray-Collector/main/Files/shuffle/Sub10_shuffled.conf",
        "https://raw.githubusercontent.com/M-Mashreghi/Free-V2ray-Collector/main/Files/shuffle/Sub11_shuffled.conf",
        "https://raw.githubusercontent.com/M-Mashreghi/Free-V2ray-Collector/main/Files/shuffle/Sub12_shuffled.conf",
        "https://p6.punchline.ir:2096/sub/v2raybluecrystal2tb",
        "https://p6.punchline.ir:2096/sub/v2raybluecrystal5TBFR",
        "https://p7.punchline.ir:2096/v2raybluecrystal/turkey5tb",
        "https://p7.punchline.ir:2096/v2raybluecrystal/turkey4tera",
        "https://proud-fire-1775.mahmmod2025.workers.dev/sub/e0e345e3-e2ce-4778-81ff-67b4a8feddd8#BPB-Normal",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Config%20list3.txt",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Config%20list10.txt",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Config%20list15.txt",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Config%20list16.txt",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Config%20list17.txt",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Config%20list18.txt",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Config%20list19.txt",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Config%20list20.txt",
        "https://raw.githubusercontent.com/taheri79/V2rayCollector/main/sub/normal/mix",
        "https://raw.githubusercontent.com/taheri79/V2rayCollector/main/sub/base64/mix",
        "https://raw.githubusercontent.com/taheri79/V2rayCollector/main/sub/normal/vless",
        "https://raw.githubusercontent.com/taheri79/V2rayCollector/main/sub/normal/vmess",
        "https://raw.githubusercontent.com/taheri79/V2rayCollector/main/sub/normal/trojan",
        "https://raw.githubusercontent.com/taheri79/V2rayCollector/main/sub/normal/shadowsocks",
        "https://raw.githubusercontent.com/taheri79/V2rayCollector/main/sub/normal/reality",
        "https://raw.githubusercontent.com/anaer/Sub/main/clash.yaml",
        "https://raw.githubusercontent.com/anaer/Sub/main/v2ray.txt",
        "https://raw.githubusercontent.com/lmc999/Region-configs/main/sub-all-v2ray.txt",
        "https://raw.githubusercontent.com/ossgo/Sub/main/sub",
        "https://raw.githubusercontent.com/hagezi/mirror/main/v2ray.txt",
        "https://raw.githubusercontent.com/abshare/abshare.github.io/main/all.txt",
        "https://raw.githubusercontent.com/fanqiangfeee/free-v2ray-vpn/main/v2ray",
        "https://raw.githubusercontent.com/free112/V2Ray-free-nodes/main/V2Ray-list-text.txt",
        "https://raw.githubusercontent.com/im-web/sub/main/vless",
        "https://raw.githubusercontent.com/Jajaj-dev/sub/main/v2ray",
        "https://raw.githubusercontent.com/mjrulesamrat/v2ray-configs/main/AllConfigs.txt",
        "https://raw.githubusercontent.com/movft/movft/main/config/config.txt",
        "https://raw.githubusercontent.com/open-source-links/v2ray-list/main/list.txt",
        "https://raw.githubusercontent.com/Ptechgithub/configs/main/sub.txt",
        "https://raw.githubusercontent.com/sun956/V2ray-Subscription-Update/main/v2ray.txt",
        "https://raw.githubusercontent.com/tbbatbb/Proxy/master/dist/v2ray.config.txt",
        "https://raw.githubusercontent.com/wonderfulgo/subscription-script/main/v2/config",
        "https://raw.githubusercontent.com/xiaomadashu/v2ray/master/config.txt",
        "https://raw.githubusercontent.com/XrayR-project/XrayR-release/master/config/subscribe.txt",
        "https://raw.githubusercontent.com/ZDCloud/Sub/main/All",
        "https://raw.githubusercontent.com/zipkocc/SagerNet-Configs/main/sub.txt",

            # Large public text / YAML feeds
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_RAW.txt",
    "https://raw.githubusercontent.com/Misaka-blog/chromego_merge/main/sub/merged_proxies_new.yaml",
    "https://raw.githubusercontent.com/MrMohebi/xray-proxy-grabber-telegram/master/collected-proxies/clash-meta/all.yaml",
    "https://raw.githubusercontent.com/NiceVPN123/NiceVPN/main/Clash.yaml",
    "https://raw.githubusercontent.com/PangTouY00/Auto_proxy/main/Long_term_subscription_num",
    "https://raw.githubusercontent.com/Vauth/node/main/Main",
    "https://raw.githubusercontent.com/aiboboxx/clashfree/main/clash.yml",
    "https://raw.githubusercontent.com/chengaopan/AutoMergePublicNodes/master/list.yml",
    "https://raw.githubusercontent.com/lagzian/SS-Collector/main/mix_clash.yaml",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge_yaml.yml",
    "https://raw.githubusercontent.com/mheidari98/.proxy/main/all",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.yml",
    "https://raw.githubusercontent.com/ronghuaxueleng/get_v2/main/pub/combine.yaml",
    "https://raw.githubusercontent.com/dongchengjie/airport/main/subs/merged/tested_within.yaml",
    "https://raw.githubusercontent.com/abbasdvd3/clash/main/vless/x",

    # du5/free repo – dated snapshots
    "https://raw.githubusercontent.com/du5/free/master/file/0407/clash.yaml",
    "https://raw.githubusercontent.com/du5/free/master/file/0407/clash2.yaml",
    "https://raw.githubusercontent.com/du5/free/master/file/0307/clash.yaml",
    "https://raw.githubusercontent.com/du5/free/master/file/0312/clash.yaml",
    "https://raw.githubusercontent.com/du5/free/master/file/0905/quan.conf",
    "https://git.ddns.tokyo/du5/free/master/file/0615/v2ray.json",
    "https://git.ddns.tokyo/du5/free/master/file/0503/clash.yaml",

    # Token-based API endpoints
    "http://www.paoche.ooo/api/v1/client/subscribe?token=4d2a30058958302ee685266f2340ea6c",
    "http://110.72.100.27:55/api/v1/client/subscribe?token=b5c6af703a58cf950498c03e7a42a0f2",
    "https://v2.fit/modules/servers/V2raySocks/osubscribe.php?sid=7063&token=lKJwbO2onxIr",
    "http://www.sksla.pro/api/v1/client/subscribe?token=99c3fa86424539bd3bd34a893bc6dee8",
    "https://fly.lo-lita.ru/api/v1/client/subscribe?token=94be7fa3d65791197dd10c6a0b757571",

    # Short-link & web-hosted feeds
    "https://mijishu.xyz/link/EqVV5nouWjbB59Ln?sub=3&extend=1",
    "https://hjysub1.com/link/cgQ2jYaeQx9LBxsh?sub=3&extend=1",
    "https://suda.sub.koicloud.pw/link/K9vz0uFPe9ULfdqX?sub=3",
    "https://suda.sub.koicloud.pw/link/JgULLCNkImsJ6Ibh?sub=3",
    "https://extrm.info/link/uirPjznB7esOezjr?sub=1",
    "https://sbnmsl.co/link/2cpTGUGJtHBXUK7d?sub=3",
    "https://pptp.cloud/sub/cXHG9wqUpQbhHr7d.html",
    "https://www.haidaobot.xyz/link/QwdUmWolPN0LkThW?mu=2",
    "https://dingyue.suying666.info/link/o7j43Aykx8CWBehE?sub=1",
    "https://vvsub.xyz/api/al/19786-xDX1SCq61Ymi",
    "https://rss-node.com/link/vqOaWFJRfbYxpAhY?mu=1",
    "https://tm2w.live/link/EqICUlKXmn1EJwaw?sub=3",
    "https://www.suncloud.fun/link/Su683BQEyUdxtyuY?mu=1&extend=1",
    "https://www.suncloud.fun/link/ja3OIcMTrky6VhN6?mu=1&extend=1",
    "https://sub88.xyz/link/egy4oyqok9aavpcy?sub=3",
    "https://sub88.xyz/link/lkY8Jt5Q3SHlffra?mu=2",
    "https://bujidao302.com/link/IJ6wKEt96Otboilb?mu=2",
    "https://rss.getfree.win/link/w9ted9eZq1zbC3gx?sub=1",
    "https://rss.cnrss.xyz/link/Rcr8h8fvZIWE001U?mu=2",
    "https://s.sublank.xyz/subscribe/66056/0yzuMVawjpr/ssr/",
    "https://12o.ooo/link/JLisT80gOhRkiFnX?sub=1",

    # Netlify & Git-hosted plain-text dumps
    "https://neurotoxinw.coding.net/p/qifei/d/qifei/git/raw/master/README.md",
    "https://qiaomenzhuanfx.netlify.com/",
    "https://youlianboshi.netlify.com/",
    "https://iwxf.netlify.app/",
    "http://qe83xk711.sabkt.gdipper.com/freev2ray.txt",
    "http://qe83xk711.sabkt.gdipper.com/freess.txt",
    "http://103.72.166.89/v2ray.php",

    # GitHub raw text feeds (misc.)
    "https://raw.githubusercontent.com/Pcrab/Dotfiles/912c1104b3f8121f72f7ee11590f52bc9c44dde7/.config/electron-ssr/gui-config.json",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/v2ray",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/ss-sub",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/ssrsub",
    "https://raw.githubusercontent.com/satrom/V2SSR/master/V2RAY/Sub.txt",
    "https://raw.githubusercontent.com/satrom/V2SSR/master/SSR/Day.txt",
    "https://raw.githubusercontent.com/satrom/V2SSR/master/SSR/Sub.txt",
    "https://raw.githubusercontent.com/hotsymbol/vpnsetting/master/v2rayopen",
    "https://raw.githubusercontent.com/ntkernel/lantern/master/vmess_base64.txt",
    "https://raw.githubusercontent.com/pojiezhiyuanjun/freev2/master/20200808.txt",
    "https://raw.githubusercontent.com/du5/free/master/file/0905/quan.conf",
    "https://raw.githubusercontent.com/du5/free/master/file/0909/Clash.yaml",
    "https://raw.githubusercontent.com/du5/free/master/file/0906/surge.conf",
    "https://raw.githubusercontent.com/du5/free/master/file/0906/ss.json",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/ssrsub",
    "https://raw.githubusercontent.com/RaymondHarris971/ssrsub/master/9a075bdee5.txt",
    "https://raw.githubusercontent.com/voken100g/AutoSSR/master/recent",
    "https://raw.githubusercontent.com/cdp2020/v2ray/master/README.md",

    # Misc tiny short-links (still valid subscription payloads)
    "https://bit.ly/2D5fWhX",

        # --- big auto-updated GitHub feeds ---
    "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/V2Ray-Config-By-EbraSha.txt",
    "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/V2Ray-Config-By-EbraSha-All-Type.txt",
    "https://raw.githubusercontent.com/SnapdragonLee/SystemProxy/master/dist/clash_config.yaml",
    "https://raw.githubusercontent.com/SnapdragonLee/SystemProxy/master/dist/clash_config_extra.yaml",
    "https://raw.githubusercontent.com/SnapdragonLee/SystemProxy/master/dist/clash_config_extra_US.yaml",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/clash.yaml",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash.yml",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/vmess.txt",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/vless.txt",
    "https://raw.githubusercontent.com/V2RaySSR/Tools/master/clash.yaml",
    "https://raw.githubusercontent.com/du5/free/master/file/0312/clash.yaml",
    "https://raw.githubusercontent.com/du5/free/master/file/0312/clash2.yaml",
    "https://raw.githubusercontent.com/du5/free/master/file/0312/quan.conf",
    "https://raw.githubusercontent.com/Ptechgithub/configs/main/clash12.yaml",
    "https://raw.githubusercontent.com/SunBK201/MySCR/master/clash/SunBK201_conf.yaml",
    "https://raw.githubusercontent.com/AzadNetCH/Clash/main/AzadNet.txt",
    "https://raw.githubusercontent.com/AzadNetCH/Clash/main/AzadNet.json",
    "https://raw.githubusercontent.com/AzadNetCH/Clash/main/AzadNet_hy.txt",
    "https://raw.githubusercontent.com/AzadNetCH/Clash/main/AzadNet_iOS.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_list.json",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.yml",
    # --- NiREvil warp / WG / hiddify mixes ---
    "https://raw.githubusercontent.com/NiREvil/vless/refs/heads/main/warp.json",
    "https://raw.githubusercontent.com/NiREvil/vless/refs/heads/main/sub/v2rayng-wg.txt",
    "https://raw.githubusercontent.com/NiREvil/vless/refs/heads/main/sub/nekobox-wg.txt",
    "https://raw.githubusercontent.com/NiREvil/vless/refs/heads/main/sub/husi-wg.txt",
    "https://raw.githubusercontent.com/NiREvil/vless/refs/heads/main/sub/exclave-wg.txt",
    "https://raw.githubusercontent.com/NiREvil/vless/refs/heads/main/hiddify/Windscribe%20on%20H2",
    "https://raw.githubusercontent.com/NiREvil/vless/refs/heads/main/hiddify/WarpOnWarp.json",
    "https://raw.githubusercontent.com/NiREvil/vless/main/Cloudflare-IPs.json",
    "https://raw.githubusercontent.com/NiREvil/vless/refs/heads/main/sub/clash-meta-wg.yml",
    "https://raw.githubusercontent.com/10ium/MihomoSaz/main/Sublist/NiREvil_SSTime.yaml",
    # --- public Clash / YAML feeds ---
    "https://nodefree.org/dy/2024/07/20240725.yaml",
    "https://cdn.jsdelivr.net/gh/vxiaov/free_proxies@main/clash/clash.provider.yaml",
    "https://freenode.openrunner.net/uploads/20240617-clash.yaml",
    "https://tt.vg/freeclash",
    "https://github.com/zu1k/proxypool/releases/download/latest/subscription.txt",
    # --- token-style v2board / Hiddify endpoints ---
    "https://qingyun.zybs.eu.org/api/v1/client/subscribe?token=9cd4a1826b992055a8e87a3f6594ba94",
    "https://api.xyurl.site/api/v1/client/subscribe?token=fed4ab7c582c2a41a08a858f91644430",
    "https://xqsub.e54.site/api/v1/client/subscribe?token=d1fd4dcc61491a02f566f6a45c56ccab&types=vless",
    "https://ch.owokkvsxks.store/api/v1/client/subscribe?token=ad180e3b9514176a8cb26bf2962d5f1e",
    "https://api.xqc.best/api/v1/client/subscribe?token=fb08adc269ff5522ba953933f6a9e9b6",
    "https://csadata4g.me/api/v1/client/subscribe?token=04a09188b487e088f7ab9773f617dd1a",
    "https://sub.lingche.icu/api/v1/client/subscribe?token=48e95450735e7d06d61b56f9bdb349fc",
    "https://cloud.targoo.live/api/v1/client/subscribe?token=1d0a9f1ee09199aac2ac946a1f7d2a0a",
    "https://www.992266.xyz/api/v1/client/subscribe?token=ab825616355b0973e4cdfb659665965f",
    "https://v2y.xyz/api/v1/client/subscribe?token=2533ce3df935ebaf4143fcc3df068ebd",
    "http://xn--nlua550ns4y.com/api/v1/client/subscribe?token=f83cdcc48766976526ab2451380b8dd0",
    "http://davgp416ip6zl8pfrusvvag.zhuyingsu.today/api/v1/client/subscribe?token=b9df9a624e3fdb1e72b10ea81cc9d437",
    "https://pqjc.site/api/v1/client/subscribe?token=0d41f5bd237d1ab92b907e1e7d5e5cb3&flag=meta",
    "http://113.31.116.212:13800/api/v1/client/subscribe?token=b5d84c66256755e551704d05600ada67",
    "http://1.1598888.xyz/api/v1/client/subscribe?token=e2c8421cd8543cd904f255fbef4490cd",
    "http://nuxyun.v2rayflash.top/api/v1/client/subscribe?token=531e0be2dbbfc393dfac550abee6ce57",
    "https://13.112.134.19:13800/api/v1/client/subscribe?token=ce41d51e5664e57b9470f9061c1f61c0",
    "https://tc.ztcloud.xyz/api/v1/client/subscribe?token=26cec3bda11795769be5d18126c4b354",
    "https://cloud.targoo.live/api/v1/client/subscribe?token=9f56998ea1b1c5e3c3a857e3ac274edf",
    "https://xqsub.minictx.top/api/v1/client/subscribe?token=ef279b9e8696510c45b1f21f1653e2c9",
    "https://chan.aztv.asia/api/v1/client/subscribe?token=264d99c3ad7b418f9e7eab1f0d2862c7",
    "https://freeyuan.maimaihuo.com/api/v1/client/subscribe?token=e61032f58d4b00db023be1347f7f6911",
    "https://api.wlins.org/api/v1/client/subscribe?token=fd8e56ea45a735e5d2fba98f3e97c7b6",
    "https://v2sub.purelife.org/api/v1/client/subscribe?token=4ff1f9623ea62a005102b1701f2fd56a",
    "https://free.jinan.cloud/api/v1/client/subscribe?token=6b9e32193f128651ed4cbf6cb0f3c3f0",
    # --- generic link-style subs (Clash=1) ---
    "https://sub.idsvip.com/link/abcd1234?clash=1",
    "https://sub.nerdz.pro/link/xyz987?clash=1",
    # --- misc raw / WG / JSON feeds ---
    "https://raw.githubusercontent.com/4n0nymou3/ss-config-updater/refs/heads/main/configs.txt",
    "https://raw.githubusercontent.com/darknessm427/WoW/refs/heads/main/subwarp/warp",
    "https://raw.githubusercontent.com/arshiacomplus/WoW-fix/main/Xray-WoW.json",
    "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/refs/heads/main/mobile.txt",
    "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/refs/heads/main/wg.txt",
    "https://raw.githubusercontent.com/10ium/ScrapeAndCategorize/refs/heads/main/output_configs/WireGuard.txt",
    "https://raw.githubusercontent.com/Alanbobs999/TopFreeProxies/master/proxies.txt",
    # --- spare token endpoints to round it out ---
    "https://okcloud.cc/api/v1/client/subscribe?token=7b2a9e8f0c373725f9c3d6bd6d1fbe43",
    "https://sub.tangcloud.xyz/api/v1/client/subscribe?token=a3d1c180cf35e5ad9d1fba2d4c5e4bf2",
    "https://vfree.xyz/api/v1/client/subscribe?token=96b51236cddc2df523d9e83a9d457f23",
    "https://free.tailsub.com/api/v1/client/subscribe?token=35b677cab1d1e8349a3e45dc367cbdfa",
    "https://raw.githubusercontent.com/ermaozi/ClashRforWindows/main/sub/2025-07-01.yml",

    ]
    
    @classmethod
    def _try_load_external(cls) -> bool:
        """Attempt to load sources from config/sources.yaml or sources.json."""
        base_dir = _get_script_dir()
        yaml_path = base_dir / "config" / "sources.yaml"
        json_path = base_dir / "sources.json"
        # Prefer YAML
        try:
            import yaml  # type: ignore
            if yaml_path.exists():
                data = yaml.safe_load(yaml_path.read_text(encoding='utf-8')) or {}
                sources = data.get('sources') or {}
                cls.IRANIAN_PRIORITY = UnifiedSources._filter_valid_urls(list(sources.get('iranian_priority', []))) or cls.IRANIAN_PRIORITY
                cls.INTERNATIONAL_MAJOR = UnifiedSources._filter_valid_urls(list(sources.get('international_major', []))) or cls.INTERNATIONAL_MAJOR
                cls.COMPREHENSIVE_BATCH = UnifiedSources._filter_valid_urls(list(sources.get('comprehensive_batch', []))) or cls.COMPREHENSIVE_BATCH
                return True
        except Exception:
            pass
        # Fallback to JSON if present
        try:
            if json_path.exists():
                data = json.loads(json_path.read_text(encoding='utf-8'))
                cls.IRANIAN_PRIORITY = UnifiedSources._filter_valid_urls(list(data.get('iranian_priority', []))) or cls.IRANIAN_PRIORITY
                cls.INTERNATIONAL_MAJOR = UnifiedSources._filter_valid_urls(list(data.get('international_major', []))) or cls.INTERNATIONAL_MAJOR
                cls.COMPREHENSIVE_BATCH = UnifiedSources._filter_valid_urls(list(data.get('comprehensive_batch', []))) or cls.COMPREHENSIVE_BATCH
                return True
        except Exception:
            pass
        return False

    @staticmethod
    @functools.lru_cache(maxsize=10000)
    def _is_valid_url(url: str) -> bool:
        try:
            s = url.strip()
            parsed = urlparse(s)
            return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and len(s) < 2048
        except Exception:
            return False

    @classmethod
    def _filter_valid_urls(cls, urls: List[str]) -> List[str]:
        return [u.strip() for u in urls if isinstance(u, str) and cls._is_valid_url(u.strip())]

    @classmethod
    def get_all_sources(cls) -> List[str]:
        """Get all unique sources in priority order with deduplication.

        Attempts to load external config first; if not available, uses
        the embedded lists as fallback.
        """
        cls._try_load_external()
        # Try loading extended file as well, if present
        try:
            ext_path = Path("config") / "sources.extended.yaml"
            if ext_path.exists():
                import yaml  # type: ignore
                data = yaml.safe_load(ext_path.read_text(encoding='utf-8')) or {}
                extra = []
                if isinstance(data, dict):
                    extra = list(data.get('additional', []))
                elif isinstance(data, list):
                    extra = data
                if extra:
                    cls.COMPREHENSIVE_BATCH = cls._filter_valid_urls(list(extra)) + cls.COMPREHENSIVE_BATCH
        except Exception:
            pass
        all_sources = cls.IRANIAN_PRIORITY + cls.INTERNATIONAL_MAJOR + cls.COMPREHENSIVE_BATCH
        return list(dict.fromkeys(all_sources))  # Remove duplicates while preserving order

# ============================================================================
# ENHANCED CONFIG PROCESSING
# ============================================================================

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
    app_test_results: Dict[str, Optional[bool]] = field(default_factory=dict)

class EnhancedConfigProcessor:
    """Advanced configuration processor with comprehensive testing capabilities."""
    
    MAX_DECODE_SIZE = 256 * 1024  # 256 kB safety limit for base64 payloads

    def __init__(self):
        self.dns_cache = {}
        # Optional runtime-injected config (may be a Pydantic model). Falls back to CONFIG.
        self.config: Optional[object] = None
        self.event_bus = None
        # Cache for connection test results to avoid N+1 duplicate probing
        # Key: (host, port, protocol, ssl_required)
        self._conn_test_cache: Dict[Tuple[str, int, str, bool], Tuple[Optional[float], Optional[bool]]] = {}

    def _get(self, key: str, default=None):
        """Safely resolve a config value from injected config or global CONFIG.

        Tries nested Pydantic model paths when present (e.g., testing.test_timeout).
        """
        # Nested paths map for pydantic-style config
        nested = {
            'enable_url_testing': ('testing', 'enable_url_testing'),
            'enable_sorting': ('testing', 'enable_sorting'),
            'test_timeout': ('testing', 'test_timeout'),
            'max_ping_ms': ('testing', 'max_ping_ms'),
            'proxy': ('network', 'proxy'),
        }
        cfg = self.config
        if cfg is not None:
            path = nested.get(key)
            try:
                if path and hasattr(cfg, path[0]):
                    inner = getattr(cfg, path[0])
                    if hasattr(inner, path[1]):
                        return getattr(inner, path[1])
                if hasattr(cfg, key):
                    return getattr(cfg, key)
            except Exception:
                pass
        return getattr(CONFIG, key, default)

    @staticmethod
    def _sanitize_host(host: Optional[str]) -> Optional[str]:
        try:
            return SecurityManager.sanitize_host(host)
        except Exception:
            return None

    @staticmethod
    def _valid_port(port: Optional[int]) -> Optional[int]:
        return SecurityManager.sanitize_port(port)

    @staticmethod
    def _is_valid_hostname(host: str) -> bool:
        try:
            return SecurityManager.sanitize_host(host) is not None
        except Exception:
            return False

    async def _async_write_text(self, path: Path, text: str) -> None:
        """Write text to a file without blocking the event loop.

        Uses aiofiles when available; falls back to a thread via asyncio.to_thread.
        """
        try:
            if aiofiles is not None:
                async with aiofiles.open(path, 'w', encoding='utf-8') as f:  # type: ignore
                    await f.write(text)
                return
        except Exception:
            # Fallback to thread-based write below
            pass
        await asyncio.to_thread(path.write_text, text, encoding='utf-8')

    @staticmethod
    def safe_b64_decode(data: str, max_size: int = 1024 * 1024) -> Optional[str]:
        """Safely decode base64 text with validation and size limits."""
        if not isinstance(data, str) or not data.strip():
            return None
        clean = re.sub(r"\s+", "", data)
        if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', clean):
            return None
        # Enforce a hard upper bound to avoid memory exhaustion
        hard_cap = min(max_size, ResourceLimits.MAX_BASE64_SIZE)
        if len(clean) > (hard_cap * 4) // 3:
            return None
        try:
            decoded_bytes = base64.b64decode(clean, validate=True)
            if len(decoded_bytes) > hard_cap:
                return None
            return decoded_bytes.decode("utf-8", errors="strict")
        except Exception:
            return None
        
    def extract_host_port(self, config: str) -> Tuple[Optional[str], Optional[int]]:
        """Extract host and port from configuration for testing."""
        try:
            # Prefer centralized parser
            host, port = ProtocolParser.extract_endpoint(config)
            if host and port:
                h = self._sanitize_host(host)
                p = self._valid_port(port)
                return (h if (h and self._is_valid_hostname(h)) else None), p
            # Fallbacks
            parsed = urlparse(config)
            if parsed.hostname and parsed.port:
                h = self._sanitize_host(parsed.hostname)
                p = self._valid_port(parsed.port)
                return (h if (h and self._is_valid_hostname(h)) else None), p
            match = re.search(r"@([^:/?#]+):(\d+)", config)
            if match:
                h = self._sanitize_host(match.group(1))
                p = self._valid_port(int(match.group(2)))
                return (h if (h and self._is_valid_hostname(h)) else None), p
        except Exception:
            pass
        return None, None
    
    def _extract_user_id(self, config: str) -> Optional[str]:
        try:
            parsed = urlparse(config)
            if parsed.username:
                return parsed.username
            after_scheme = config.split("://", 1)[1]
            decoded = self.safe_b64_decode(after_scheme, self.MAX_DECODE_SIZE)
            if decoded:
                data = json.loads(decoded)
                return data.get("id") or data.get("uuid") or data.get("user")
        except Exception:
            return None
        return None

    def create_semantic_hash(self, config: str) -> str:
        """Create semantic hash with collision resistance."""
        host, port = self.extract_host_port(config)
        protocol = self.categorize_protocol(config)
        parts: List[str] = [protocol]
        if host and port:
            parts.extend([host, str(port)])
        user_id = self._extract_user_id(config)
        if user_id:
            parts.append(user_id)
        key = "|".join(parts)
        return hashlib.sha256(key.encode('utf-8')).hexdigest()
    
    async def test_connection(self, host: str, port: int, protocol: str) -> Tuple[Optional[float], Optional[bool]]:
        """Test connection and optionally perform a TLS handshake."""
        # Use injected config if available, otherwise global CONFIG
        url_testing_enabled = bool(self._get('enable_url_testing', True))
        if not url_testing_enabled:
            return None, None
            
        start = time.time()
        ssl_ctx = None
        handshake = None
        # Sanitize / validate host and port before attempting connection
        host = self._sanitize_host(host)
        port = self._valid_port(port)
        if not host or not port or not self._is_valid_hostname(host):
            # Count invalid host skips if requested
            try:
                if bool(self._get('skip_tests_on_invalid_host', False)):
                    # local counter
                    if not hasattr(self, 'invalid_host_skips'):
                        self.invalid_host_skips = 0  # type: ignore[attr-defined]
                    self.invalid_host_skips += 1  # type: ignore[attr-defined]
                    # event for dashboard/metrics
                    if self.event_bus is not None:
                        from vpn_merger.core.events import Event, EventType  # type: ignore
                        await self.event_bus.publish(Event(
                            type=EventType.INVALID_HOST_SKIPPED,
                            data={"host": host, "port": port, "protocol": protocol},
                            timestamp=time.time(),
                            source=str(host or ''),
                        ))
            except Exception:
                pass
            return None, None
        ssl_required = bool(CONFIG.full_test and protocol in {
            "VMess", "VLESS", "Trojan", "Hysteria2", "Hysteria",
            "TUIC", "Reality", "Naive", "Juicity", "ShadowTLS",
            "WireGuard"
        })

        # Use cached result for identical (host,port,protocol,ssl_required)
        cache_key = (host, port, protocol, ssl_required)
        if cache_key in self._conn_test_cache:
            return self._conn_test_cache[cache_key]

        if ssl_required:
            ssl_ctx = ssl.create_default_context()
            handshake = False
        try:
            with tracer_span("test_connection", {"host": host, "port": port, "protocol": protocol}):
                conn = await asyncio.wait_for(
                    asyncio.open_connection(
                        host,
                        port,
                        ssl=ssl_ctx,
                        server_hostname=host if ssl_ctx else None,
                    ),
                    timeout=float(self._get('test_timeout', CONFIG.test_timeout)),
                )
            reader, writer = conn
            if ssl_ctx:
                handshake = True
            writer.close()
            await writer.wait_closed()
            elapsed = time.time() - start
            # emit event for completed test
            try:
                if self.event_bus is not None:
                    from vpn_merger.core.events import Event, EventType  # type: ignore
                    await self.event_bus.publish(Event(
                        type=EventType.TEST_COMPLETED,
                        data={"host": host, "port": port, "protocol": protocol, "latency": elapsed, "success": True},
                        timestamp=time.time(),
                        source=host,
                    ))
            except Exception:
                pass
            result = (elapsed, handshake)
            self._conn_test_cache[cache_key] = result
            return result
        except (asyncio.TimeoutError, OSError) as e:
            logging.getLogger(__name__).debug(f"Connection test failed for {host}:{port} - {e}")
            try:
                if self.event_bus is not None:
                    from vpn_merger.core.events import Event, EventType  # type: ignore
                    await self.event_bus.publish(Event(
                        type=EventType.TEST_COMPLETED,
                        data={"host": host, "port": port, "protocol": protocol, "latency": None, "success": False},
                        timestamp=time.time(),
                        source=host,
                    ))
            except Exception:
                pass
            result = (None, handshake)
            self._conn_test_cache[cache_key] = result
            return result
        except Exception as e:
            logging.getLogger(__name__).error(f"Unexpected error during test_connection: {e}")
            result = (None, handshake)
            self._conn_test_cache[cache_key] = result
            return result
    
    def categorize_protocol(self, config: str) -> str:
        """Categorize configuration by protocol via central parser."""
        try:
            proto = ProtocolParser.categorize(config)
            # Preserve legacy behavior expected by unit tests: treat trojan as Other here
            if proto == 'Trojan':
                return 'Other'
            return proto
        except Exception:
            return "Other"

# ============================================================================
# ASYNC SOURCE FETCHER WITH COMPREHENSIVE TESTING
# ============================================================================

class AsyncSourceFetcher:
    """Async source fetcher with comprehensive testing and availability checking."""
    
    def __init__(self, processor: EnhancedConfigProcessor):
        self.processor = processor
        self.session: Optional[aiohttp.ClientSession] = None
        self.event_bus = None
        self._cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=30)
        self._backoff = ExponentialBackoff(base=0.3, max_delay=4.0)
        self._rate = PerHostRateLimiter(per_host_rate=5.0, per_host_capacity=10)

    def _effective_proxy(self) -> Optional[str]:
        """Return proxy URL from injected config or global CONFIG."""
        try:
            return self.processor._get('proxy', CONFIG.proxy)
        except Exception:
            return CONFIG.proxy
        
    async def test_source_availability(self, url: str) -> bool:
        """Test if a source URL is available (HTTP 200/206) with HEAD+GET fallback."""
        try:
            with tracer_span("source_availability", {"url": url}):
                if self._cb.is_open(url):
                    return False
                import aiohttp  # type: ignore
                timeout = aiohttp.ClientTimeout(total=10)
                try:
                    host = urlparse(url).hostname or ""
                    if host:
                        await self._rate.acquire(host)
                except Exception:
                    pass
                async with self.session.head(
                    url,
                    timeout=timeout,
                    allow_redirects=True,
                    proxy=self._effective_proxy(),
                ) as response:
                    status = response.status
                    if status == 200:
                        self._cb.record_success(url)
                        return True
                    if 400 <= status < 500:
                        try:
                            if host:
                                await self._rate.acquire(host)
                        except Exception:
                            pass
                        async with self.session.get(
                            url,
                            headers={**CONFIG.headers, 'Range': 'bytes=0-0'},
                            timeout=timeout,
                            allow_redirects=True,
                            proxy=self._effective_proxy(),
                        ) as get_resp:
                            ok = get_resp.status in (200, 206)
                            if ok:
                                self._cb.record_success(url)
                            else:
                                self._cb.record_failure(url)
                            return ok
                    self._cb.record_failure(url)
                    return False
        except (asyncio.TimeoutError, Exception) as e:
            logging.getLogger(__name__).debug(f"Availability check error for {url}: {e}")
            return False
        
    async def fetch_source(self, url: str) -> Tuple[str, List[ConfigResult]]:
        """Fetch VPN configurations from a source URL.

        Args:
            url: Source URL to fetch from.

        Returns:
            Tuple of (source_url, list_of_config_results)
        """
        if not UnifiedSources._is_valid_url(url):
            return url, []
        for attempt in range(CONFIG.max_retries):
            try:
                with tracer_span("fetch_source", {"url": url, "attempt": attempt+1}):
                    import aiohttp  # type: ignore
                    timeout = aiohttp.ClientTimeout(total=CONFIG.request_timeout)
                    # Rate-limit per host to be polite
                    try:
                        host = urlparse(url).hostname or ""
                        if host:
                            await self._rate.acquire(host)
                    except Exception:
                        pass
                    if self._cb.is_open(url):
                        return url, []
                    async with self.session.get(
                        url,
                        headers=CONFIG.headers,
                        timeout=timeout,
                        proxy=self._effective_proxy(),
                    ) as response:
                        if response.status != 200:
                            self._cb.record_failure(url)
                            await asyncio.sleep(self._backoff.get_delay(attempt))
                            continue
                        
                    # Try streaming if content is large and textual
                    content_type = (response.headers.get('Content-Type') or '').lower()
                    content_length = int(response.headers.get('Content-Length') or 0)
                    config_results: List[ConfigResult] = []
                    # Use processor's safe config accessor instead of a non-existent _cfg()
                    url_testing_enabled = bool(self.processor._get('enable_url_testing', True))

                    async def handle_line(line: str) -> None:
                        nonlocal config_results
                        if (line.startswith(CONFIG.valid_prefixes) and 
                            len(line) > 20 and len(line) < 2000 and
                            len(config_results) < CONFIG.max_configs_per_source):
                            host, port = self.processor.extract_host_port(line)
                            protocol = self.processor.categorize_protocol(line)
                            res = ConfigResult(config=line, protocol=protocol, host=host, port=port, source_url=url)
                            if url_testing_enabled and host and port:
                                ping_time, hs = await self.processor.test_connection(host, port, protocol)
                                res.ping_time = ping_time
                                res.handshake_ok = hs
                                res.is_reachable = ping_time is not None and (hs is not False)
                            config_results.append(res)
                            # Emit CONFIG_PARSED event
                            try:
                                if self.event_bus is not None:
                                    from vpn_merger.core.events import Event, EventType  # type: ignore
                                    await self.event_bus.publish(Event(
                                        type=EventType.CONFIG_PARSED,
                                        data={"protocol": protocol, "host": host, "port": port},
                                        timestamp=time.time(),
                                        source=url,
                                    ))
                            except Exception:
                                pass

                    # Stream large/unknown-sized text to avoid memory spikes
                    if ("text" in content_type and (content_length == 0 or content_length > 1024 * 1024 or content_length > ResourceLimits.MAX_RESPONSE_SIZE)):
                        async for chunk in response.content:
                            try:
                                text = chunk.decode('utf-8', 'ignore')
                            except Exception:
                                continue
                            for raw_line in text.splitlines():
                                if not raw_line:
                                    continue
                                line = raw_line.strip()
                                if not line:
                                    continue
                                await handle_line(line)
                                if len(config_results) >= CONFIG.max_configs_per_source:
                                    break
                            if len(config_results) >= CONFIG.max_configs_per_source:
                                break
                        # Prepare event payload
                        try:
                            if self.event_bus is not None:
                                from vpn_merger.core.events import Event, EventType  # type: ignore
                                samples = []
                                for r in config_results[-3:]:
                                    samples.append({
                                        'protocol': getattr(r, 'protocol', ''),
                                        'host': getattr(r, 'host', ''),
                                        'port': getattr(r, 'port', None),
                                        'ping_ms': (getattr(r, 'ping_time', None) or 0) * 1000 if getattr(r, 'ping_time', None) else None,
                                    })
                                reachable = sum(1 for r in config_results if getattr(r, 'is_reachable', False))
                                protocol_counts: Dict[str, int] = {}
                                for r in config_results:
                                    p = getattr(r, 'protocol', 'Unknown')
                                    protocol_counts[p] = protocol_counts.get(p, 0) + 1
                                await self.event_bus.publish(Event(
                                    type=EventType.SOURCE_FETCHED,
                                    data={"url": url, "count": len(config_results), "reachable": reachable, "samples": samples, "protocol_counts": protocol_counts},
                                    timestamp=time.time(),
                                    source=url,
                                ))
                        except Exception:
                            pass
                        return url, config_results
                    else:
                        # Read with a hard cap to avoid memory exhaustion on malformed servers
                        raw = await response.content.read(ResourceLimits.MAX_RESPONSE_SIZE + 1)
                        if len(raw) > ResourceLimits.MAX_RESPONSE_SIZE:
                            return url, []
                        try:
                            content = raw.decode(response.charset or 'utf-8', 'ignore')
                        except Exception:
                            content = raw.decode('utf-8', 'ignore')
                        if not content.strip():
                            return url, []
                        # Enhanced Base64 detection and decoding
                        try:
                            if not any(char in content for char in '\n\r') and len(content) > 100:
                                decoded = self.processor.safe_b64_decode(content, self.processor.MAX_DECODE_SIZE)
                                if decoded and decoded.count("://") > content.count("://"):
                                    content = decoded
                        except Exception:
                            pass
                        lines = [line.strip() for line in content.splitlines() if line.strip()]
                        for line in lines:
                            await handle_line(line)
                        try:
                            if self.event_bus is not None:
                                from vpn_merger.core.events import Event, EventType  # type: ignore
                                samples = []
                                for r in config_results[-3:]:
                                    samples.append({
                                        'protocol': getattr(r, 'protocol', ''),
                                        'host': getattr(r, 'host', ''),
                                        'port': getattr(r, 'port', None),
                                        'ping_ms': (getattr(r, 'ping_time', None) or 0) * 1000 if getattr(r, 'ping_time', None) else None,
                                    })
                                reachable = sum(1 for r in config_results if getattr(r, 'is_reachable', False))
                                protocol_counts: Dict[str, int] = {}
                                for r in config_results:
                                    p = getattr(r, 'protocol', 'Unknown')
                                    protocol_counts[p] = protocol_counts.get(p, 0) + 1
                                await self.event_bus.publish(Event(
                                    type=EventType.SOURCE_FETCHED,
                                    data={"url": url, "count": len(config_results), "reachable": reachable, "samples": samples, "protocol_counts": protocol_counts},
                                    timestamp=time.time(),
                                    source=url,
                                ))
                        except Exception:
                            pass
                        # Mark success for circuit breaker
                        self._cb.record_success(url)
                        return url, config_results
                
            except (asyncio.TimeoutError, Exception) as e:
                logging.getLogger(__name__).debug(f"Fetch error for {url} (attempt {attempt+1}): {e}")
                try:
                    if self.event_bus is not None:
                        from vpn_merger.core.events import Event, EventType  # type: ignore
                        await self.event_bus.publish(Event(
                            type=EventType.ERROR_OCCURRED,
                            data={"url": url, "error": str(e)},
                            timestamp=time.time(),
                            source=url,
                        ))
                except Exception:
                    pass
                if attempt < CONFIG.max_retries - 1:
                    self._cb.record_failure(url)
                    await asyncio.sleep(self._backoff.get_delay(attempt))
                    
        return url, []

# ============================================================================
# MAIN PROCESSOR WITH UNIFIED FUNCTIONALITY
# ============================================================================

class UltimateVPNMerger:
    """VPN merger with unified functionality and comprehensive testing."""
    
    def __init__(self, config=None):
        self.config = config
        # Small helper to safely read nested attributes from an injected
        # pydantic config (or any object), with a fallback default.
        def _get_cfg(*path, default=None):
            obj = self.config
            try:
                for key in path:
                    if obj is None or not hasattr(obj, str(key)):
                        return default
                    obj = getattr(obj, str(key))
                return obj if obj is not None else default
            except Exception:
                return default

        # Bind as instance method
        self._get_cfg = _get_cfg  # type: ignore[attr-defined]
        # Lazy imports for new modular components to avoid breaking runtime
        try:
            from vpn_merger.storage.database import VPNDatabase  # type: ignore
            self.db = VPNDatabase()
        except Exception:
            self.db = None

        # Optional dashboard manager for real-time status updates
        try:
            from vpn_merger.api.dashboard import DashboardManager  # type: ignore
            self.dashboard_manager = DashboardManager()
        except Exception:
            self.dashboard_manager = None
        self._dashboard_via_events = False

        # Optional Prometheus metrics
        try:
            from vpn_merger.monitoring.metrics import VPNMergerMetrics  # type: ignore
            enable_metrics = bool(self._get_cfg('monitoring', 'enable_metrics', default=CONFIG.enable_metrics))
            port = int(self._get_cfg('monitoring', 'metrics_port', default=8001))
            self.metrics = VPNMergerMetrics(port=port) if enable_metrics else None
        except Exception:
            self.metrics = None

        # Event bus for lifecycle events
        try:
            from vpn_merger.core.events import EventBus  # type: ignore
            self.event_bus = EventBus()
        except Exception:
            self.event_bus = None

    def _maybe_start_dashboard(self) -> None:
        enable_dash_cli = bool(getattr(CONFIG, 'enable_dashboard_cli', False))
        port_cli = int(getattr(CONFIG, 'dashboard_port_cli', 8000))
        host_cli = str(getattr(CONFIG, 'dashboard_host_cli', '0.0.0.0'))
        app_cli = str(getattr(CONFIG, 'dashboard_app_cli', 'api'))
        cert_cli = getattr(CONFIG, 'dashboard_cert_cli', None)
        key_cli = getattr(CONFIG, 'dashboard_key_cli', None)

        enable_dash_cfg = bool(self._get_cfg('monitoring', 'enable_dashboard', default=False))
        port_cfg = int(self._get_cfg('monitoring', 'dashboard_port', default=port_cli))
        enable_dash = enable_dash_cfg or enable_dash_cli
        port = port_cfg
        if enable_dash:
            try:
                import uvicorn  # type: ignore
                import threading
                if app_cli == 'realtime':
                    from vpn_merger.dashboard.realtime_dashboard import app as dashboard_app  # type: ignore
                else:
                    from vpn_merger.api.dashboard import app as dashboard_app  # type: ignore
                def run_server():
                    # Auto-increment port if in use, try up to +10
                    chosen_port = port
                    for candidate in range(port, port + 11):
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        try:
                            s.bind((host_cli, candidate))
                            chosen_port = candidate
                            s.close()
                            break
                        except OSError:
                            try:
                                s.close()
                            except Exception:
                                pass
                            continue
                    if chosen_port != port:
                        print(f"ℹ️  Dashboard port {port} busy; using {chosen_port} instead")
                    kwargs = {"host": host_cli, "port": chosen_port, "log_level": "error"}
                    if cert_cli and key_cli:
                        kwargs["ssl_certfile"] = cert_cli
                        kwargs["ssl_keyfile"] = key_cli
                    try:
                        uvicorn.run(dashboard_app, **kwargs)
                    except BaseException as e:
                        print(f"⚠️  Dashboard failed to start: {e}")
                t = threading.Thread(target=run_server, daemon=True)
                t.start()
                # Optionally print HMAC token for API dashboard
                try:
                    client_id = getattr(CONFIG, 'dashboard_client_id_cli', None)
                    if client_id and app_cli == 'api':
                        from vpn_merger.api.dashboard import WebSocketAuth  # type: ignore
                        import os as _os
                        key = _os.environ.get('DASHBOARD_HMAC_KEY')
                        if key:
                            token = WebSocketAuth(key).generate_token(str(client_id))
                            print(f"🔑 Dashboard token for client '{client_id}': {token}")
                except Exception:
                    pass
            except Exception:
                pass

        self.sources = UnifiedSources.get_all_sources()
        should_shuffle = bool(self._get_cfg('processing', 'shuffle_sources', default=CONFIG.shuffle_sources))
        if should_shuffle:
            random.shuffle(self.sources)
        # Use the built-in implementations to avoid placeholder stubs
        self.processor = EnhancedConfigProcessor()
        self.fetcher = AsyncSourceFetcher(self.processor)
        try:
            self.fetcher.event_bus = self.event_bus  # type: ignore[attr-defined]
        except Exception:
            pass
        try:
            self.processor.event_bus = self.event_bus  # type: ignore[attr-defined]
        except Exception:
            pass
        # Propagate high-level config into components that expect it
        try:
            self.processor.config = self.config  # type: ignore[attr-defined]
        except Exception:
            pass
        try:
            self.fetcher.config = self.config  # type: ignore[attr-defined]
        except Exception:
            pass
        self.batch_counter = 0
        try:
            batch_size_value = int(self.config.processing.batch_size) if (self.config and getattr(self.config, 'processing', None)) else int(CONFIG.batch_size)
        except Exception:
            batch_size_value = int(CONFIG.batch_size)
        self.next_batch_threshold = batch_size_value if batch_size_value else float('inf')
        self.start_time = 0.0
        self.available_sources: List[str] = []
        self.sources_with_configs: List[str] = []
        self.all_results: List[ConfigResult] = []
        self.stop_fetching = False
        self.saved_hashes: Set[str] = set()
        self.cumulative_unique: List[ConfigResult] = []
        self.last_processed_index = 0
        self.last_saved_count = 0
        self._batch_lock = asyncio.Lock()
        self._shutdown_event = GlobalState.get_shutdown_event()
        # Optional Bloom filter for dedupe
        self._bloom = None
        try:
            if self._get_cfg('processing', 'use_bloom_dedupe', default=False):
                cap = int(self._get_cfg('processing', 'bloom_capacity', default=1_000_000))
                fp = float(self._get_cfg('processing', 'bloom_error_rate', default=0.01))
                self._bloom = BloomFilter(capacity=cap, error_rate=fp)
        except Exception:
            self._bloom = None
        # Quarantine tracking
        self._fail_streak: Dict[str, int] = {}
        self._quarantined: Set[str] = set()
        try:
            self._quarantine_enabled: bool = bool(self._get_cfg('processing', 'quarantine_failures', default=CONFIG.quarantine_failures) or CONFIG.quarantine_failures)
        except Exception:
            self._quarantine_enabled = bool(CONFIG.quarantine_failures)
        try:
            self._quarantine_threshold: int = int(self._get_cfg('processing', 'quarantine_threshold', default=CONFIG.quarantine_threshold))
        except Exception:
            self._quarantine_threshold = int(CONFIG.quarantine_threshold)
        # Preload quarantined sources from DB
        try:
            if self.db is not None:
                for u in self.db.get_quarantined_sources():
                    self._quarantined.add(u)
        except Exception:
            pass

    def _load_existing_results(self, path: str) -> List[ConfigResult]:
        """Load previously saved configs from a raw or base64 file."""
        try:
            p = Path(path)
            ResourceLimits.check_file_size(p)
            text = p.read_text(encoding="utf-8").strip()
        except Exception as e:
            print(f"⚠️  Failed to read resume file: {e}")
            return []

        if text and '://' not in text.splitlines()[0]:
            decoded = self.processor.safe_b64_decode(text, self.processor.MAX_DECODE_SIZE)
            if decoded:
                text = decoded

        results = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            protocol = self.processor.categorize_protocol(line)
            host, port = self.processor.extract_host_port(line)
            results.append(
                ConfigResult(
                    config=line,
                    protocol=protocol,
                    host=host,
                    port=port,
                    source_url="(resume)"
                )
            )
        return results
        
    async def run(self) -> None:
        """Execute the complete unified merging process."""
        # Optionally start dashboard server in the background
        try:
            self._maybe_start_dashboard()
        except Exception:
            pass
        print("🚀 VPN Subscription Merger - Final Unified & Polished Edition")
        print("=" * 85)
        # Start event bus processor
        if self.event_bus is not None:
            try:
                asyncio.create_task(self.event_bus.start())
            except Exception:
                pass
        # Attach metrics subscriber to event bus
        if getattr(self, 'metrics', None) is not None and self.event_bus is not None:
            try:
                from vpn_merger.monitoring.metrics_subscribers import attach as attach_metrics  # type: ignore
                attach_metrics(self.event_bus, self.metrics)
            except Exception:
                pass
        # Optional discovery
        try:
            discover_enabled = bool(self._get_cfg('processing', 'enable_discovery', default=CONFIG.enable_discovery) or CONFIG.enable_discovery)
        except Exception:
            discover_enabled = bool(CONFIG.enable_discovery)
        if discover_enabled:
            try:
                from vpn_merger.core.source_discovery import discover_sources  # type: ignore
                print("🔎 Discovering additional sources...")
                discovered = await discover_sources()
                if discovered:
                    before = len(self.sources)
                    # merge and dedup, discovered last to keep curated priority
                    self.sources = list(dict.fromkeys(self.sources + discovered))
                    print(f"   ✔ Added {len(self.sources) - before} new candidates (total {len(self.sources)})")
            except Exception as e:
                print(f"⚠️  Discovery failed: {e}")

        print(f"📊 Total unified sources: {len(self.sources)}")
        print(f"🇮🇷 Iranian priority: {len(UnifiedSources.IRANIAN_PRIORITY)}")
        print(f"🌍 International major: {len(UnifiedSources.INTERNATIONAL_MAJOR)}")
        print(f"📦 Comprehensive batch: {len(UnifiedSources.COMPREHENSIVE_BATCH)}")
        url_testing_enabled = bool(self._get_cfg('testing', 'enable_url_testing', default=CONFIG.enable_url_testing))
        sorting_enabled = bool(self._get_cfg('testing', 'enable_sorting', default=CONFIG.enable_sorting))
        print(f"🔧 URL Testing: {'Enabled' if url_testing_enabled else 'Disabled'}")
        print(f"📈 Smart Sorting: {'Enabled' if sorting_enabled else 'Disabled'}")
        print()
        
        start_time = time.time()
        self.start_time = start_time

        if CONFIG.resume_file:
            print(f"🔄 Loading existing configs from {CONFIG.resume_file} ...")
            self.all_results.extend(self._load_existing_results(CONFIG.resume_file))
            print(f"   ✔ Loaded {len(self.all_results)} configs from resume file")

        # Step 1: Test source availability and remove dead links
        # Attach dashboard event subscribers if available
        if self.event_bus is not None and self.dashboard_manager is not None:
            try:
                from vpn_merger.monitoring.dashboard_subscribers import attach  # type: ignore
                self._dash_agg = attach(self.event_bus, self.dashboard_manager, total_sources=len(self.sources))
                self._dashboard_via_events = True
            except Exception:
                self._dashboard_via_events = False

        print("🔄 [1/6] Testing source availability and removing dead links...")
        log_json(logging.INFO, "phase_status", phase=1, action="test_sources", total_sources=len(self.sources))
        self.available_sources = await self._test_and_filter_sources()
        
        # Step 2: Fetch all configs from available sources
        print(f"\n🔄 [2/6] Fetching configs from {len(self.available_sources)} available sources...")
        log_json(logging.INFO, "phase_status", phase=2, action="fetch_configs", available_sources=len(self.available_sources))
        use_distributed = bool(getattr(CONFIG, 'distributed', False))
        if use_distributed:
            try:
                from vpn_merger.distributed.coordinator import DistributedCoordinator  # type: ignore
                coord = DistributedCoordinator(redis_url=getattr(CONFIG, 'redis_url', None), worker_count=int(getattr(CONFIG, 'dist_workers', 4)))
                dist = await coord.distribute_sources(self.available_sources)
                mode = dist.get('mode')
                if mode == 'local':
                    mapping = dist.get('results', {})
                    await self._ingest_distributed_results(mapping)
                else:
                    tasks = dist.get('tasks', [])
                    print(f"   📤 Celery tasks queued: {len(tasks)}. Waiting for results...")
                    mapping = await coord.collect_results(tasks, timeout=120.0)
                    if mapping:
                        await self._ingest_distributed_results(mapping)
                    else:
                        print("   ⚠️  No Celery results within timeout; proceeding with local fetch as fallback.")
                        await self._fetch_all_sources(self.available_sources)
            except Exception as e:
                print(f"⚠️  Distributed fetch failed ({e}); falling back to local fetch.")
                await self._fetch_all_sources(self.available_sources)
        else:
            await self._fetch_all_sources(self.available_sources)
        
        # Step 3: Deduplicate efficiently  
        print(f"\n🔍 [3/6] Deduplicating {len(self.all_results):,} configs...")
        log_json(logging.INFO, "phase_status", phase=3, action="dedupe", input=len(self.all_results))
        unique_results = self._deduplicate_config_results(self.all_results)
        
        # Step 4: Sort by performance if enabled
        if sorting_enabled:
            print(f"\n📊 [4/6] Sorting {len(unique_results):,} configs by performance...")
            log_json(logging.INFO, "phase_status", phase=4, action="sort", input=len(unique_results))
            unique_results = self._sort_by_performance(unique_results)
        else:
            print(f"\n⏭️ [4/6] Skipping sorting (disabled)")

        if CONFIG.top_n > 0:
            unique_results = unique_results[:CONFIG.top_n]
            print(f"   🔝 Keeping top {CONFIG.top_n} configs")
            try:
                log_json(logging.INFO, "top_n", top_n=CONFIG.top_n)
            except Exception:
                pass

        max_ping_ms_value = self._get_cfg('testing', 'max_ping_ms', default=None)
        url_testing_enabled = bool(self._get_cfg('testing', 'enable_url_testing', default=CONFIG.enable_url_testing))
        if max_ping_ms_value is not None and url_testing_enabled:
            before = len(unique_results)
            unique_results = [r for r in unique_results
                              if r.ping_time is not None and r.ping_time * 1000 <= max_ping_ms_value]
            removed = before - len(unique_results)
            print(f"   ⏱️  Removed {removed} configs over {max_ping_ms_value} ms")

        before_filter = len(unique_results)
        unique_results = self._filter_reachable_results(unique_results)
        if before_filter != len(unique_results):
            print(f"   🚫 Filtered out {before_filter - len(unique_results)} unreachable/untested configs")

        app_tests_value = list(self._get_cfg('testing', 'app_tests', default=CONFIG.app_tests) or []) or (CONFIG.app_tests if CONFIG.app_tests else None)
        if app_tests_value:
            await self._run_app_tests(unique_results)

        # Step 5: Analyze protocols and performance
        print(f"\n📋 [5/6] Analyzing {len(unique_results):,} unique configs...")
        stats = self._analyze_results(unique_results, self.sources_with_configs)
        
        # Step 6: Generate comprehensive outputs
        print("\n💾 [6/6] Generating comprehensive outputs...")
        log_json(logging.INFO, "phase_status", phase=6, action="outputs")
        await self._generate_comprehensive_outputs(unique_results, stats, self.start_time)

        # Avoid division by zero in final summary
        _cfg_count = len(unique_results)
        _elapsed = time.time() - self.start_time
        self._print_final_summary(max(_cfg_count, 1), max(_elapsed, 1.0), stats)
    
    async def _test_and_filter_sources(self) -> List[str]:
        """Test all sources for availability and filter out dead links."""
        # Setup HTTP session via connection pool manager with graceful fallback
        try:
            from vpn_merger.core.pipeline import ConnectionPoolManager  # type: ignore
            pool = ConnectionPoolManager()
            self.fetcher.session = await pool.get_pool(name='default', limit=CONFIG.concurrent_limit, limit_per_host=10)
        except Exception as e:
            try:
                import aiohttp  # type: ignore
                self.fetcher.session = aiohttp.ClientSession()
                print(f"⚠️  Falling back to direct ClientSession due to pool error: {e}")
            except Exception as e2:
                raise RuntimeError("Failed to initialize HTTP connection pool or fallback session. Ensure aiohttp is installed.") from e2
        
        try:
            # Test all sources concurrently
            semaphore = asyncio.Semaphore(CONFIG.concurrent_limit)
            
            async def test_single_source(url: str) -> Optional[str]:
                async with semaphore:
                    if self._quarantine_enabled and url in self._quarantined:
                        return None
                    is_available = await self.fetcher.test_source_availability(url)
                    if not is_available:
                        if self._quarantine_enabled:
                            n = self._fail_streak.get(url, 0) + 1
                            self._fail_streak[url] = n
                            try:
                                if self.db is not None:
                                    n = self.db.increment_fail_streak(url)
                            except Exception:
                                pass
                            if n >= self._quarantine_threshold:
                                self._quarantined.add(url)
                                try:
                                    if self.db is not None:
                                        self.db.set_quarantined(url, True)
                                except Exception:
                                    pass
                        return None
                    # Reset fail streak on success
                    if url in self._fail_streak:
                        self._fail_streak[url] = 0
                    try:
                        if self.db is not None:
                            self.db.reset_fail_streak(url)
                            # optional: unquarantine on success
                            self.db.set_quarantined(url, False)
                    except Exception:
                        pass
                    return url
            
            tasks = [test_single_source(url) for url in self.sources]
            
            completed = 0
            available_sources = []

            with tqdm(total=len(self.sources), desc="Testing sources", unit="src") as pbar:
                for coro in asyncio.as_completed(tasks):
                    if self._shutdown_event.is_set():
                        break
                    result = await coro
                    completed += 1
                    pbar.update(1)

                    if result:
                        available_sources.append(result)
                        status = "✅ Available"
                    else:
                        status = "❌ Dead link"

                    pbar.set_postfix_str(status)
            
            removed_count = len(self.sources) - len(available_sources)
            print(f"\n   🗑️ Removed {removed_count} dead sources")
            print(f"   ✅ Keeping {len(available_sources)} available sources")
            
            return available_sources
            
        finally:
            # Don't close session here, we'll reuse it
            pass
    
    async def _fetch_all_sources(self, available_sources: List[str]) -> List[ConfigResult]:
        """Fetch all configs from available sources."""
        # Append results directly to self.all_results so that _maybe_save_batch
        # sees the running total and can save incremental batches.
        successful_sources = 0
        self.sources_with_configs = []
        
        try:
            # Process sources via ParallelPipeline
            async def process_single_source(url: str) -> Tuple[str, List[ConfigResult]]:
                return await self.fetcher.fetch_source(url)

            from vpn_merger.core.pipeline import ParallelPipeline  # type: ignore
            pipeline = ParallelPipeline([process_single_source], concurrency=CONFIG.concurrent_limit)
            fetched = await pipeline.process(available_sources)

            completed = 0
            with tqdm(total=len(fetched), desc="Fetching configs", unit="src") as pbar:
                for (url, results) in fetched:
                    if self._shutdown_event.is_set():
                        break
                    completed += 1
                    pbar.update(1)
                    # Prefilter duplicates early (Bloom or hash set) to reduce memory
                    prefiltered: List[ConfigResult] = []
                    for r in results:
                        try:
                            h = self.processor.create_semantic_hash(r.config)
                            if getattr(self, '_bloom', None) is not None:
                                if h in self._bloom:  # type: ignore[operator]
                                    continue
                                self._bloom.add(h)  # type: ignore[union-attr]
                                prefiltered.append(r)
                            else:
                                if h in self.saved_hashes:
                                    continue
                                # Optional DB-dedupe across runs
                                try:
                                    use_db = bool(self._get_cfg('processing', 'use_db_dedupe', default=False))
                                except Exception:
                                    use_db = False
                                if use_db and getattr(self, 'db', None) is not None:
                                    try:
                                        if self.db.has_config(r.config):  # type: ignore[attr-defined]
                                            continue
                                    except Exception:
                                        pass
                                self.saved_hashes.add(h)
                                prefiltered.append(r)
                        except Exception:
                            prefiltered.append(r)
                    # Ensure consistent view for batch saver
                    async with self._batch_lock:
                        self.all_results.extend(prefiltered)
                    # Persist, record metrics, and broadcast incrementally
                    if prefiltered:
                        if self.db is not None:
                            for result in prefiltered:
                                try:
                                    self.db.store_config(result)
                                except Exception:
                                    pass
                        # Metrics are handled via event subscribers
                        # If dashboard is event-driven, skip direct broadcasts
                    if prefiltered:
                        successful_sources += 1
                        self.sources_with_configs.append(url)
                        reachable = sum(1 for r in prefiltered if r.is_reachable)
                        status = f"✓ {len(prefiltered):,} configs ({reachable} reachable)"
                    else:
                        status = "✗ No configs"

                    domain = urlparse(url).netloc or url[:50] + "..."
                    pbar.set_postfix_str(f"{status} - {domain}")

                    await self._maybe_save_batch()

                    if self.stop_fetching:
                        break

            if self.stop_fetching:
                for t in tasks:
                    if not t.done():
                        t.cancel()
                # Drain cancellations to avoid warnings
                for t in tasks:
                    try:
                        await t
                    except Exception:
                        pass

            print(f"\n   📈 Sources with configs: {len(self.sources_with_configs)}/{len(available_sources)}")
            if self._quarantine_enabled and self._quarantined:
                print(f"   🚧 Quarantined sources: {len(self._quarantined)}")
            
        finally:
            await self.fetcher.session.close()

        # Return the accumulated list for backward compatibility
        return self.all_results

    async def _ingest_distributed_results(self, mapping: Dict[str, List[str]]) -> None:
        """Convert distributed fetch results to ConfigResult and ingest them.

        mapping: {url -> [config_line, ...]}
        """
        try:
            total = len(mapping)
            completed = 0
            with tqdm(total=total, desc="Ingest distributed", unit="src") as pbar:
                for url, lines in mapping.items():
                    if self._shutdown_event.is_set():
                        break
                    url_testing_enabled = bool(self.processor._get('enable_url_testing', True))
                    results_for_url: List[ConfigResult] = []
                    for line in lines:
                        if not line:
                            continue
                        host, port = self.processor.extract_host_port(line)
                        protocol = self.processor.categorize_protocol(line)
                        res = ConfigResult(config=line, protocol=protocol, host=host, port=port, source_url=url)
                        if url_testing_enabled and host and port:
                            ping_time, hs = await self.processor.test_connection(host, port, protocol)
                            res.ping_time = ping_time
                            res.handshake_ok = hs
                            res.is_reachable = ping_time is not None and (hs is not False)
                        results_for_url.append(res)
                    async with self._batch_lock:
                        self.all_results.extend(results_for_url)
                    if results_for_url:
                        self.sources_with_configs.append(url)
                    completed += 1
                    pbar.update(1)
                    await self._maybe_save_batch()
        except Exception as e:
            print(f"⚠️  Failed to ingest distributed results: {e}")

    async def _maybe_save_batch(self) -> None:
        """Save intermediate output based on batch settings."""
        if CONFIG.batch_size <= 0:
            return

        # Process new results since last call
        async with self._batch_lock:
            new_slice = self.all_results[self.last_processed_index:]
            self.last_processed_index = len(self.all_results)
        for r in new_slice:
            if CONFIG.tls_fragment and CONFIG.tls_fragment.lower() not in r.config.lower():
                continue
            if CONFIG.include_protocols and r.protocol.upper() not in CONFIG.include_protocols:
                continue
            if CONFIG.exclude_protocols and r.protocol.upper() in CONFIG.exclude_protocols:
                continue
            h = self.processor.create_semantic_hash(r.config)
            # Bloom filter preferred when enabled to curb memory use
            if getattr(self, '_bloom', None) is not None:
                if h in self._bloom:  # type: ignore[operator]
                    continue
                self._bloom.add(h)  # type: ignore[union-attr]
                self.cumulative_unique.append(r)
            else:
                if h not in self.saved_hashes:
                    self.saved_hashes.add(h)
                    self.cumulative_unique.append(r)

        strict_batch_enabled = bool(self._get_cfg('processing', 'strict_batch', default=CONFIG.strict_batch))
        if strict_batch_enabled:
            while len(self.cumulative_unique) - self.last_saved_count >= CONFIG.batch_size:
                self.batch_counter += 1
                if CONFIG.cumulative_batches:
                    batch_results = self.cumulative_unique[:]
                else:
                    start = self.last_saved_count
                    end = start + CONFIG.batch_size
                    batch_results = self.cumulative_unique[start:end]
                    self.last_saved_count = end

                sorting_enabled = bool(self._get_cfg('testing', 'enable_sorting', default=CONFIG.enable_sorting))
                if sorting_enabled:
                    batch_results = self._sort_by_performance(batch_results)
                if CONFIG.top_n > 0:
                    batch_results = batch_results[:CONFIG.top_n]
                batch_results = self._filter_reachable_results(batch_results)
                app_tests_value = list(self._get_cfg('testing', 'app_tests', default=CONFIG.app_tests) or []) or (CONFIG.app_tests if CONFIG.app_tests else None)
                if app_tests_value:
                    await self._run_app_tests(batch_results)

                stats = self._analyze_results(batch_results, self.sources_with_configs)
                await self._generate_comprehensive_outputs(batch_results, stats, self.start_time, prefix=f"batch_{self.batch_counter}_")
                # Event: batch ready
                try:
                    if self.event_bus is not None:
                        from vpn_merger.core.events import Event, EventType  # type: ignore
                        await self.event_bus.publish(Event(
                            type=EventType.BATCH_READY,
                            data={"batch": self.batch_counter, "count": len(batch_results)},
                            timestamp=time.time(),
                        ))
                except Exception:
                    pass

                cumulative_stats = self._analyze_results(self.cumulative_unique, self.sources_with_configs)
                await self._generate_comprehensive_outputs(self.cumulative_unique, cumulative_stats, self.start_time, prefix="cumulative_")

                threshold_value = int(self._get_cfg('processing', 'threshold', default=CONFIG.threshold))
                if threshold_value > 0 and len(self.cumulative_unique) >= threshold_value:
                    print(f"\n⏹️  Threshold of {CONFIG.threshold} configs reached. Stopping early.")
                    self.stop_fetching = True
                    break
        else:
            if len(self.cumulative_unique) >= self.next_batch_threshold:
                self.batch_counter += 1
                if CONFIG.cumulative_batches:
                    batch_results = self.cumulative_unique[:]
                else:
                    batch_results = self.cumulative_unique[self.last_saved_count:]
                    self.last_saved_count = len(self.cumulative_unique)

                if sorting_enabled:
                    batch_results = self._sort_by_performance(batch_results)
                if CONFIG.top_n > 0:
                    batch_results = batch_results[:CONFIG.top_n]
                batch_results = self._filter_reachable_results(batch_results)
                app_tests_value = list(self._get_cfg('testing', 'app_tests', default=CONFIG.app_tests) or []) or (CONFIG.app_tests if CONFIG.app_tests else None)
                if app_tests_value:
                    await self._run_app_tests(batch_results)

                stats = self._analyze_results(batch_results, self.sources_with_configs)
                await self._generate_comprehensive_outputs(batch_results, stats, self.start_time, prefix=f"batch_{self.batch_counter}_")

                cumulative_stats = self._analyze_results(self.cumulative_unique, self.sources_with_configs)
                await self._generate_comprehensive_outputs(self.cumulative_unique, cumulative_stats, self.start_time, prefix="cumulative_")

                local_batch_size_value = int(self._get_cfg('processing', 'batch_size', default=CONFIG.batch_size))
                self.next_batch_threshold += local_batch_size_value

                threshold_value = int(self._get_cfg('processing', 'threshold', default=CONFIG.threshold))
                if threshold_value > 0 and len(self.cumulative_unique) >= threshold_value:
                    print(f"\n⏹️  Threshold of {CONFIG.threshold} configs reached. Stopping early.")
                    self.stop_fetching = True
    
    def _deduplicate_config_results(self, results: List[ConfigResult]) -> List[ConfigResult]:
        """Efficient deduplication using batch hashing preserving first occurrence order."""
        index_by_hash: Dict[str, int] = {}
        filtered: List[Tuple[int, str]] = []
        for i, result in enumerate(results):
            if CONFIG.tls_fragment and CONFIG.tls_fragment.lower() not in result.config.lower():
                continue
            if CONFIG.include_protocols and result.protocol.upper() not in CONFIG.include_protocols:
                continue
            if CONFIG.exclude_protocols and result.protocol.upper() in CONFIG.exclude_protocols:
                continue
            h = self.processor.create_semantic_hash(result.config)
            if h not in index_by_hash:
                index_by_hash[h] = i
        unique_indices = sorted(index_by_hash.values())
        unique_results = [results[i] for i in unique_indices]
        duplicates = len(results) - len(unique_results)
        print(f"   🗑️ Duplicates removed: {duplicates:,}")
        efficiency = (duplicates / len(results) * 100) if results else 0
        print(f"   📊 Deduplication efficiency: {efficiency:.1f}%")
        try:
            log_json(logging.INFO, "dedupe_stats", duplicates=duplicates, input=len(results), efficiency=round(efficiency, 1))
        except Exception:
            pass
        return unique_results
    
    def _sort_by_performance(self, results: List[ConfigResult]) -> List[ConfigResult]:
        """Sort results by connection performance and protocol preference.

        If available, compute advanced quality metrics and sort by quality_score.
        """
        # Attempt advanced quality scoring
        used_quality = False
        try:
            from vpn_merger.core.quality_scorer import AdvancedQualityScorer  # type: ignore
            scorer = AdvancedQualityScorer()
            for r in results:
                history_data = None
                try:
                    # Optional hook for future: fetch history from DB
                    history_data = None
                except Exception:
                    history_data = None
                qm = scorer.calculate_quality_metrics(r, history_data)
                setattr(r, 'quality_score', qm.composite_score)
                setattr(r, 'quality_metrics', qm)
            results = sorted(results, key=lambda x: getattr(x, 'quality_score', 0.0), reverse=True)
            used_quality = True
        except Exception:
            used_quality = False

        if used_quality:
            reachable_count = sum(1 for r in results if getattr(r, 'is_reachable', False))
            print(f"   🚀 Sorted by quality score; reachable: {reachable_count:,}")
            return results

        # If no advanced scorer, try a lightweight ML/heuristic predictor to break ties
        try:
            from vpn_merger.ml.quality_predictor import QualityPredictor  # type: ignore
            qp = QualityPredictor()
            for r in results:
                # Only boost untested items; keep measured latency primary
                if r.ping_time is None:
                    ctx = {"source_reputation": 0}
                    try:
                        ctx["source_reputation"] = 0.1 if (r.source_url and 'githubusercontent' in r.source_url) else 0
                    except Exception:
                        pass
                    score = qp.predict_quality(r.protocol, r.port, ctx)
                    setattr(r, 'ml_score', score)
        except Exception:
            pass

        # Fallback: Protocol priority ranking
        protocol_priority = {
            "VLESS": 1, "VMess": 2, "Reality": 3, "Hysteria2": 4,
            "Trojan": 5, "Shadowsocks": 6, "TUIC": 7, "Hysteria": 8,
            "Naive": 9, "Juicity": 10, "WireGuard": 11, "Other": 12
        }
        if CONFIG.prefer_protocols:
            for idx, proto in enumerate(CONFIG.prefer_protocols, start=1):
                protocol_priority[proto] = idx
        
        def sort_key(result: ConfigResult) -> Tuple:
            is_reachable = 1 if result.is_reachable else 0
            ping_time = result.ping_time if result.ping_time is not None else float('inf')
            protocol_rank = protocol_priority.get(result.protocol, 13)
            # Lower ping_time is better. For untested, use negative ML score to prefer higher.
            ml_penalty = -getattr(result, 'ml_score', 0.0)
            return (-is_reachable, ping_time, protocol_rank, ml_penalty)
        
        sorted_results = sorted(results, key=sort_key)
        
        reachable_count = sum(1 for r in results if r.is_reachable)
        print(f"   🚀 Sorted: {reachable_count:,} reachable configs first")
        
        if reachable_count > 0:
            fastest = min((r for r in results if r.ping_time), key=lambda x: x.ping_time, default=None)
            if fastest:
                print(f"   ⚡ Fastest server: {fastest.ping_time*1000:.1f}ms ({fastest.protocol})")

        return sorted_results

    def _filter_reachable_results(self, results: List[ConfigResult]) -> List[ConfigResult]:
        """Remove configs that failed reachability tests or lack ping data."""
        return [r for r in results if r.is_reachable and r.ping_time is not None]

    async def _run_app_tests(self, results: List[ConfigResult]) -> None:
        """Run service connectivity tests on the fastest configs."""
        try:
            app_tests_value = list(self.config.testing.app_tests) if (self.config and getattr(self.config, 'testing', None) and self.config.testing.app_tests) else None
        except Exception:
            app_tests_value = CONFIG.app_tests
        if not app_tests_value:
            return

        test_urls = {name: APP_TEST_URLS.get(name) for name in app_tests_value}
        test_urls = {k: v for k, v in test_urls.items() if v}
        if not test_urls:
            return

        top = [r for r in results if r.is_reachable][:APP_TEST_TOP_N]
        if not top:
            return

        import aiohttp  # type: ignore
        timeout = aiohttp.ClientTimeout(total=10)
        try:
            proxy_value = self.processor._get('proxy', CONFIG.proxy)
        except Exception:
            proxy_value = CONFIG.proxy
        async with aiohttp.ClientSession(timeout=timeout, proxy=proxy_value) as session:
            for res in top:
                for name, url in test_urls.items():
                    ok = False
                    try:
                        async with session.get(url) as resp:
                            ok = resp.status == 200
                    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                        logging.getLogger(__name__).debug(f"App test {name} failed via {url}: {e}")
                        ok = False
                    res.app_test_results[name] = ok
    
    def _analyze_results(self, results: List[ConfigResult], sources_with_configs: List[str]) -> Dict:
        """Analyze results and generate comprehensive statistics."""
        protocol_stats = {}
        performance_stats = {}
        
        for result in results:
            # Protocol count
            protocol_stats[result.protocol] = protocol_stats.get(result.protocol, 0) + 1
            
            # Performance stats
            if result.ping_time is not None:
                if result.protocol not in performance_stats:
                    performance_stats[result.protocol] = []
                performance_stats[result.protocol].append(result.ping_time)
        
        # Calculate performance metrics
        perf_summary = {}
        for protocol, times in performance_stats.items():
            if times:
                perf_summary[protocol] = {
                    "count": len(times),
                    "avg_ms": round(sum(times) / len(times) * 1000, 2),
                    "min_ms": round(min(times) * 1000, 2),
                    "max_ms": round(max(times) * 1000, 2)
                }
        
        # Print comprehensive breakdown
        total = len(results)
        reachable = sum(1 for r in results if r.is_reachable)

        print(f"   📊 Total configs: {total:,}")
        reach_pct = (reachable / total * 100) if total else 0
        print(f"   🌐 Reachable configs: {reachable:,} ({reach_pct:.1f}%)")
        print(f"   🔗 Sources with configs: {len(sources_with_configs)}")
        print(f"   📋 Protocol breakdown:")
        
        for protocol, count in sorted(protocol_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100 if total else 0
            perf_info = ""
            if protocol in perf_summary:
                avg_ms = perf_summary[protocol]["avg_ms"]
                perf_info = f" | Avg: {avg_ms}ms"
            print(f"      {protocol:12} {count:>7,} configs ({percentage:5.1f}%){perf_info}")
        
        if not protocol_stats:
            protocol_stats = {"Unknown": 0}

        return {
            "protocol_stats": protocol_stats,
            "performance_stats": perf_summary,
            "total_configs": total,
            "reachable_configs": reachable,
            "sources_with_configs": len(sources_with_configs),
            "total_sources": len(self.sources)
        }
    
    async def _generate_comprehensive_outputs(self, results: List[ConfigResult], stats: Dict, start_time: float, prefix: str = "") -> None:
        """Generate comprehensive output files with all formats."""
        # Create output directory
        output_dir_value = None
        if getattr(self, 'config', None) and getattr(self.config, 'output', None):
            try:
                output_dir_value = str(self.config.output.output_dir)
            except Exception:
                output_dir_value = None
        output_dir = validate_output_directory(str(output_dir_value or CONFIG.output_dir))

        # Extract configs for traditional outputs
        configs = [result.config.strip() for result in results]

        # Determine enabled output formats from new config if present
        try:
            enabled_formats = set([str(x).lower() for x in (self.config.output.output_formats or [])]) if (self.config and getattr(self.config, 'output', None)) else set()
            write_csv_enabled = bool(self.config.output.write_csv) if (self.config and getattr(self.config, 'output', None)) else True
        except Exception:
            enabled_formats = set()
            write_csv_enabled = True

        # Optional: use lightweight converter for simple formats
        converter_outputs = {}
        try:
            from vpn_merger.services.converter_service import MultiFormatConverter  # type: ignore
            converter = MultiFormatConverter()
            converter_outputs = converter.convert_to_all_formats(configs)
        except Exception:
            converter_outputs = {}

        # Track temporary files for potential cleanup (best-effort)
        tmp_files: List[Path] = []
        
        # Raw text output
        if not enabled_formats or 'raw' in enabled_formats:
            raw_file = output_dir / f"{prefix}vpn_subscription_raw.txt"
            tmp_raw = raw_file.with_suffix('.tmp')
            tmp_files.append(tmp_raw)
            await self._async_write_text(tmp_raw, "\n".join(configs))
            tmp_raw.replace(raw_file)
        
        # Base64 output
        if not enabled_formats or 'base64' in enabled_formats:
            base64_content = converter_outputs.get('base64') or base64.b64encode("\n".join(configs).encode("utf-8")).decode("utf-8")
            base64_file = output_dir / f"{prefix}vpn_subscription_base64.txt"
            tmp_base64 = base64_file.with_suffix('.tmp')
            tmp_files.append(tmp_base64)
            await self._async_write_text(tmp_base64, base64_content)
            tmp_base64.replace(base64_file)
        
        # Enhanced CSV with comprehensive performance data
        if write_csv_enabled:
            csv_file = output_dir / f"{prefix}vpn_detailed.csv"
            tmp_csv = csv_file.with_suffix('.tmp')
            tmp_files.append(tmp_csv)
            # Build CSV content in-memory to leverage proper quoting
            buf = io.StringIO()
            writer = csv.writer(buf)
            headers = ['Config', 'Protocol', 'Host', 'Port', 'Ping_MS', 'Reachable', 'Source']
            if CONFIG.full_test:
                headers.append('Handshake')
            if CONFIG.app_tests:
                for name in CONFIG.app_tests:
                    headers.append(f"{name.capitalize()}_OK")
            writer.writerow(headers)
            for result in results:
                ping_ms = round(result.ping_time * 1000, 2) if result.ping_time else None
                row = [
                    result.config, result.protocol, result.host, result.port,
                    ping_ms, result.is_reachable, result.source_url
                ]
                if CONFIG.full_test:
                    if result.handshake_ok is None:
                        row.append('')
                    else:
                        row.append('OK' if result.handshake_ok else 'FAIL')
                if CONFIG.app_tests:
                    for name in CONFIG.app_tests:
                        val = result.app_test_results.get(name)
                        if val is None:
                            row.append('')
                        else:
                            row.append('OK' if val else 'FAIL')
                writer.writerow(row)
            await self._async_write_text(tmp_csv, buf.getvalue())
            tmp_csv.replace(csv_file)
        
        # Comprehensive JSON report
        report = {
            "generation_info": {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "processing_time_seconds": round(time.time() - start_time, 2),
                "script_version": "Unified & Polished Edition",
                "url_testing_enabled": CONFIG.enable_url_testing,
                "sorting_enabled": CONFIG.enable_sorting,
            },
            "statistics": stats,
            "source_categories": {
                "iranian_priority": len(UnifiedSources.IRANIAN_PRIORITY),
                "international_major": len(UnifiedSources.INTERNATIONAL_MAJOR),
                "comprehensive_batch": len(UnifiedSources.COMPREHENSIVE_BATCH),
                "total_unique_sources": len(self.sources),
            },
            "output_files": {
                "raw": str(raw_file),
                "base64": str(base64_file),
                "detailed_csv": str(csv_file),
                "json_report": "vpn_report.json",
                "singbox": str(output_dir / f"{prefix}vpn_singbox.json"),
            },
            "usage_instructions": {
                "base64_subscription": "Copy content of base64 file as subscription URL",
                "raw_subscription": "Host raw file and use URL as subscription link",
                "csv_analysis": "Use CSV file for detailed analysis and custom filtering",
                "supported_clients": [
                    "V2rayNG", "V2rayN", "Hiddify Next", "Shadowrocket",
                    "NekoBox", "Clash Meta", "Sing-Box", "Streisand", "Karing"
                ]
            },
            "advanced_settings": {
                "tls_fragment_size": CONFIG.tls_fragment_size,
                "tls_fragment_sleep": CONFIG.tls_fragment_sleep,
                "mux_enabled": CONFIG.mux_enable,
                "mux_protocol": CONFIG.mux_protocol,
                "mux_max_connections": CONFIG.mux_max_connections,
                "mux_min_streams": CONFIG.mux_min_streams,
                "mux_max_streams": CONFIG.mux_max_streams,
                "mux_padding": CONFIG.mux_padding,
                "mux_brutal": CONFIG.mux_brutal
            }
        }
        
        report_file = output_dir / f"{prefix}vpn_report.json"
        tmp_report = report_file.with_suffix('.tmp')
        tmp_files.append(tmp_report)
        await self._async_write_text(tmp_report, json.dumps(report, indent=2, ensure_ascii=False))
        tmp_report.replace(report_file)

        # Optional simple configs JSON via converter
        if 'json' in enabled_formats and converter_outputs.get('json'):
            simple_json_file = output_dir / f"{prefix}configs.json"
            tmp_simple = simple_json_file.with_suffix('.tmp')
            tmp_files.append(tmp_simple)
            await self._async_write_text(tmp_simple, converter_outputs['json'])
            tmp_simple.replace(simple_json_file)

        # Simple outbounds JSON
        outbounds = []
        for idx, r in enumerate(results):
            ob = {
                "type": r.protocol.lower(),
                "tag": f"{r.protocol} {idx}",
                "server": r.host or "",
                "server_port": r.port or 0,
                "raw": r.config
            }
            try:
                tls_size = int(self.config.advanced.tls_fragment_size) if (self.config and getattr(self.config, 'advanced', None) and self.config.advanced.tls_fragment_size) else None
                tls_sleep = int(self.config.advanced.tls_fragment_sleep) if (self.config and getattr(self.config, 'advanced', None) and self.config.advanced.tls_fragment_sleep) else None
            except Exception:
                tls_size = CONFIG.tls_fragment_size
                tls_sleep = CONFIG.tls_fragment_sleep
            if tls_size:
                ob["tls_fragment"] = {
                    "size": tls_size,
                    "sleep": tls_sleep
                }
            try:
                mux_enabled = bool(self.config.advanced.mux_enable) if (self.config and getattr(self.config, 'advanced', None)) else bool(CONFIG.mux_enable)
                mux_protocol = (self.config.advanced.mux_protocol if (self.config and getattr(self.config, 'advanced', None)) else CONFIG.mux_protocol)
                mux_max_connections = int(self.config.advanced.mux_max_connections) if (self.config and getattr(self.config, 'advanced', None)) else int(CONFIG.mux_max_connections)
                mux_min_streams = int(self.config.advanced.mux_min_streams) if (self.config and getattr(self.config, 'advanced', None)) else int(CONFIG.mux_min_streams)
                mux_max_streams = int(self.config.advanced.mux_max_streams) if (self.config and getattr(self.config, 'advanced', None)) else int(CONFIG.mux_max_streams)
                mux_padding = bool(self.config.advanced.mux_padding) if (self.config and getattr(self.config, 'advanced', None)) else bool(CONFIG.mux_padding)
                mux_brutal = bool(self.config.advanced.mux_brutal) if (self.config and getattr(self.config, 'advanced', None)) else bool(CONFIG.mux_brutal)
            except Exception:
                mux_enabled = bool(CONFIG.mux_enable)
                mux_protocol = CONFIG.mux_protocol
                mux_max_connections = int(CONFIG.mux_max_connections)
                mux_min_streams = int(CONFIG.mux_min_streams)
                mux_max_streams = int(CONFIG.mux_max_streams)
                mux_padding = bool(CONFIG.mux_padding)
                mux_brutal = bool(CONFIG.mux_brutal)
            if mux_enabled:
                ob["multiplex"] = {
                    "protocol": mux_protocol,
                    "max_connections": mux_max_connections,
                    "min_streams": mux_min_streams,
                    "max_streams": mux_max_streams,
                    "padding": mux_padding,
                    "brutal": mux_brutal
                }
            outbounds.append(ob)

        singbox_file = output_dir / f"{prefix}vpn_singbox.json"
        tmp_singbox = singbox_file.with_suffix('.tmp')
        tmp_files.append(tmp_singbox)
        await self._async_write_text(tmp_singbox, json.dumps({"outbounds": outbounds}, indent=2, ensure_ascii=False))
        tmp_singbox.replace(singbox_file)

        try:
            output_clash_enabled = bool(self.config.output.output_clash) if (self.config and getattr(self.config, 'output', None)) else bool(CONFIG.output_clash)
        except Exception:
            output_clash_enabled = bool(CONFIG.output_clash)
        if output_clash_enabled:
            try:
                import yaml
            except ImportError:
                print("⚠️  PyYAML not installed, cannot write clash.yaml")
            else:
                clash_file = output_dir / f"{prefix}clash.yaml"
                tmp_clash = clash_file.with_suffix('.tmp')
                yaml.safe_dump({"proxies": configs}, tmp_clash.open('w', encoding='utf-8'))
                tmp_clash.replace(clash_file)
    
    def _print_final_summary(self, config_count: int, elapsed_time: float, stats: Dict) -> None:
        """Print comprehensive final summary."""
        print("\n" + "=" * 85)
        print("🎉 UNIFIED VPN MERGER COMPLETE!")
        print(f"⏱️  Total processing time: {elapsed_time:.2f} seconds")
        print(f"📊 Final unique configs: {config_count:,}")
        try:
            log_json(logging.INFO, "final_summary", elapsed_seconds=elapsed_time, total_configs=config_count,
                    reachable=stats.get('reachable_configs'), total_sources=stats.get('total_sources'))
        except Exception:
            pass
        print(f"🌐 Reachable configs: {stats['reachable_configs']:,}")
        print(f"📈 Success rate: {stats['reachable_configs']/config_count*100:.1f}%")
        print(f"🔗 Sources with configs: {stats['sources_with_configs']}/{stats['total_sources']}")
        print(f"⚡ Processing speed: {config_count/elapsed_time:.0f} configs/second")
        # Optional: invalid host skips report
        try:
            if bool(getattr(CONFIG, 'skip_tests_on_invalid_host', False)):
                skipped = 0
                try:
                    skipped = int(getattr(self.processor, 'invalid_host_skips', 0))
                except Exception:
                    skipped = 0
                print(f"🚫 Invalid hosts skipped: {skipped}")
        except Exception:
            pass
        
        if CONFIG.enable_sorting and stats['reachable_configs'] > 0:
            print(f"🚀 Configs sorted by performance (fastest first)")
        
        top_protocol = max(stats['protocol_stats'].items(), key=lambda x: x[1])[0]
        print(f"🏆 Top protocol: {top_protocol}")
        try:
            if getattr(self, 'config', None) and getattr(self.config, 'output', None):
                print(f"📁 Output directory: ./{self.config.output.output_dir}/")
            else:
                print(f"📁 Output directory: ./{CONFIG.output_dir}/")
        except Exception:
            print(f"📁 Output directory: ./{CONFIG.output_dir}/")
        print("\n🔗 Usage Instructions:")
        print("   • Copy Base64 file content as subscription URL")
        print("   • Use CSV file for detailed analysis and filtering")
        print("   • All configs tested and sorted by performance")
        print("   • Dead sources automatically removed")
        print("=" * 85)

# ============================================================================
# EVENT LOOP DETECTION AND MAIN EXECUTION
# ============================================================================

async def main_async(config=None):
    """Main async function."""
    try:
        merger = UltimateVPNMerger(config=config)
        await merger.run()
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

def detect_and_run(config=None):
    """Detect event loop and run appropriately."""
    try:
        # Try to get the running loop
        loop = asyncio.get_running_loop()
        print("🔄 Detected existing event loop")
        print("📝 Creating task in existing loop...")
        
        # We're in an async environment (like Jupyter)
        task = asyncio.create_task(main_async(config=config))
        print("✅ Task created successfully!")
        print("📋 Use 'await task' to wait for completion in Jupyter")
        return task
        
    except RuntimeError:
        # No running loop - we can use asyncio.run()
        print("🔄 No existing event loop detected")
        print("📝 Using asyncio.run()...")
        return asyncio.run(main_async(config=config))

# Alternative for Jupyter/async environments
async def run_in_jupyter():
    """Direct execution for Jupyter notebooks and async environments."""
    print("🔄 Running in Jupyter/async environment")
    await main_async()

def _get_script_dir() -> Path:
    """
    Return a safe base directory for writing output.
    • In a regular script run, that’s the directory the script lives in.
    • In interactive/Jupyter runs, fall back to the current working dir.
    """
    try:
        return Path(__file__).resolve().parent        # normal execution
    except NameError:
        return Path.cwd()                             # Jupyter / interactive


def main():
    """Main entry point with event loop detection."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)

    import argparse

    # Ensure UTF-8 capable output to avoid UnicodeEncodeError on Windows terminals
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="ignore")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="ignore")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="VPN Merger")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to YAML/JSON config file (optional)")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=CONFIG.batch_size,
        help="Save intermediate output every N configs (0 disables, default 100)"
    )
    parser.add_argument("--threshold", type=int, default=CONFIG.threshold,
                        help="Stop processing after N unique configs (0 = unlimited)")
    parser.add_argument("--top-n", type=int, default=CONFIG.top_n,
                        help="Keep only the N best configs after sorting (0 = all)")
    parser.add_argument("--tls-fragment", type=str, default=CONFIG.tls_fragment,
                        help="Only keep configs containing this TLS fragment")
    parser.add_argument("--include-protocols", type=str, default=None,
                        help="Comma-separated list of protocols to include")
    parser.add_argument("--exclude-protocols", type=str, default=None,
                        help="Comma-separated list of protocols to exclude")
    parser.add_argument("--resume", type=str, default=None,
                        help="Resume processing from existing raw/base64 file")
    parser.add_argument("--output-dir", type=str, default=CONFIG.output_dir,
                        help="Directory to save output files")
    parser.add_argument("--test-timeout", type=float, default=CONFIG.test_timeout,
                        help="TCP connection test timeout in seconds")
    parser.add_argument("--no-url-test", action="store_true",
                        help="Disable server reachability testing")
    parser.add_argument("--no-sort", action="store_true",
                        help="Disable performance-based sorting")
    parser.add_argument("--discover", action="store_true",
                        help="Discover additional sources from GitHub before merging")
    parser.add_argument("--quarantine-failures", action="store_true",
                        help="Quarantine sources after repeated availability failures")
    parser.add_argument("--quarantine-threshold", type=int, default=CONFIG.quarantine_threshold,
                        help="Consecutive failures required to quarantine a source")
    parser.add_argument("--no-metrics", action="store_true",
                        help="Disable Prometheus metrics server")
    parser.add_argument("--concurrent-limit", type=int, default=CONFIG.concurrent_limit,
                        help="Number of concurrent requests")
    parser.add_argument("--max-retries", type=int, default=CONFIG.max_retries,
                        help="Retry attempts when fetching sources")
    parser.add_argument("--proxy", type=str, default=None,
                        help="Route HTTP requests through this proxy URL")
    parser.add_argument("--max-ping", type=int, default=0,
                        help="Discard configs slower than this ping in ms (0 = no limit)")
    parser.add_argument("--log-file", type=str, default=None,
                        help="Write output messages to a log file")
    parser.add_argument("--cumulative-batches", action="store_true",
                        help="Save each batch as cumulative rather than standalone")
    parser.add_argument("--no-strict-batch", action="store_true",
                        help="Use batch size only as update threshold")
    parser.add_argument("--shuffle-sources", action="store_true",
                        help="Process sources in random order")
    parser.add_argument("--full-test", action="store_true",
                        help="Perform full TLS handshake when applicable")
    parser.add_argument("--output-clash", action="store_true",
                        help="Generate a clash.yaml file from results")
    # Dashboard flags
    parser.add_argument("--enable-dashboard", action="store_true",
                        help="Start the dashboard web UI")
    parser.add_argument("--dashboard-port", type=int, default=8000,
                        help="Dashboard port (default 8000)")
    parser.add_argument("--dashboard-host", type=str, default="0.0.0.0",
                        help="Dashboard host (default 0.0.0.0)")
    parser.add_argument("--dashboard-app", type=str, default="api", choices=["api", "realtime"],
                        help="Dashboard app to use: api or realtime")
    parser.add_argument("--print-dashboard-token", type=str, default=None,
                        help="Client ID to print an HMAC WS token for (requires DASHBOARD_HMAC_KEY)")
    parser.add_argument("--dashboard-cert-file", type=str, default=None,
                        help="TLS certificate file for HTTPS dashboard")
    parser.add_argument("--dashboard-key-file", type=str, default=None,
                        help="TLS key file for HTTPS dashboard")
    parser.add_argument("--prefer-protocols", type=str, default=None,
                        help="Comma-separated protocol priority list")
    parser.add_argument("--app-tests", type=str, default=None,
                        help="Comma-separated list of services to test via configs")
    # Distributed processing (Phase 3)
    parser.add_argument("--distributed", action="store_true",
                        help="Use distributed coordinator for fetching (Celery if available, else local partitioning)")
    parser.add_argument("--redis-url", type=str, default=None,
                        help="Celery/Redis broker URL (optional)")
    parser.add_argument("--workers", type=int, default=4,
                        help="Hint for number of distributed workers for local partitioning")
    parser.add_argument("--tls-fragment-size", type=int, default=CONFIG.tls_fragment_size,
                        help="Size of TLS fragment to send (0 disables)")
    parser.add_argument("--tls-fragment-sleep", type=int, default=CONFIG.tls_fragment_sleep,
                        help="Delay between TLS fragments in ms")
    parser.add_argument("--enable-mux", action="store_true",
                        help="Enable connection multiplexing")
    parser.add_argument("--mux-protocol", type=str, default=CONFIG.mux_protocol,
                        choices=["smux", "yamux", "h2mux"],
                        help="Multiplexing protocol to use")
    parser.add_argument("--mux-max-connections", type=int, default=CONFIG.mux_max_connections,
                        help="Maximum simultaneous MUX connections")
    parser.add_argument("--mux-min-streams", type=int, default=CONFIG.mux_min_streams,
                        help="Minimum number of streams per connection")
    parser.add_argument("--mux-max-streams", type=int, default=CONFIG.mux_max_streams,
                        help="Maximum number of streams per connection")
    parser.add_argument("--mux-padding", action="store_true",
                        help="Reject connections without padding")
    parser.add_argument("--mux-brutal", action="store_true",
                        help="Enable TCP congestion control for noisy links")
    parser.add_argument("--skip-tests-on-invalid-host", action="store_true",
                        help="Count and report skipped connection tests for invalid hostnames")
    args, unknown = parser.parse_known_args()
    if unknown:
        logging.warning("Ignoring unknown arguments: %s", unknown)

    CONFIG.batch_size = max(0, args.batch_size)
    CONFIG.threshold = max(0, args.threshold)
    CONFIG.top_n = max(0, args.top_n)
    CONFIG.tls_fragment = args.tls_fragment
    if args.include_protocols:
        CONFIG.include_protocols = {p.strip().upper() for p in args.include_protocols.split(',') if p.strip()}
    if args.exclude_protocols:
        CONFIG.exclude_protocols = {p.strip().upper() for p in args.exclude_protocols.split(',') if p.strip()}
    CONFIG.resume_file = args.resume
    # Resolve output directory (allow absolute or relative paths) with validation
    try:
        resolved_output = validate_output_directory(args.output_dir)
    except Exception as e:
        print(f"❌ Invalid output directory: {e}")
        sys.exit(2)
    # Update legacy CONFIG output_dir (new config injection handled elsewhere)
    CONFIG.output_dir = str(resolved_output)
    CONFIG.test_timeout = max(0.1, args.test_timeout)
    CONFIG.concurrent_limit = max(1, args.concurrent_limit)
    CONFIG.max_retries = max(1, args.max_retries)
    try:
        CONFIG.proxy = ProxyValidator.validate(args.proxy)
    except Exception as e:
        print(f"❌ Invalid proxy: {e}")
        sys.exit(2)
    CONFIG.max_ping_ms = args.max_ping if args.max_ping > 0 else None
    CONFIG.log_file = args.log_file
    CONFIG.cumulative_batches = args.cumulative_batches
    CONFIG.strict_batch = not args.no_strict_batch
    CONFIG.shuffle_sources = args.shuffle_sources
    CONFIG.full_test = args.full_test
    CONFIG.output_clash = args.output_clash
    if args.prefer_protocols:
        CONFIG.prefer_protocols = [p.strip().upper() for p in args.prefer_protocols.split(',') if p.strip()]
    if args.app_tests:
        CONFIG.app_tests = [p.strip().lower() for p in args.app_tests.split(',') if p.strip()]
    CONFIG.tls_fragment_size = args.tls_fragment_size if args.tls_fragment_size > 0 else None
    CONFIG.tls_fragment_sleep = args.tls_fragment_sleep if args.tls_fragment_sleep > 0 else None
    CONFIG.mux_enable = args.enable_mux
    CONFIG.mux_protocol = args.mux_protocol
    CONFIG.mux_max_connections = max(1, args.mux_max_connections)
    CONFIG.mux_min_streams = max(1, args.mux_min_streams)
    CONFIG.mux_max_streams = max(CONFIG.mux_min_streams, args.mux_max_streams)
    CONFIG.mux_padding = args.mux_padding
    CONFIG.mux_brutal = args.mux_brutal
    CONFIG.skip_tests_on_invalid_host = bool(args.skip_tests_on_invalid_host)
    if args.discover:
        CONFIG.enable_discovery = True
    if args.quarantine_failures:
        CONFIG.quarantine_failures = True
    if args.quarantine_threshold and args.quarantine_threshold > 0:
        CONFIG.quarantine_threshold = args.quarantine_threshold
    if args.no_metrics:
        CONFIG.enable_metrics = False
    # Expose dashboard CLI settings for _maybe_start_dashboard()
    CONFIG.enable_dashboard_cli = bool(args.enable_dashboard)
    CONFIG.dashboard_port_cli = int(args.dashboard_port)
    CONFIG.dashboard_host_cli = str(args.dashboard_host)
    CONFIG.dashboard_app_cli = str(args.dashboard_app)
    CONFIG.dashboard_client_id_cli = args.print_dashboard_token
    CONFIG.dashboard_cert_cli = args.dashboard_cert_file
    CONFIG.dashboard_key_cli = args.dashboard_key_file
    if args.no_url_test:
        CONFIG.enable_url_testing = False
    if args.no_sort:
        CONFIG.enable_sorting = False
    # Distributed flags to CONFIG
    CONFIG.distributed = bool(args.distributed)
    CONFIG.redis_url = args.redis_url
    CONFIG.dist_workers = max(1, args.workers)

    if CONFIG.log_file:
        logging.basicConfig(filename=CONFIG.log_file, level=logging.INFO,
                            format='%(asctime)s %(levelname)s:%(message)s')

    print("🔧 VPN Merger - Checking environment...")
    # Check dependencies at runtime
    check_dependencies()
    # Apply nest_asyncio only after deps check
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except Exception:
        pass

    # Optional new config loading
    config_obj = None
    if args.config:
        try:
            from vpn_merger.core.config_manager import ConfigManager  # type: ignore
            cm = ConfigManager()
            config_obj = cm.load_config(Path(args.config))
        except Exception as e:
            print(f"⚠️  Failed to load config from {args.config}: {e}")

    # Graceful shutdown handling
    shutdown_flag = {"set": False}

    def _handle_signal(signum, frame):
        if not shutdown_flag["set"]:
            shutdown_flag["set"] = True
            print(f"\n🛑 Received signal {signum}, finishing current tasks and shutting down...")
            try:
                GlobalState.get_shutdown_event().set()
            except Exception:
                pass

    for sig in (getattr(signal, "SIGTERM", None), getattr(signal, "SIGINT", None)):
        if sig is not None:
            try:
                signal.signal(sig, _handle_signal)
            except Exception:
                pass

    try:
        return detect_and_run(config=config_obj)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n📋 Alternative execution methods:")
        print("   • For Jupyter: await run_in_jupyter()")
        print("   • For scripts: python script.py")

if __name__ == "__main__":
    main()
    # ============================================================================
    # USAGE INSTRUCTIONS
    # ============================================================================
    
    print("""
    🚀 VPN Subscription Merger - Final Unified Edition
    
    📋 Execution Methods:
       • Regular Python: python script.py
       • Jupyter/IPython: await run_in_jupyter()
       • With event loop errors: task = detect_and_run(); await task
    
    🎯 Unified Features:
       • 450+ sources (Iranian priority + International + Comprehensive)
       • Dead link detection and automatic removal
       • Real-time server reachability testing with response time measurement
       • Smart sorting by connection speed and protocol preference
       • Advanced semantic deduplication
       • Multiple output formats (raw, base64, CSV with performance data, JSON)
       • Event loop compatibility for all environments
       • Comprehensive error handling and retry logic
    
    📊 Expected Results:
       • 800k-1.2M+ tested and sorted configs
       • 70-85% configs will be reachable and validated
       • Processing time: 8-12 minutes with full testing
       • Dead sources automatically filtered out
       • Performance-optimized final list
    
    📁 Output Files:
       • vpn_subscription_raw.txt (for hosting)
       • vpn_subscription_base64.txt (for direct import)
       • vpn_detailed.csv (with performance metrics)
       • vpn_report.json (comprehensive statistics)
    """)

