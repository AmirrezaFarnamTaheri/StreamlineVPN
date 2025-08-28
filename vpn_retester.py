#!/usr/bin/env python3
"""Retest and sort an existing VPN subscription output."""

import asyncio
import argparse
import base64
import csv
from pathlib import Path
from typing import List, Tuple, Optional

from vpn_merger import EnhancedConfigProcessor, CONFIG


async def _test_config(proc: EnhancedConfigProcessor, cfg: str) -> Tuple[str, Optional[float], Optional[bool]]:
    host, port = proc.extract_host_port(cfg)
    proto = proc.categorize_protocol(cfg)
    if host and port:
        ping, hs = await proc.test_connection(host, port, proto)
    else:
        ping, hs = None, None
    return cfg, ping, hs


async def retest_configs(configs: List[str]) -> List[Tuple[str, Optional[float], Optional[bool]]]:
    proc = EnhancedConfigProcessor()
    semaphore = asyncio.Semaphore(CONFIG.concurrent_limit)

    async def worker(cfg: str) -> Tuple[str, Optional[float], Optional[bool]]:
        async with semaphore:
            return await _test_config(proc, cfg)

    tasks = [asyncio.create_task(worker(c)) for c in configs]
    return await asyncio.gather(*tasks)


def load_configs(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8").strip()
    if text and '://' not in text.splitlines()[0]:
        try:
            text = base64.b64decode(text).decode("utf-8")
        except Exception as e:
            raise ValueError("Failed to decode base64 input") from e
    return [l.strip() for l in text.splitlines() if l.strip()]


def filter_configs(configs: List[str]) -> List[str]:
    """Filter configs based on include/exclude protocol settings."""
    if CONFIG.include_protocols is None and CONFIG.exclude_protocols is None:
        return configs

    proc = EnhancedConfigProcessor()
    filtered = []
    for cfg in configs:
        proto = proc.categorize_protocol(cfg).upper()
        if CONFIG.include_protocols and proto not in CONFIG.include_protocols:
            continue
        if CONFIG.exclude_protocols and proto in CONFIG.exclude_protocols:
            continue
        filtered.append(cfg)
    return filtered


def save_results(results: List[Tuple[str, Optional[float], Optional[bool]]], sort: bool, top_n: int) -> None:
    output_dir = Path(CONFIG.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if sort:
        results.sort(key=lambda x: (x[1] is None, x[1] if x[1] is not None else float('inf')))

    if top_n > 0:
        results = results[:top_n]

    configs = [c for c, _, _ in results]
    raw_path = output_dir / "vpn_retested_raw.txt"
    raw_path.write_text("\n".join(configs), encoding="utf-8")

    if CONFIG.write_base64:
        base64_path = output_dir / "vpn_retested_base64.txt"
        base64_path.write_text(base64.b64encode("\n".join(configs).encode()).decode(), encoding="utf-8")

    if CONFIG.write_csv:
        csv_path = output_dir / "vpn_retested_detailed.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            headers = ["Config", "Ping_MS"]
            if CONFIG.full_test:
                headers.append("Handshake")
            writer.writerow(headers)
            for cfg, ping, hs in results:
                row = [cfg, round(ping * 1000, 2) if ping is not None else ""]
                if CONFIG.full_test:
                    if hs is None:
                        row.append("")
                    else:
                        row.append("OK" if hs else "FAIL")
                writer.writerow(row)

    print(f"\n✔ Retested files saved in {output_dir}/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Retest and sort an existing VPN subscription list")
    parser.add_argument("input", help="Path to existing raw or base64 subscription file")
    parser.add_argument("--top-n", type=int, default=0, help="Keep only the N fastest configs")
    parser.add_argument("--no-sort", action="store_true", help="Skip sorting by latency")
    parser.add_argument("--concurrent-limit", type=int, default=CONFIG.concurrent_limit,
                        help="Number of concurrent tests")
    parser.add_argument("--test-timeout", type=float, default=CONFIG.test_timeout,
                        help="TCP connection timeout in seconds")
    parser.add_argument("--max-ping", type=int, default=0,
                        help="Discard configs slower than this ping in ms (0 disables)")
    parser.add_argument("--include-protocols", type=str, default=None,
                        help="Comma-separated protocols to include")
    parser.add_argument("--exclude-protocols", type=str, default=None,
                        help="Comma-separated protocols to exclude")
    parser.add_argument("--output-dir", type=str, default=CONFIG.output_dir,
                        help="Directory to save output files")
    parser.add_argument("--no-base64", action="store_true", help="Do not save base64 file")
    parser.add_argument("--no-csv", action="store_true", help="Do not save CSV report")
    parser.add_argument("--full-test", action="store_true", help="Perform full TLS handshake when applicable")
    args = parser.parse_args()

    CONFIG.concurrent_limit = max(1, args.concurrent_limit)
    CONFIG.test_timeout = max(0.1, args.test_timeout)
    CONFIG.max_ping_ms = args.max_ping if args.max_ping > 0 else None
    if args.include_protocols:
        CONFIG.include_protocols = {p.strip().upper() for p in args.include_protocols.split(',') if p.strip()}
    if args.exclude_protocols:
        CONFIG.exclude_protocols = {p.strip().upper() for p in args.exclude_protocols.split(',') if p.strip()}
    CONFIG.output_dir = str(Path(args.output_dir).expanduser())
    CONFIG.write_base64 = not args.no_base64
    CONFIG.write_csv = not args.no_csv
    CONFIG.full_test = args.full_test

    configs = load_configs(Path(args.input))
    configs = filter_configs(configs)
    results = asyncio.run(retest_configs(configs))
    if CONFIG.max_ping_ms is not None:
        results = [(c, p, hs) for c, p, hs in results if p is not None and p * 1000 <= CONFIG.max_ping_ms]
    save_results(results, not args.no_sort, args.top_n)


if __name__ == "__main__":
    main()
