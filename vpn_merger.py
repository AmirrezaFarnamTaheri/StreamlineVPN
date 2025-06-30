#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultimate VPN Subscription Merger - Final, Unabbreviated Edition
================================================================

This script fetches, tests, and merges VPN configurations from a massive, curated
list of public sources. It's designed for ease of use, resilience, and providing
the best possible performance by sorting servers based on real-world latency.
"""

import asyncio
import aiohttp
import base64
import csv
import hashlib
import json
import logging
import re
import ssl
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
from datetime import datetime, timezone
import argparse

# --- Compatibility and Dependency Handling ---
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    # This is fine for standard execution but may be needed for some IDEs or notebooks.
    pass

# --- Constants and Configuration ---
VERSION = "3.0.0"
SCRIPT_START_TIME = time.time()
CHECKPOINT_DIR = Path(".checkpoints")
CHECKPOINT_SOURCES_FILE = CHECKPOINT_DIR / "available_sources.json"

@dataclass
class Config:
    """Stores all operational settings for the script."""
    request_timeout: int = 20
    connect_timeout: float = 5.0
    max_retries: int = 2
    concurrent_limit: int = 200
    valid_prefixes: Tuple[str, ...] = (
        "vmess://", "vless://", "ss://", "ssr://", "trojan://", "tuic://", "hy2://", "hysteria://"
    )
    enable_testing: bool = True
    enable_sorting: bool = True
    test_timeout: float = 4.0
    output_dir: Path = Path("output")
    resume: bool = False

class Colors:
    """ANSI color codes for richer terminal output."""
    HEADER, OKBLUE, OKCYAN, OKGREEN, WARNING, FAIL, ENDC, BOLD, UNDERLINE = \
    '\033[95m', '\033[94m', '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[0m', '\033[1m', '\033[4m'

# ===========================================================================
# SOURCE COLLECTION (UNABBREVIATED)
# ===========================================================================

class UnifiedSources:
    """
    Manages the comprehensive, unified collection of all VPN subscription sources.
    This is the full, unabbreviated list from the original code.
    """
    SOURCES = [
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
        "https://raw.githubusercontent.com/Rayan-Config/C-Sub/refs/heads/main/configs/proxy.txt",
        "https://raw.githubusercontent.com/Rayan-Config/C-Sub/refs/heads/main/configs/singbox_configs.json",
        
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

	# Rayan
	"https://raw.githubusercontent.com/Rayan-Config/Rayan-Config.github.io/refs/heads/main/All",        

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
    ]
    

    @classmethod
    def get_all_sources(cls) -> List[str]:
        """Returns a deduplicated list of all sources, maintaining order."""
        # Use dict.fromkeys to remove duplicates while preserving insertion order
        return list(dict.fromkeys(cls.SOURCES))

# ===========================================================================
# CORE LOGIC & CLASSES
# ===========================================================================

@dataclass
class ConfigResult:
    """Represents a tested and processed VPN configuration."""
    config: str
    protocol: str
    host: Optional[str] = None
    port: Optional[int] = None
    ping_time: Optional[float] = None
    is_reachable: bool = False
    source_url: str = ""

class Utility:
    """Helper class for various utility functions."""

    @staticmethod
    def print_header():
        """Prints the script's header to the console."""
        print(f"{Colors.HEADER}{'='*85}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKCYAN}🚀 Ultimate VPN Subscription Merger - Version {VERSION}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*85}{Colors.ENDC}")

    @staticmethod
    def update_progress(label: str, progress: int, total: int, color: str = Colors.OKCYAN):
        """Displays or updates a progress bar on a single line in the terminal."""
        bar_length = 40
        percent = 100 * (progress / float(total))
        filled_length = int(bar_length * progress // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        sys.stdout.write(f"\r{color}{label: <12} |{bar}| {percent:6.2f}% ({progress}/{total}){Colors.ENDC}")
        sys.stdout.flush()
        if progress == total:
            sys.stdout.write('\n')

    @staticmethod
    def extract_host_port(config_str: str) -> Tuple[Optional[str], Optional[int]]:
        """Extracts host and port from a VPN configuration URI."""
        try:
            if config_str.startswith(("vmess://", "vless://")):
                try:
                    # Handle Base64 encoded JSON for vmess and vless
                    json_part = base64.b64decode(config_str.split("://")[1]).decode("utf-8", "ignore")
                    data = json.loads(json_part)
                    return data.get("add"), int(data.get("port", 0))
                except (json.JSONDecodeError, TypeError, ValueError):
                    return None, None # Ignore configs with invalid base64/json
            else:
                # Handle standard URI formats (trojan, ss, etc.)
                parsed_uri = urlparse(config_str)
                if parsed_uri.hostname and parsed_uri.port:
                    return parsed_uri.hostname, parsed_uri.port
                # Fallback for user:pass@host:port format often found in ss://
                match = re.search(r"@([^:]+):(\d+)", config_str)
                if match:
                    return match.group(1), int(match.group(2))
        except Exception:
            pass # Ignore any parsing errors
        return None, None

    @staticmethod
    def get_protocol(config_str: str) -> str:
        """Determines the protocol from the configuration URI prefix."""
        return config_str.split("://")[0].capitalize() if "://" in config_str else "Unknown"

class AsyncProcessor:
    """Handles all asynchronous network operations."""

    def __init__(self, config: Config):
        self.config = config
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Initializes the aiohttp session."""
        # Use a more robust SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(limit_per_host=20, ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector, headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.config.request_timeout))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Closes the aiohttp session."""
        if self.session:
            await self.session.close()

    async def test_source_availability(self, url: str) -> bool:
        """Checks if a source URL is accessible."""
        try:
            async with self.session.head(url, allow_redirects=True, timeout=self.config.connect_timeout) as response:
                return response.status == 200
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return False

    async def fetch_configs_from_source(self, url: str) -> List[str]:
        """Fetches and decodes configurations from a single source URL."""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return []
                content = await response.text(encoding='utf-8', errors='ignore')

                # Try decoding if it looks like a single base64 string
                try:
                    # A simple heuristic: no newlines and is long enough
                    if '\n' not in content and len(content) > 100:
                        decoded_content = base64.b64decode(content).decode('utf-8', errors='ignore')
                        # Check if decoding produced valid-looking config lines
                        if "://" in decoded_content:
                            content = decoded_content
                except Exception:
                    pass # Not a base64 string, proceed with content as is

                return [line.strip() for line in content.splitlines() if any(line.strip().startswith(p) for p in self.config.valid_prefixes)]
        except Exception:
            return []

    async def test_connection(self, host: str, port: int) -> Optional[float]:
        """Tests TCP connection to a server and returns latency in seconds."""
        if not self.config.enable_testing:
            return 9999.0 # Return a placeholder value if testing is disabled

        start_time = time.time()
        try:
            # Use asyncio's wait_for for a clean timeout mechanism
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=self.config.test_timeout
            )
            writer.close()
            await writer.wait_closed()
            return time.time() - start_time
        except Exception:
            return None

