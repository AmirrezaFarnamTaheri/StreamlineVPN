#!/usr/bin/env python3
"""
Quick smoke test for StreamlineVPN services.

Pings Unified API endpoints and Static Web UI assets to verify that
servers are reachable and essential pages/assets load correctly.

Usage:
  python scripts/smoke_check.py --api http://127.0.0.1:8080 --web http://127.0.0.1:8000

Environment variables (fallbacks):
  API_BASE, WEB_BASE
Defaults:
  API: http://127.0.0.1:8080
  WEB: http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import httpx


def make_client(timeout: float = 6.0) -> httpx.Client:
    return httpx.Client(timeout=timeout, follow_redirects=True)


def check_json(client: httpx.Client, url: str, required_keys: Optional[List[str]] = None) -> Tuple[bool, str]:
    try:
        r = client.get(url)
        if r.status_code != 200:
            return False, f"{url} -> HTTP {r.status_code}"
        try:
            data = r.json()
        except Exception as exc:
            return False, f"{url} -> invalid JSON: {exc}"
        if required_keys:
            missing = [k for k in required_keys if k not in data]
            if missing:
                return False, f"{url} -> missing keys: {', '.join(missing)}"
        return True, f"{url} -> OK"
    except Exception as exc:
        return False, f"{url} -> ERROR: {exc}"


def check_text_contains(client: httpx.Client, url: str, needles: List[str]) -> Tuple[bool, str]:
    try:
        r = client.get(url)
        if r.status_code != 200:
            return False, f"{url} -> HTTP {r.status_code}"
        text = r.text
        missing = [n for n in needles if n not in text]
        if missing:
            return False, f"{url} -> missing text: {', '.join(missing)}"
        return True, f"{url} -> OK"
    except Exception as exc:
        return False, f"{url} -> ERROR: {exc}"


def run_smoke(api: str, web: str) -> int:
    failures: List[str] = []
    print(f"\n== Smoke Check ==\nAPI: {api}\nWEB: {web}\n")

    with make_client() as client:
        # Unified API
        api_checks = [
            (check_json, f"{api}/health", ["status", "version"]),
            (check_json, f"{api}/api/v1/statistics", None),
            (check_json, f"{api}/api/v1/configurations?limit=1", ["configurations"]),
            (check_json, f"{api}/api/v1/sources", ["sources"]),
        ]
        for func, url, keys in api_checks:
            ok, msg = func(client, url, keys)  # type: ignore[arg-type]
            print(("[OK]  " if ok else "[FAIL]") + " " + msg)
            if not ok:
                failures.append(msg)

        # Static Web UI basic pages
        web_checks = [
            (check_text_contains, f"{web}/index.html", ["StreamlineVPN"]),
            (check_text_contains, f"{web}/interactive.html", ["Control Panel"]),
            (check_text_contains, f"{web}/configuration/index.html", ["Configuration"]),
            (check_text_contains, f"{web}/api-base.js", ["window.__API_BASE__"]),
            (check_text_contains, f"{web}/assets/css/style.css", [".stat-card", "bar-blue"]),
            (check_text_contains, f"{web}/assets/js/main.js", ["StreamlineVPNApp", "makeRequest"]),
            (check_text_contains, f"{web}/assets/js/app.js", ["API_BASE", "loadStatistics"]),
        ]
        for func, url, needles in web_checks:
            ok, msg = func(client, url, needles)  # type: ignore[arg-type]
            print(("[OK]  " if ok else "[FAIL]") + " " + msg)
            if not ok:
                failures.append(msg)

    print("\n== Result ==")
    if failures:
        for f in failures:
            print(" - " + f)
        print(f"\n{len(failures)} check(s) failed.")
        return 2
    print("All checks passed.")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="StreamlineVPN smoke check")
    parser.add_argument("--api", default=os.getenv("API_BASE", "http://127.0.0.1:8080"), help="Unified API base URL")
    parser.add_argument("--web", default=os.getenv("WEB_BASE", "http://127.0.0.1:8000"), help="Static Web base URL")
    args = parser.parse_args(argv)
    return run_smoke(args.api.rstrip("/"), args.web.rstrip("/"))


if __name__ == "__main__":
    sys.exit(main())

