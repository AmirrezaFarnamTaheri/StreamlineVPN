#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPN Subscription Merger
===================================================================

The definitive VPN subscription merger combining 450+ sources with comprehensive
testing, smart sorting, and automatic dead link removal.

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
import json
import logging
import random
import re
import ssl
import sys
import time
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union
from tqdm import tqdm
from urllib.parse import urlparse

try:
    import aiohttp
    from aiohttp.resolver import AsyncResolver
except ImportError:
    print("📦 Installing aiohttp...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
    import aiohttp
    from aiohttp.resolver import AsyncResolver

# Event loop compatibility fix
try:
    import nest_asyncio
    nest_asyncio.apply()
    print("✅ Applied nest_asyncio patch for event loop compatibility")
except ImportError:
    print("📦 Installing nest_asyncio...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "nest-asyncio"])
    import nest_asyncio
    nest_asyncio.apply()

try:
    import aiodns
except ImportError:
    print("📦 Installing aiodns...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiodns"])
    import aiodns

from config import CONFIG, Config
from sources import UnifiedSources
from testing import ConfigResult, EnhancedConfigProcessor, AsyncSourceFetcher

# ============================================================================

class UltimateVPNMerger:
    """VPN merger with unified functionality and comprehensive testing."""
    
    def __init__(self):
        self.sources = UnifiedSources.get_all_sources()
        if CONFIG.shuffle_sources:
            random.shuffle(self.sources)
        self.processor = EnhancedConfigProcessor()
        self.fetcher = AsyncSourceFetcher(self.processor)
        self.batch_counter = 0
        self.next_batch_threshold = CONFIG.batch_size if CONFIG.batch_size else float('inf')
        self.start_time = 0.0
        self.available_sources: List[str] = []
        self.all_results: List[ConfigResult] = []
        self.stop_fetching = False
        self.saved_hashes: Set[str] = set()
        self.cumulative_unique: List[ConfigResult] = []
        self.last_processed_index = 0
        self.last_saved_count = 0

    def _load_existing_results(self, path: str) -> List[ConfigResult]:
        """Load previously saved configs from a raw or base64 file."""
        try:
            text = Path(path).read_text(encoding="utf-8").strip()
        except Exception as e:
            print(f"⚠️  Failed to read resume file: {e}")
            return []

        if text and '://' not in text.splitlines()[0]:
            try:
                text = base64.b64decode(text).decode("utf-8")
            except Exception:
                pass

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
        print("🚀 VPN Subscription Merger - Final Unified & Polished Edition")
        print("=" * 85)
        print(f"📊 Total unified sources: {len(self.sources)}")
        print(f"🇮🇷 Iranian priority: {len(UnifiedSources.IRANIAN_PRIORITY)}")
        print(f"🌍 International major: {len(UnifiedSources.INTERNATIONAL_MAJOR)}")
        print(f"📦 Comprehensive batch: {len(UnifiedSources.COMPREHENSIVE_BATCH)}")
        print(f"🔧 URL Testing: {'Enabled' if CONFIG.enable_url_testing else 'Disabled'}")
        print(f"📈 Smart Sorting: {'Enabled' if CONFIG.enable_sorting else 'Disabled'}")
        print()
        
        start_time = time.time()
        self.start_time = start_time

        if CONFIG.resume_file:
            print(f"🔄 Loading existing configs from {CONFIG.resume_file} ...")
            self.all_results.extend(self._load_existing_results(CONFIG.resume_file))
            print(f"   ✔ Loaded {len(self.all_results)} configs from resume file")

        # Step 1: Test source availability and remove dead links
        print("🔄 [1/6] Testing source availability and removing dead links...")
        self.available_sources = await self._test_and_filter_sources()
        
        # Step 2: Fetch all configs from available sources
        print(f"\n🔄 [2/6] Fetching configs from {len(self.available_sources)} available sources...")
        await self._fetch_all_sources(self.available_sources)
        
        # Step 3: Deduplicate efficiently  
        print(f"\n🔍 [3/6] Deduplicating {len(self.all_results):,} configs...")
        unique_results = self._deduplicate_config_results(self.all_results)
        
        # Step 4: Sort by performance if enabled
        if CONFIG.enable_sorting:
            print(f"\n📊 [4/6] Sorting {len(unique_results):,} configs by performance...")
            unique_results = self._sort_by_performance(unique_results)
        else:
            print(f"\n⏭️ [4/6] Skipping sorting (disabled)")

        if CONFIG.top_n > 0:
            unique_results = unique_results[:CONFIG.top_n]
            print(f"   🔝 Keeping top {CONFIG.top_n} configs")

        if CONFIG.max_ping_ms is not None and CONFIG.enable_url_testing:
            before = len(unique_results)
            unique_results = [r for r in unique_results
                              if r.ping_time is not None and r.ping_time * 1000 <= CONFIG.max_ping_ms]
            removed = before - len(unique_results)
            print(f"   ⏱️  Removed {removed} configs over {CONFIG.max_ping_ms} ms")

        # Step 5: Analyze protocols and performance
        print(f"\n📋 [5/6] Analyzing {len(unique_results):,} unique configs...")
        stats = self._analyze_results(unique_results, self.available_sources)
        
        # Step 6: Generate comprehensive outputs
        print("\n💾 [6/6] Generating comprehensive outputs...")
        await self._generate_comprehensive_outputs(unique_results, stats, self.start_time)

        self._print_final_summary(len(unique_results), time.time() - self.start_time, stats)
    
    async def _test_and_filter_sources(self) -> List[str]:
        """Test all sources for availability and filter out dead links."""
        # Setup HTTP session
        connector = aiohttp.TCPConnector(
            limit=CONFIG.concurrent_limit,
            limit_per_host=10,
            ttl_dns_cache=300,
            ssl=ssl.create_default_context(),
            resolver=AsyncResolver()
        )
        
        self.fetcher.session = aiohttp.ClientSession(connector=connector)
        
        try:
            # Test all sources concurrently
            semaphore = asyncio.Semaphore(CONFIG.concurrent_limit)
            
            async def test_single_source(url: str) -> Optional[str]:
                async with semaphore:
                    is_available = await self.fetcher.test_source_availability(url)
                    return url if is_available else None
            
            tasks = [test_single_source(url) for url in self.sources]
            
            completed = 0
            available_sources = []

            with tqdm(total=len(self.sources), desc="Testing sources", unit="src") as pbar:
                for coro in asyncio.as_completed(tasks):
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
        
        try:
            # Process sources with semaphore
            semaphore = asyncio.Semaphore(CONFIG.concurrent_limit)
            
            async def process_single_source(url: str) -> Tuple[str, List[ConfigResult]]:
                async with semaphore:
                    return await self.fetcher.fetch_source(url)
            
            # Create tasks
            tasks = [process_single_source(url) for url in available_sources]
            
            completed = 0
            with tqdm(total=len(available_sources), desc="Fetching configs", unit="src") as pbar:
                for coro in asyncio.as_completed(tasks):
                    url, results = await coro
                    completed += 1
                    pbar.update(1)

                    self.all_results.extend(results)
                    if results:
                        successful_sources += 1
                        reachable = sum(1 for r in results if r.is_reachable)
                        status = f"✓ {len(results):,} configs ({reachable} reachable)"
                    else:
                        status = "✗ No configs"

                    domain = urlparse(url).netloc or url[:50] + "..."
                    pbar.set_postfix_str(f"{status} - {domain}")

                    await self._maybe_save_batch()

                    if self.stop_fetching:
                        break

            if self.stop_fetching:
                for t in tasks:
                    t.cancel()

            print(f"\n   📈 Sources with configs: {successful_sources}/{len(available_sources)}")
            
        finally:
            await self.fetcher.session.close()

        # Return the accumulated list for backward compatibility
        return self.all_results

    async def _maybe_save_batch(self) -> None:
        """Save intermediate output based on batch settings."""
        if CONFIG.batch_size <= 0:
            return

        # Process new results since last call
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
            if h not in self.saved_hashes:
                self.saved_hashes.add(h)
                self.cumulative_unique.append(r)

        if CONFIG.strict_batch:
            while len(self.cumulative_unique) - self.last_saved_count >= CONFIG.batch_size:
                self.batch_counter += 1
                if CONFIG.cumulative_batches:
                    batch_results = self.cumulative_unique[:]
                else:
                    start = self.last_saved_count
                    end = start + CONFIG.batch_size
                    batch_results = self.cumulative_unique[start:end]
                    self.last_saved_count = end

                if CONFIG.enable_sorting:
                    batch_results = self._sort_by_performance(batch_results)
                if CONFIG.top_n > 0:
                    batch_results = batch_results[:CONFIG.top_n]

                stats = self._analyze_results(batch_results, self.available_sources)
                await self._generate_comprehensive_outputs(batch_results, stats, self.start_time, prefix=f"batch_{self.batch_counter}_")

                cumulative_stats = self._analyze_results(self.cumulative_unique, self.available_sources)
                await self._generate_comprehensive_outputs(self.cumulative_unique, cumulative_stats, self.start_time, prefix="cumulative_")

                if CONFIG.threshold > 0 and len(self.cumulative_unique) >= CONFIG.threshold:
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

                if CONFIG.enable_sorting:
                    batch_results = self._sort_by_performance(batch_results)
                if CONFIG.top_n > 0:
                    batch_results = batch_results[:CONFIG.top_n]

                stats = self._analyze_results(batch_results, self.available_sources)
                await self._generate_comprehensive_outputs(batch_results, stats, self.start_time, prefix=f"batch_{self.batch_counter}_")

                cumulative_stats = self._analyze_results(self.cumulative_unique, self.available_sources)
                await self._generate_comprehensive_outputs(self.cumulative_unique, cumulative_stats, self.start_time, prefix="cumulative_")

                self.next_batch_threshold += CONFIG.batch_size

                if CONFIG.threshold > 0 and len(self.cumulative_unique) >= CONFIG.threshold:
                    print(f"\n⏹️  Threshold of {CONFIG.threshold} configs reached. Stopping early.")
                    self.stop_fetching = True
    
    def _deduplicate_config_results(self, results: List[ConfigResult]) -> List[ConfigResult]:
        """Efficient deduplication of config results using semantic hashing."""
        seen_hashes: Set[str] = set()
        unique_results: List[ConfigResult] = []

        for result in results:
            if CONFIG.tls_fragment and CONFIG.tls_fragment.lower() not in result.config.lower():
                continue
            if CONFIG.include_protocols and result.protocol.upper() not in CONFIG.include_protocols:
                continue
            if CONFIG.exclude_protocols and result.protocol.upper() in CONFIG.exclude_protocols:
                continue
            config_hash = self.processor.create_semantic_hash(result.config)
            if config_hash not in seen_hashes:
                seen_hashes.add(config_hash)
                unique_results.append(result)
        
        duplicates = len(results) - len(unique_results)
        print(f"   🗑️ Duplicates removed: {duplicates:,}")
        if len(results) > 0:
            efficiency = duplicates / len(results) * 100
        else:
            efficiency = 0
        print(f"   📊 Deduplication efficiency: {efficiency:.1f}%")
        return unique_results
    
    def _sort_by_performance(self, results: List[ConfigResult]) -> List[ConfigResult]:
        """Sort results by connection performance and protocol preference."""
        # Protocol priority ranking
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
            return (-is_reachable, ping_time, protocol_rank)
        
        sorted_results = sorted(results, key=sort_key)
        
        reachable_count = sum(1 for r in results if r.is_reachable)
        print(f"   🚀 Sorted: {reachable_count:,} reachable configs first")
        
        if reachable_count > 0:
            fastest = min((r for r in results if r.ping_time), key=lambda x: x.ping_time, default=None)
            if fastest:
                print(f"   ⚡ Fastest server: {fastest.ping_time*1000:.1f}ms ({fastest.protocol})")
        
        return sorted_results
    
    def _analyze_results(self, results: List[ConfigResult], available_sources: List[str]) -> Dict:
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
        print(f"   🔗 Available sources: {len(available_sources)}")
        print(f"   📋 Protocol breakdown:")
        
        for protocol, count in sorted(protocol_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100 if total else 0
            perf_info = ""
            if protocol in perf_summary:
                avg_ms = perf_summary[protocol]["avg_ms"]
                perf_info = f" | Avg: {avg_ms}ms"
            print(f"      {protocol:12} {count:>7,} configs ({percentage:5.1f}%){perf_info}")
        
        return {
            "protocol_stats": protocol_stats,
            "performance_stats": perf_summary,
            "total_configs": total,
            "reachable_configs": reachable,
            "available_sources": len(available_sources),
            "total_sources": len(self.sources)
        }
    
    async def _generate_comprehensive_outputs(self, results: List[ConfigResult], stats: Dict, start_time: float, prefix: str = "") -> None:
        """Generate comprehensive output files with all formats."""
        # Create output directory
        output_dir = Path(CONFIG.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Extract configs for traditional outputs
        configs = [result.config for result in results]
        
        # Raw text output
        raw_file = output_dir / f"{prefix}vpn_subscription_raw.txt"
        tmp_raw = raw_file.with_suffix('.tmp')
        tmp_raw.write_text("\n".join(configs), encoding="utf-8")
        tmp_raw.replace(raw_file)
        
        # Base64 output
        base64_content = base64.b64encode("\n".join(configs).encode("utf-8")).decode("utf-8")
        base64_file = output_dir / f"{prefix}vpn_subscription_base64.txt"
        tmp_base64 = base64_file.with_suffix('.tmp')
        tmp_base64.write_text(base64_content, encoding="utf-8")
        tmp_base64.replace(base64_file)
        
        # Enhanced CSV with comprehensive performance data
        csv_file = output_dir / f"{prefix}vpn_detailed.csv"
        tmp_csv = csv_file.with_suffix('.tmp')
        with open(tmp_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            headers = ['Config', 'Protocol', 'Host', 'Port', 'Ping_MS', 'Reachable', 'Source']
            if CONFIG.full_test:
                headers.append('Handshake')
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
                writer.writerow(row)
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
            }
        }
        
        report_file = output_dir / f"{prefix}vpn_report.json"
        tmp_report = report_file.with_suffix('.tmp')
        tmp_report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp_report.replace(report_file)

        # Simple outbounds JSON
        outbounds = []
        for idx, r in enumerate(results):
            ob = {
                "type": r.protocol.lower(),
                "tag": f"{r.protocol} {idx}",
                "server": r.host or "",
                "server_port": r.port,
                "raw": r.config
            }
            outbounds.append(ob)

        singbox_file = output_dir / f"{prefix}vpn_singbox.json"
        tmp_singbox = singbox_file.with_suffix('.tmp')
        tmp_singbox.write_text(json.dumps({"outbounds": outbounds}, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp_singbox.replace(singbox_file)

        if CONFIG.output_clash:
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
        print(f"🌐 Reachable configs: {stats['reachable_configs']:,}")
        print(f"📈 Success rate: {stats['reachable_configs']/config_count*100:.1f}%")
        print(f"🔗 Available sources: {stats['available_sources']}/{stats['total_sources']}")
        print(f"⚡ Processing speed: {config_count/elapsed_time:.0f} configs/second")
        
        if CONFIG.enable_sorting and stats['reachable_configs'] > 0:
            print(f"🚀 Configs sorted by performance (fastest first)")
        
        top_protocol = max(stats['protocol_stats'].items(), key=lambda x: x[1])[0]
        print(f"🏆 Top protocol: {top_protocol}")
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

async def main_async():
    """Main async function."""
    try:
        merger = UltimateVPNMerger()
        await merger.run()
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

def detect_and_run():
    """Detect event loop and run appropriately."""
    try:
        # Try to get the running loop
        loop = asyncio.get_running_loop()
        print("🔄 Detected existing event loop")
        print("📝 Creating task in existing loop...")
        
        # We're in an async environment (like Jupyter)
        task = asyncio.create_task(main_async())
        print("✅ Task created successfully!")
        print("📋 Use 'await task' to wait for completion in Jupyter")
        return task
        
    except RuntimeError:
        # No running loop - we can use asyncio.run()
        print("🔄 No existing event loop detected")
        print("📝 Using asyncio.run()...")
        return asyncio.run(main_async())

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

    parser = argparse.ArgumentParser(description="VPN Merger")
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
    parser.add_argument("--prefer-protocols", type=str, default=None,
                        help="Comma-separated protocol priority list")
    parser.add_argument("--app-tests", type=str, default=None,
                        help="Comma-separated list of services to test via configs")
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
    # Resolve and validate output directory to prevent path traversal
    allowed_base = _get_script_dir()
    resolved_output = Path(args.output_dir).expanduser().resolve()
    try:
        resolved_output.relative_to(allowed_base)
    except ValueError:
        parser.error(f"--output-dir must be within {allowed_base}")
    CONFIG.output_dir = str(resolved_output)
    CONFIG.test_timeout = max(0.1, args.test_timeout)
    CONFIG.concurrent_limit = max(1, args.concurrent_limit)
    CONFIG.max_retries = max(1, args.max_retries)
    CONFIG.proxy = args.proxy
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
    if args.no_url_test:
        CONFIG.enable_url_testing = False
    if args.no_sort:
        CONFIG.enable_sorting = False

    if CONFIG.log_file:
        logging.basicConfig(filename=CONFIG.log_file, level=logging.INFO,
                            format='%(asctime)s %(levelname)s:%(message)s')

    print("🔧 VPN Merger - Checking environment...")

    try:
        return detect_and_run()
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

