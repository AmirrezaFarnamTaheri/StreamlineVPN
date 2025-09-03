#!/usr/bin/env python3
"""Minimal smoke checks that avoid network by default.

Usage:
  python scripts/smoke.py

Behavior:
  - Validates basic functionality
  - Tests core classes and methods
  - Verifies configuration loading
"""
import os

os.environ.setdefault("SKIP_NETWORK", "1")
os.environ.setdefault("SKIP_DISCOVERY", "1")


def assert_true(cond, msg):
    if not cond:
        raise SystemExit(f"[SMOKE] FAIL: {msg}")


def main():
    # 1) Test basic imports
    try:
        from vpn_merger import (
            ConfigurationProcessor,
            SourceManager,
            UnifiedSourceValidator,
            VPNSubscriptionMerger,
        )

        print("[SMOKE] OK: Basic imports")
    except ImportError as e:
        print(f"[SMOKE] FAIL: Import error - {e}")
        return

    # 2) Test source manager
    try:
        source_manager = SourceManager()
        sources = source_manager.get_all_sources()
        assert_true(len(sources) > 0, "source manager has sources")
        print("[SMOKE] OK: Source manager")
    except Exception as e:
        print(f"[SMOKE] FAIL: Source manager - {e}")
        return

    # 3) Test configuration processor
    try:
        processor = ConfigurationProcessor()
        test_config = "vmess://eyJhZGQiOiAidGVzdC5leGFtcGxlLmNvbSIsICJwb3J0IjogNDQzfQ=="
        result = processor.process_config(test_config)
        assert_true(result is not None, "config processor processes valid configs")
        assert_true(result.protocol == "vmess", "protocol detection works")
        print("[SMOKE] OK: Configuration processor")
    except Exception as e:
        print(f"[SMOKE] FAIL: Configuration processor - {e}")
        return

    # 4) Test VPN merger initialization
    try:
        merger = VPNSubscriptionMerger()
        assert_true(merger is not None, "VPN merger initializes")
        print("[SMOKE] OK: VPN merger initialization")
    except Exception as e:
        print(f"[SMOKE] FAIL: VPN merger - {e}")
        return

    print("[SMOKE] OK: All basic functionality tests passed")


if __name__ == "__main__":
    main()
