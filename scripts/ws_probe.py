#!/usr/bin/env python3
"""
WebSocket Handshake Probe Harness
=================================

Repeatedly connects to /ws and /ws/test_client (and alias) and records behavior
into a single diffable log. Useful to compare environments and headers.

Usage:
  python scripts/ws_probe.py --base ws://localhost:8080 --attempts 3 --headers none|origin|origin-host

Logs:
  logs/ws_probe.log
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path

import websockets


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


async def try_ws(url: str, headers_mode: str) -> tuple[str, str]:
    try:
        if headers_mode in {"origin", "origin-host"}:
            extra_headers = {"Origin": "http://localhost:8080"}
            if headers_mode == "origin-host":
                extra_headers["Host"] = "localhost:8080"
            ws_ctx = websockets.connect(url, extra_headers=extra_headers)
        else:
            ws_ctx = websockets.connect(url)
        async with ws_ctx as ws:
            await ws.send(json.dumps({"type": "ping"}))
            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
            return ("OK", msg)
    except Exception as e:
        return ("ERR", repr(e))


async def run(base: str, attempts: int, headers_mode: str) -> None:
    logs_dir = Path("logs"); logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "ws_probe.log"
    paths = ["/ws", "/ws?client_id=test", "/ws/test_client", "/ws/testclient", "/ws/abc"]
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"\n==== WS PROBE {now()} base={base} attempts={attempts} headers={headers_mode} ====\n")
    for i in range(attempts):
        for p in paths:
            url = base + p
            status, info = await try_ws(url, headers_mode)
            line = f"{now()} [{status}] {url} -> {info}"
            print(line)
            with log_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="ws://localhost:8080")
    ap.add_argument("--attempts", type=int, default=3)
    ap.add_argument("--headers", choices=["none", "origin", "origin-host"], default="none")
    args = ap.parse_args()
    asyncio.run(run(args.base, args.attempts, args.headers))


if __name__ == "__main__":
    main()
