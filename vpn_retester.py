#!/usr/bin/env python3
"""Retest and sort an existing VPN subscription output."""

import asyncio
import argparse
import base64
import csv
from pathlib import Path
from typing import List, Tuple, Optional

from vpn_merger import EnhancedConfigProcessor, CONFIG


async def _test_config(proc: EnhancedConfigProcessor, cfg: str) -> Tuple[str, Optional[float]]:
    host, port = proc.extract_host_port(cfg)
    if host and port:
        ping = await proc.test_connection(host, port)
    else:
        ping = None
    return cfg, ping


async def retest_configs(configs: List[str]) -> List[Tuple[str, Optional[float]]]:
    proc = EnhancedConfigProcessor()
    semaphore = asyncio.Semaphore(CONFIG.concurrent_limit)

    async def worker(cfg: str) -> Tuple[str, Optional[float]]:
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


def save_results(results: List[Tuple[str, Optional[float]]], sort: bool, top_n: int) -> None:
    output_dir = Path(CONFIG.output_dir)
    output_dir.mkdir(exist_ok=True)

    if sort:
        results.sort(key=lambda x: (x[1] is None, x[1] if x[1] is not None else float('inf')))

    if top_n > 0:
        results = results[:top_n]

    configs = [c for c, _ in results]
    raw_path = output_dir / "vpn_retested_raw.txt"
    raw_path.write_text("\n".join(configs), encoding="utf-8")

    base64_path = output_dir / "vpn_retested_base64.txt"
    base64_path.write_text(base64.b64encode("\n".join(configs).encode()).decode(), encoding="utf-8")

    csv_path = output_dir / "vpn_retested_detailed.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Config", "Ping_MS"])
        for cfg, ping in results:
            writer.writerow([cfg, round(ping * 1000, 2) if ping is not None else ""])

    print(f"\n✔ Retested files saved in {output_dir}/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Retest and sort an existing VPN subscription list")
    parser.add_argument("input", help="Path to existing raw or base64 subscription file")
    parser.add_argument("--top-n", type=int, default=0, help="Keep only the N fastest configs")
    parser.add_argument("--no-sort", action="store_true", help="Skip sorting by latency")
    args = parser.parse_args()

    configs = load_configs(Path(args.input))
    results = asyncio.run(retest_configs(configs))
    save_results(results, not args.no_sort, args.top_n)


if __name__ == "__main__":
    main()
