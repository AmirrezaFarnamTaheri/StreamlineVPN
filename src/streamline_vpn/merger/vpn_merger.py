#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPN Subscription Merger
===================================================================

The definitive VPN subscription merger combining hundreds of sources from `sources.txt` with comprehensive
testing, smart sorting, and automatic dead link removal.

Features:
• Reads from `sources.txt` (over 450 curated repositories)
• Real-time URL availability testing and dead link removal
• Server reachability testing with response time measurement
• Smart sorting by connection speed and protocol preference
• Event loop compatibility (Jupyter, IPython, regular Python)
• Advanced deduplication with semantic analysis
• Multiple output formats (raw, base64, CSV, JSON)
• Comprehensive error handling and retry logic
• Best practices implemented throughout
• Default protocol set optimised for the Hiddify client

Requirements: pip install aiohttp aiodns nest-asyncio
Author: Final Unified Edition - June 30, 2025
Expected Output: 800k-1.2M+ tested and sorted configs
"""

import asyncio
import signal
import logging
import random
import re
import sys
import time
import argparse
import os
import json
import base64
import binascii
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from urllib.parse import urlparse, parse_qs
from tqdm import tqdm

try:
    import colorama

    colorama.just_fix_windows_console()
except Exception:
    pass

from .source_fetcher import (
    fetch_text,
    parse_first_configs,
    UnifiedSources,
    AsyncSourceFetcher,
)
from .result_processor import (
    CONFIG,
    ConfigResult,
    EnhancedConfigProcessor,
)
from .output_writer import (
    generate_comprehensive_outputs,
    EXCLUDE_REGEXES as OUTPUT_EXCLUDE_REGEXES,
    upload_files_to_gist,
    write_upload_links,
)
from .clash_utils import config_to_clash_proxy, flag_emoji, build_clash_config
from .utils import print_public_source_warning, choose_proxy
from .deduplicator import Deduplicator
from .sorter import Sorter
from .analyzer import Analyzer
from .batch_processor import BatchProcessor

try:
    import aiohttp
except ImportError as exc:
    raise ImportError(
        "Missing optional dependency 'aiohttp'. "
        "Run `pip install -r requirements.txt` before running this script."
    ) from exc

# Event loop compatibility fix
try:
    import nest_asyncio
    import os  # noqa: F811

    if __name__ == "__main__" or os.environ.get("NEST_ASYNCIO") == "1":
        nest_asyncio.apply()
        if __name__ == "__main__":
            print("✅ Applied nest_asyncio patch for event loop compatibility")
except ImportError as exc:
    raise ImportError(
        "Missing optional dependency 'nest_asyncio'. "
        "Run `pip install -r requirements.txt` before running this script."
    ) from exc

from .config import load_config

try:
    import aiodns  # noqa: F401
except ImportError as exc:
    raise ImportError(
        "Missing optional dependency 'aiodns'. "
        "Run `pip install -r requirements.txt` before running this script."
    ) from exc

# ============================================================================
# CONFIGURATION & SETTINGS
# ============================================================================


# ============================================================================
# MAIN PROCESSOR WITH UNIFIED FUNCTIONALITY
# ============================================================================


class UltimateVPNMerger:
    """VPN merger with unified functionality and comprehensive testing."""

    def __init__(
        self,
        sources_file: Optional[Union[str, Path]] = None,
        include_regexes: Optional[List[re.Pattern]] = None,
        exclude_regexes: Optional[List[re.Pattern]] = None,
    ):
        self.sources = UnifiedSources.get_all_sources(sources_file)
        if CONFIG.shuffle_sources:
            random.shuffle(self.sources)
        self.processor = EnhancedConfigProcessor()
        self.seen_hashes: Set[str] = set()
        self.seen_hashes_lock = asyncio.Lock()
        self.fetcher = AsyncSourceFetcher(
            self.processor,
            self.seen_hashes,
            self.seen_hashes_lock,
            self._update_history,
            proxy=choose_proxy(CONFIG),
        )
        self.deduplicator = Deduplicator(
            self.processor,
            include_regexes or [],
            exclude_regexes or [],
        )
        self.sorter = Sorter(self.processor, self.proxy_history)
        self.analyzer = Analyzer()
        self.batch_processor = BatchProcessor(self)
        self.batch_counter = 0
        self.next_batch_threshold = (
            CONFIG.save_every if CONFIG.save_every else float("inf")
        )
        self.start_time = 0.0
        self.available_sources: List[str] = []
        self.all_results: List[ConfigResult] = []
        self.stop_fetching = False
        self.saved_hashes: Set[str] = set()
        self.cumulative_unique: List[ConfigResult] = []
        self.last_processed_index = 0
        self.last_saved_count = 0
        self.current_progress: Optional[tqdm] = None
        self._file_lock = asyncio.Lock()
        self._history_lock = asyncio.Lock()
        # Store proxy history in configurable location
        hist_path = Path(CONFIG.history_file)
        if not hist_path.is_absolute():
            hist_path = Path(CONFIG.output_dir) / hist_path
        self.history_path = hist_path
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.proxy_history = json.loads(self.history_path.read_text())
        except (OSError, json.JSONDecodeError):
            self.proxy_history = {}

    async def _update_history(
        self,
        config_hash: str,
        success: bool,
        latency: Optional[float],
    ) -> None:
        async with self._history_lock:
            entry = self.proxy_history.setdefault(
                config_hash,
                {
                    "last_latency_ms": None,
                    "last_seen_online_utc": None,
                    "successful_checks": 0,
                    "total_checks": 0,
                },
            )
            entry["total_checks"] += 1
            if success:
                entry["successful_checks"] += 1
                entry["last_seen_online_utc"] = datetime.now(timezone.utc).isoformat()
            entry["last_latency_ms"] = (
                round(latency * 1000) if latency is not None else None
            )

    async def _save_proxy_history(self) -> None:
        async with self._file_lock:
            tmp = self.history_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.proxy_history, indent=2))
            tmp.replace(self.history_path)

    def _register_signal_handlers(self) -> None:
        """Set up SIGINT handler to close progress bars gracefully."""

        def handler() -> None:
            self.stop_fetching = True
            if self.current_progress:
                self.current_progress.close()
                if self.fetcher.progress is self.current_progress:
                    self.fetcher.progress = None
                self.current_progress = None
            if self.fetcher.progress:
                self.fetcher.progress.close()
                self.fetcher.progress = None

        try:
            loop = asyncio.get_running_loop()
            loop.add_signal_handler(signal.SIGINT, handler)
        except (RuntimeError, NotImplementedError, AttributeError):
            signal.signal(signal.SIGINT, lambda s, f: handler())

    async def _load_existing_results(self, path: str) -> List[ConfigResult]:
        """Load previously saved configs from a raw or base64 file."""
        try:
            text = Path(path).read_text(encoding="utf-8").strip()
        except OSError as e:
            print(f"⚠️  Failed to read resume file: {e}")
            return []

        if text and "://" not in text.splitlines()[0]:
            try:
                text = base64.b64decode(text).decode("utf-8")
            except (binascii.Error, UnicodeDecodeError) as exc:
                logging.debug("resume base64 decode failed: %s", exc)

        results = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            protocol = self.processor.categorize_protocol(line)
            host, port = self.processor.extract_host_port(line)
            country = await self.processor.lookup_country(host) if host else None
            results.append(
                ConfigResult(
                    config=line,
                    protocol=protocol,
                    host=host,
                    port=port,
                    source_url="(resume)",
                    country=country,
                )
            )
            h = self.processor.create_semantic_hash(line)
            async with self.seen_hashes_lock:
                self.seen_hashes.add(h)
        return results

    async def run(self) -> None:
        """Execute the complete unified merging process."""
        print("🚀 VPN Subscription Merger - Final Unified & Polished Edition")
        print("=" * 85)
        print(f"📊 Total sources: {len(self.sources)}")
        print(
            f"🔧 URL Testing: {'Enabled' if CONFIG.enable_url_testing else 'Disabled'}"
        )
        print(f"📈 Smart Sorting: {'Enabled' if CONFIG.enable_sorting else 'Disabled'}")
        print()

        self._register_signal_handlers()
        start_time = time.time()
        self.start_time = start_time

        if CONFIG.resume_file:
            print(f"🔄 Loading existing configs from {CONFIG.resume_file} ...")
            self.all_results.extend(
                await self._load_existing_results(CONFIG.resume_file)
            )
            print(f"   ✔ Loaded {len(self.all_results)} configs from resume file")
            await self.batch_processor.maybe_save_batch()

        # Step 1: Test source availability and remove dead links
        print("🔄 [1/6] Testing source availability and removing dead links...")
        source_tester = SourceTester(self.fetcher)
        self.available_sources = await source_tester.test_and_filter_sources(
            self.sources
        )

        if CONFIG.enable_url_testing:
            print("\n🔎 Running pre-flight connectivity check...")
            ok = await source_tester.preflight_connectivity_check(
                self.available_sources, 10
            )
            if not ok:
                sys.stderr.write(
                    "❌ Critical Error: All initial connectivity tests failed. Please check your internet connection and firewall, then try again.\n"
                )
                sys.exit(1)

        # Step 2: Fetch all configs from available sources
        print(
            f"\n🔄 [2/6] Fetching configs from {len(self.available_sources)} available sources..."
        )
        await self.fetcher.fetch_all_sources(self)

        # Step 3: Deduplicate efficiently
        print(f"\n🔍 [3/6] Deduplicating {len(self.all_results):,} configs...")
        unique_results = self.deduplicator.deduplicate(self.all_results)

        # Step 4: Sort by performance if enabled
        if CONFIG.enable_sorting:
            print(
                f"\n📊 [4/6] Sorting {len(unique_results):,} configs by performance..."
            )
            unique_results = self._sort_by_performance(unique_results)
        else:
            print("\n⏭️ [4/6] Skipping sorting (disabled)")

        if CONFIG.enable_url_testing:
            before = len(unique_results)
            unique_results = [r for r in unique_results if r.ping_time is not None]
            removed = before - len(unique_results)
            print(f"   ❌ Removed {removed} configs with no ping")

        if CONFIG.top_n > 0:
            unique_results = unique_results[: CONFIG.top_n]
            print(f"   🔝 Keeping top {CONFIG.top_n} configs")

        if CONFIG.max_ping_ms is not None and CONFIG.enable_url_testing:
            before = len(unique_results)
            unique_results = [
                r
                for r in unique_results
                if r.ping_time is not None and r.ping_time * 1000 <= CONFIG.max_ping_ms
            ]
            removed = before - len(unique_results)
            print(f"   ⏱️  Removed {removed} configs over {CONFIG.max_ping_ms} ms")

        # Step 5: Analyze protocols and performance
        print(f"\n📋 [5/6] Analyzing {len(unique_results):,} unique configs...")
        stats = self.analyzer.analyze(
            unique_results, self.available_sources, len(self.sources)
        )

        # Step 6: Generate comprehensive outputs
        print("\n💾 [6/6] Generating comprehensive outputs...")
        await self._generate_comprehensive_outputs(
            unique_results, stats, self.start_time
        )

        await self._save_proxy_history()

        self._print_final_summary(
            len(unique_results), time.time() - self.start_time, stats
        )

        elapsed = time.time() - start_time
        summary = (
            f"Sources checked: {len(self.available_sources)} | "
            f"Configs fetched: {len(self.all_results)} | "
            f"Unique configs: {len(unique_results)} | "
            f"Elapsed: {elapsed:.1f}s"
        )
        print(summary)
        logging.info(summary)

        # Clean up tester resources
        await self.processor.tester.close()

    def _sort_by_performance(self, results: List[ConfigResult]) -> List[ConfigResult]:
        """Sort results by connection performance and protocol preference."""
        progress = tqdm(total=len(results), desc="Sorting", unit="cfg", leave=False)
        self.current_progress = progress
        try:
            return self.sorter.sort_by_performance(results, progress)
        finally:
            progress.close()
            self.current_progress = None

    def _parse_extra_params(self, link: str) -> Dict[str, Any]:
        """Extract additional parameters for sing-box outbounds."""
        try:
            p = urlparse(link)
            q = parse_qs(p.query)
            scheme = p.scheme.lower()
            extra: Dict[str, Any] = {}
            if scheme in {"vless", "reality"}:
                pbk = (
                    q.get("pbk")
                    or q.get("public-key")
                    or q.get("publicKey")
                    or q.get("public_key")
                    or q.get("publickey")
                )
                sid = (
                    q.get("sid")
                    or q.get("short-id")
                    or q.get("shortId")
                    or q.get("short_id")
                    or q.get("shortid")
                )
                spider = q.get("spiderX") or q.get("spider-x") or q.get("spider_x")
                if pbk:
                    extra["publicKey"] = pbk[0]
                if sid:
                    extra["shortId"] = sid[0]
                if spider:
                    extra["spiderX"] = spider[0]
            elif scheme == "tuic":
                uuid = p.username or q.get("uuid", [None])[0]
                password = p.password or q.get("password", [None])[0]
                if uuid:
                    extra["uuid"] = uuid
                if password:
                    extra["password"] = password
                if "alpn" in q:
                    extra["alpn"] = q["alpn"][0]
                cc = q.get("congestion-control") or q.get("congestion_control")
                if cc:
                    extra["congestion-control"] = cc[0]
                mode = q.get("udp-relay-mode") or q.get("udp_relay_mode")
                if mode:
                    extra["udp-relay-mode"] = mode[0]
            elif scheme in {"hy2", "hysteria2"}:
                passwd = p.password or q.get("password", [None])[0]
                if p.username and not passwd:
                    passwd = p.username
                if passwd:
                    extra["password"] = passwd
                for key in (
                    "auth",
                    "peer",
                    "sni",
                    "insecure",
                    "alpn",
                    "obfs",
                    "obfs-password",
                ):
                    if key in q:
                        extra[key.replace("-", "_")] = q[key][0]
                up_keys = ["upmbps", "up", "up_mbps"]
                down_keys = ["downmbps", "down", "down_mbps"]
                for k in up_keys:
                    if k in q:
                        extra["upmbps"] = q[k][0]
                        break
                for k in down_keys:
                    if k in q:
                        extra["downmbps"] = q[k][0]
                        break
            return extra
        except Exception:
            return {}

    async def _generate_comprehensive_outputs(
        self,
        results: List[ConfigResult],
        stats: Dict,
        start_time: float,
        prefix: str = "",
    ) -> None:
        await generate_comprehensive_outputs(self, results, stats, start_time, prefix)

    def _print_final_summary(
        self, config_count: int, elapsed_time: float, stats: Dict
    ) -> None:
        """Print comprehensive final summary."""
        print("\n" + "=" * 85)
        print("🎉 UNIFIED VPN MERGER COMPLETE!")
        print(f"⏱️  Total processing time: {elapsed_time:.2f} seconds")
        print(f"📊 Final unique configs: {config_count:,}")
        print(f"🌐 Reachable configs: {stats['reachable_configs']:,}")
        if config_count:
            success = f"{stats['reachable_configs'] / config_count * 100:.1f}%"
        else:
            success = "N/A"
        print(f"📈 Success rate: {success}")
        if CONFIG.sort_by == "reliability":
            total_checks = sum(
                h.get("total_checks", 0) for h in self.proxy_history.values()
            )
            successes = sum(
                h.get("successful_checks", 0) for h in self.proxy_history.values()
            )
            if total_checks:
                avg_rel = successes / total_checks * 100
                reliability = f"{avg_rel:.1f}% over {total_checks} checks"
            else:
                reliability = "N/A over 0 checks"
            print(f"⭐ Average reliability: {reliability}")
        speed = (config_count / elapsed_time) if elapsed_time else 0

        rows = [
            ("Total configs", f"{config_count:,}"),
            ("Reachable", f"{stats['reachable_configs']:,}"),
            ("Success rate", success),
            ("Sources", f"{stats['available_sources']}/{stats['total_sources']}"),
            ("Speed", f"{speed:.0f} cfg/s"),
        ]
        print("\033[95m\nSUMMARY\033[0m")
        print("\033[94m┌────────────────────┬──────────────┐\033[0m")
        for label, value in rows:
            print(f"\033[94m│ {label:<18} │\033[92m {value:<12}\033[94m│\033[0m")
        print("\033[94m└────────────────────┴──────────────┘\033[0m")
        if CONFIG.enable_sorting and stats["reachable_configs"] > 0:
            print("🚀 Configs sorted by performance (fastest first)")
        if stats["protocol_stats"]:
            top_protocol = max(stats["protocol_stats"].items(), key=lambda x: x[1])[0]
        else:
            top_protocol = "N/A"
        print(f"🏆 Top protocol: {top_protocol}")
        print(f"📁 Output directory: ./{CONFIG.output_dir}/")


# ============================================================================
# EVENT LOOP DETECTION AND MAIN EXECUTION
# ============================================================================


async def main_async(
    sources_file: Optional[Union[str, Path]] = None,
    include_regexes: Optional[List[re.Pattern]] = None,
    exclude_regexes: Optional[List[re.Pattern]] = None,
):
    """Main async function."""
    try:
        merger = UltimateVPNMerger(
            sources_file,
            include_regexes=include_regexes,
            exclude_regexes=exclude_regexes,
        )
        await merger.run()
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
    except (OSError, aiohttp.ClientError, ValueError, RuntimeError) as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


def detect_and_run(
    sources_file: Optional[Union[str, Path]] = None,
    include_regexes: Optional[List[re.Pattern]] = None,
    exclude_regexes: Optional[List[re.Pattern]] = None,
):
    """Detect event loop and run appropriately."""
    try:
        # Try to get the running loop
        asyncio.get_running_loop()
        print("🔄 Detected existing event loop")
        print("📝 Creating task in existing loop...")

        # We're in an async environment (like Jupyter)
        task = asyncio.create_task(
            main_async(
                sources_file,
                include_regexes=include_regexes,
                exclude_regexes=exclude_regexes,
            )
        )
        print("✅ Task created successfully!")
        print("📋 Use 'await task' to wait for completion in Jupyter")
        return task

    except RuntimeError:
        # No running loop - we can use asyncio.run()
        print("🔄 No existing event loop detected")
        print("📝 Using asyncio.run()...")
        return asyncio.run(
            main_async(
                sources_file,
                include_regexes=include_regexes,
                exclude_regexes=exclude_regexes,
            )
        )


# Alternative for Jupyter/async environments
async def run_in_jupyter(sources_file: Optional[Union[str, Path]] = None):
    """Direct execution for Jupyter notebooks and async environments."""
    print("🔄 Running in Jupyter/async environment")
    await main_async(sources_file)
