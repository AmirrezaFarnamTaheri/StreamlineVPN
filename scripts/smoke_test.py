#!/usr/bin/env python3
"""
StreamlineVPN Unified API Smoke Test
====================================

Verifies core endpoints of the unified API. Can either:
- Test an already running server via --url
- Start a temporary server (uvicorn) via --start

Examples:
  python scripts/smoke_test.py --start --cache --port 8082
  python scripts/smoke_test.py --url http://127.0.0.1:8080
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from typing import Dict, Tuple

import httpx


def wait_for_health(base_url: str, timeout: float = 20.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            r = httpx.get(f"{base_url}/health", timeout=2.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.25)
    return False


def check_endpoint(method: str, url: str, expect_ok: bool = True, **kwargs) -> Tuple[bool, str]:
    try:
        r = httpx.request(method.upper(), url, timeout=5.0, **kwargs)
        ok = (r.status_code == 200) if expect_ok else True
        return ok, f"{r.status_code} {r.text[:200]}"
    except Exception as e:
        return False, f"ERR: {e}"


def run_checks(base_url: str) -> Dict[str, Dict[str, str]]:
    results: Dict[str, Dict[str, str]] = {}

    def record(name: str, ok: bool, info: str) -> None:
        results[name] = {"ok": str(ok), "info": info}

    # Core API
    ok, info = check_endpoint("GET", f"{base_url}/health")
    record("health", ok, info)

    ok, info = check_endpoint("GET", f"{base_url}/api/v1/cache/health")
    record("cache_health", ok, info)

    ok, info = check_endpoint("POST", f"{base_url}/api/v1/cache/clear")
    record("cache_clear", ok, info)

    ok, info = check_endpoint("GET", f"{base_url}/api/v1/statistics")
    record("statistics", ok, info)

    ok, info = check_endpoint("GET", f"{base_url}/api/v1/sources")
    record("sources", ok, info)

    ok, info = check_endpoint("POST", f"{base_url}/api/v1/sources/validate")
    record("sources_validate", ok, info)

    # Static assets/UI
    ok, info = check_endpoint("GET", f"{base_url}/api-base.js")
    record("api_base_js", ok, info)

    ok, info = check_endpoint("GET", f"{base_url}/interactive.html")
    record("interactive_html", ok, info)

    return results


def start_server(port: int, cache: bool) -> subprocess.Popen:
    env = os.environ.copy()
    if cache:
        env["CACHE_ENABLED"] = "1"
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "streamline_vpn.web.unified_api:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    return subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main() -> int:
    parser = argparse.ArgumentParser(description="StreamlineVPN Unified API smoke test")
    parser.add_argument("--url", default=None, help="Base URL (e.g., http://127.0.0.1:8080)")
    parser.add_argument("--start", action="store_true", help="Start a temporary server")
    parser.add_argument("--port", type=int, default=8082, help="Port to use when starting a server")
    parser.add_argument("--cache", action="store_true", help="Enable cache when starting a server")
    parser.add_argument("--timeout", type=float, default=20.0, help="Health wait timeout (seconds)")
    args = parser.parse_args()

    proc: subprocess.Popen | None = None
    base_url = args.url or f"http://127.0.0.1:{args.port}"

    try:
        if args.start:
            proc = start_server(args.port, args.cache)
            if not wait_for_health(base_url, timeout=args.timeout):
                print(json.dumps({"error": "server did not become healthy", "url": base_url}))
                return 2

        results = run_checks(base_url)
        print(json.dumps({"base_url": base_url, "results": results}, indent=2))

        # Determine overall success
        all_ok = all(v.get("ok") == "True" for v in results.values())
        return 0 if all_ok else 1

    finally:
        if proc is not None:
            try:
                if os.name == "nt":
                    proc.send_signal(signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except Exception:
                    proc.kill()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())

