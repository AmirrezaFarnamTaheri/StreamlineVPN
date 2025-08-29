from __future__ import annotations

import argparse
from pathlib import Path

from .validators import positive_int


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vpn-merger", description="VPN Config Merger")
    sub = p.add_subparsers(dest="command")

    m = sub.add_parser("merge", help="Run merge and write outputs")
    m.add_argument("--output-dir", type=Path, default=Path("output"), help="Output directory")
    m.add_argument("--min-score", type=float, default=0.5, help="Discovery min reliability score")
    m.add_argument("--limit", type=positive_int, default=0, help="Process only top N sources (0=all)")
    m.add_argument(
        "--formats",
        nargs="+",
        choices=["raw", "base64", "csv", "singbox", "clash"],
        default=None,
        help="Restrict outputs to selected formats (default: all)",
    )

    d = sub.add_parser("discover", help="Discover sources and print or save")
    d.add_argument("--limit", type=positive_int, default=100, help="Max sources to return")
    d.add_argument("--output", type=Path, default=None, help="Optional file to write list")

    v = sub.add_parser("validate", help="Validate sources and show scores")
    v.add_argument("--file", type=Path, required=False, help="File with URLs (one per line)")
    v.add_argument("--min-score", type=float, default=0.5, help="Minimum reliability score")
    v.add_argument("urls", nargs="*", help="URLs to validate if --file not provided")

    f = sub.add_parser("format", help="Format raw configs into specific output")
    f.add_argument("--type", choices=["base64", "clash", "singbox", "csv"], required=True)
    f.add_argument("--input", type=Path, required=False, help="Input file (raw lines)")
    f.add_argument("--output", type=Path, required=False, help="Output file (default: stdout)")

    flt = sub.add_parser("filter", help="Filter configs by include/exclude protocols")
    flt.add_argument("--include", nargs="*", default=None, help="Protocols to include (e.g., vmess vless)")
    flt.add_argument("--exclude", nargs="*", default=None, help="Protocols to exclude")
    flt.add_argument("--input", type=Path, required=False, help="Input file (raw lines)")
    flt.add_argument("--output", type=Path, required=False, help="Output file (default: stdout)")

    sc = sub.add_parser("score", help="Score and output top N configs")
    sc.add_argument("--input", type=Path, required=False, help="Input file (raw lines)")
    sc.add_argument("--top", type=int, default=100, help="Top N to output")
    sc.add_argument("--output", type=Path, required=False, help="Output file (default: stdout)")

    ex = sub.add_parser("export", help="Export raw configs to multiple formats")
    ex.add_argument("--input", type=Path, required=False, help="Input file (raw lines)")
    ex.add_argument("--output-dir", type=Path, required=True, help="Directory to write outputs")
    ex.add_argument(
        "--formats",
        nargs="+",
        choices=["raw", "base64", "csv", "singbox", "clash"],
        required=True,
        help="Formats to write",
    )
    return p
