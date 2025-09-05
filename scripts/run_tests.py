#!/usr/bin/env python3
"""
Test Runner for StreamlineVPN
"""

import os
import sys
import subprocess
import argparse


def main() -> int:
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="StreamlineVPN Test Runner")
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="Skip tests that require network access.",
    )
    args = parser.parse_args()

    env = os.environ.copy()
    if args.no_network:
        env["SKIP_NETWORK"] = "true"

    cmd = [sys.executable, "-m", "pytest", "-q"]
    try:
        return subprocess.call(cmd, env=env)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