class VPNMerger:
    """Main class to orchestrate the VPN merging process."""

    def __init__(self, config: Config):
        self.config = config
        self.sources = UnifiedSources.get_all_sources()
        self.all_configs: Set[str] = set()
        self.processed_results: List[ConfigResult] = []

    async def run(self):
        """Executes the entire workflow."""
        Utility.print_header()
        available_sources = await self._get_available_sources()
        await self._fetch_all_configs(available_sources)
        await self._process_configs()
        if self.config.enable_sorting:
            self._sort_results()
        self._generate_outputs()
        self._print_summary()

    async def _get_available_sources(self) -> List[str]:
        """Tests all sources for availability. Uses a checkpoint if `resume` is enabled."""
        CHECKPOINT_DIR.mkdir(exist_ok=True)
        if self.config.resume and CHECKPOINT_SOURCES_FILE.exists():
            print(f"{Colors.OKGREEN}✅ Resuming from checkpoint: Loading available sources...{Colors.ENDC}")
            with open(CHECKPOINT_SOURCES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data['sources']

        print("🔄 Step 1: Testing source availability...")
        available_sources = []
        progress_counter = 0
        total_sources = len(self.sources)

        async with AsyncProcessor(self.config) as processor:
            tasks = [processor.test_source_availability(url) for url in self.sources]
            for i, task in enumerate(asyncio.as_completed(tasks)):
                if await task:
                    available_sources.append(self.sources[i])
                progress_counter += 1
                Utility.update_progress("Testing...", progress_counter, total_sources)

        print(f"\n{Colors.OKGREEN}✅ Found {len(available_sources)} available sources out of {total_sources}.{Colors.ENDC}")
        with open(CHECKPOINT_SOURCES_FILE, 'w', encoding='utf-8') as f:
            json.dump({'sources': available_sources, 'timestamp': datetime.now(timezone.utc).isoformat()}, f)
        return available_sources

    async def _fetch_all_configs(self, sources: List[str]):
        """Fetches configurations from all available sources concurrently."""
        print("🔄 Step 2: Fetching configurations from sources...")
        progress_counter = 0
        total_sources = len(sources)

        async with AsyncProcessor(self.config) as processor:
            tasks = [processor.fetch_configs_from_source(url) for url in sources]
            for task in asyncio.as_completed(tasks):
                configs = await task
                self.all_configs.update(configs)
                progress_counter += 1
                Utility.update_progress("Fetching...", progress_counter, total_sources)

        print(f"\n{Colors.OKGREEN}✅ Fetched a total of {len(self.all_configs)} unique configurations.{Colors.ENDC}")

    async def _process_configs(self):
        """Tests all fetched configurations for reachability and latency."""
        print("🔄 Step 3: Testing and processing configurations...")
        if not self.config.enable_testing:
            print(f"{Colors.WARNING}⚠️ Connection testing is disabled. Reachability and ping will not be checked.{Colors.ENDC}")

        progress_counter = 0
        total_configs = len(self.all_configs)

        async with AsyncProcessor(self.config) as processor:
            tasks = []
            for config_str in self.all_configs:
                host, port = Utility.extract_host_port(config_str)
                if host and port:
                    tasks.append(self._test_and_create_result(processor, config_str, host, port))

            for task in asyncio.as_completed(tasks):
                result = await task
                if result:
                    self.processed_results.append(result)
                progress_counter += 1
                Utility.update_progress("Processing..", progress_counter, total_configs, Colors.WARNING)

        reachable_count = sum(1 for r in self.processed_results if r.is_reachable)
        print(f"\n{Colors.OKGREEN}✅ Processed all configurations. Found {reachable_count} reachable servers.{Colors.ENDC}")

    async def _test_and_create_result(self, processor: AsyncProcessor, config_str: str, host: str, port: int) -> Optional[ConfigResult]:
        """Helper to test a single config and create a result object."""
        ping = await processor.test_connection(host, port)
        return ConfigResult(
            config=config_str,
            protocol=Utility.get_protocol(config_str),
            host=host,
            port=port,
            ping_time=ping,
            is_reachable=ping is not None
        )

    def _sort_results(self):
        """Sorts the processed results based on reachability and ping time."""
        print("🔄 Step 4: Sorting configurations by performance...")
        self.processed_results.sort(key=lambda x: (not x.is_reachable, x.ping_time or float('inf')))
        print(f"{Colors.OKGREEN}✅ Sorting complete.{Colors.ENDC}")

    def _generate_outputs(self):
        """Generates all output files."""
        print("🔄 Step 5: Generating output files...")
        self.config.output_dir.mkdir(exist_ok=True)

        raw_configs = [res.config for res in self.processed_results]
        raw_content = "\n".join(raw_configs)
        (self.config.output_dir / "ultimate_vpn_subscription_raw.txt").write_text(raw_content, encoding="utf-8")

        base64_content = base64.b64encode(raw_content.encode("utf-8")).decode("utf-8")
        (self.config.output_dir / "ultimate_vpn_subscription_base64.txt").write_text(base64_content, encoding="utf-8")

        with open(self.config.output_dir / "ultimate_vpn_detailed.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Protocol', 'Host', 'Port', 'Ping_MS', 'Reachable', 'Config'])
            for res in self.processed_results:
                writer.writerow([
                    res.protocol, res.host, res.port,
                    f"{res.ping_time * 1000:.2f}" if res.ping_time else 'N/A',
                    res.is_reachable, res.config
                ])

        report = {
            "metadata": {"version": VERSION, "timestamp_utc": datetime.now(timezone.utc).isoformat(), "processing_time_seconds": round(time.time() - SCRIPT_START_TIME, 2)},
            "stats": {"total_sources_checked": len(self.sources), "total_configs_found": len(self.all_configs), "total_configs_processed": len(self.processed_results), "reachable_servers": sum(1 for r in self.processed_results if r.is_reachable)},
            "configs": [asdict(res) for res in self.processed_results]
        }
        (self.config.output_dir / "ultimate_vpn_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

        print(f"{Colors.OKGREEN}✅ All output files generated in '{self.config.output_dir}' directory.{Colors.ENDC}")

    def _print_summary(self):
        """Prints a final summary of the execution."""
        total_processed = len(self.processed_results)
        if total_processed == 0:
            print(f"\n{Colors.FAIL}No configurations could be processed. Please check the sources.{Colors.ENDC}")
            return
            
        reachable = sum(1 for r in self.processed_results if r.is_reachable)
        elapsed_time = time.time() - SCRIPT_START_TIME

        print(f"\n{Colors.HEADER}{'='*85}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKCYAN}🎉 Processing Complete!{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*85}{Colors.ENDC}")
        print(f"  {Colors.BOLD}Execution Time:{Colors.ENDC} {elapsed_time:.2f} seconds")
        print(f"  {Colors.BOLD}Total Configs Processed:{Colors.ENDC} {total_processed}")
        print(f"  {Colors.BOLD}Reachable Servers:{Colors.ENDC} {Colors.OKGREEN}{reachable}{Colors.ENDC} ({reachable/total_processed:.1%})")

        if self.processed_results and self.processed_results[0].is_reachable:
            fastest = self.processed_results[0]
            print(f"  {Colors.BOLD}Fastest Server:{Colors.ENDC} {fastest.host} ({fastest.protocol}) with a ping of {Colors.OKGREEN}{fastest.ping_time*1000:.2f} ms{Colors.ENDC}")

        print(f"\n{Colors.BOLD}Output files are ready in the '{Colors.UNDERLINE}{self.config.output_dir}{Colors.ENDC}' directory.")
        print(f"{Colors.HEADER}{'-'*85}{Colors.ENDC}")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Ultimate VPN Subscription Merger.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--no-test", action="store_false", dest="enable_testing", help="Disable server connection testing (faster, but no ping data).")
    parser.add_argument("--no-sort", action="store_false", dest="enable_sorting", help="Disable sorting of results by performance.")
    parser.add_argument("--resume", action="store_true", help="Resume from the last checkpoint (skips source testing if data exists).")
    parser.add_argument("-o", "--output", type=Path, default=Path("output"), help="Specify the output directory for generated files.")
    
    args = parser.parse_args()

    config = Config(enable_testing=args.enable_testing, enable_sorting=args.enable_sorting, resume=args.resume, output_dir=args.output)
    merger = VPNMerger(config)

    try:
        asyncio.run(merger.run())
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠️ Process interrupted by user. Exiting gracefully.{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ An unexpected error occurred: {e}{Colors.ENDC}")
        logging.exception("Detailed traceback:")

if __name__ == "__main__":
    if sys.version_info < (3, 8):
        sys.exit("❌ This script requires Python 3.8 or newer.")
    main()
