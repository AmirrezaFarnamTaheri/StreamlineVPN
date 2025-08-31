from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_error_recovery_network_and_write_failures(tmp_path: Path):
    calls: dict[str, int] = {"ok": 0, "fail": 0}

    class _CtxResp:
        def __init__(self, status: int, body: bytes = b""):
            self.status = status
            self._body = body
            self.headers = {}

        async def read(self):
            return self._body

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    def _get(url: str, *args, **kwargs):
        if "source-ok" in url:
            calls["ok"] += 1
            payload = b"vmess://dGVzdA==\nvless://12345678-90ab-12f3-a6c5-4681aaaaaaaa@test.example.com:443?security=tls\n"
            return _CtxResp(200, payload)
        calls["fail"] += 1
        raise RuntimeError("simulated network error")

    # Simulate a write failure for the first attempt, then succeed
    wrote_once = {"fail": False}

    def flaky_write_text(self, data: str, encoding: str = "utf-8"):
        if not wrote_once["fail"]:
            wrote_once["fail"] = True
            raise OSError("simulated disk full")
        # Retry path: actually write
        Path(self).write_bytes(data.encode(encoding))

    with patch("aiohttp.ClientSession.get", new=_get), \
         patch("pathlib.Path.write_text", new=flaky_write_text):
        import importlib.util
        root = Path(__file__).resolve().parents[1] / "vpn_merger.py"
        spec = importlib.util.spec_from_file_location("vpn_merger_app", str(root))
        vm = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(vm)

        vm.CONFIG.output_dir = str(tmp_path)
        merger = vm.UltimateVPNMerger()
        merger.sources = [
                    "https://raw.githubusercontent.com/test/source-fail-1.txt",
        "https://raw.githubusercontent.com/test/source-ok.txt",
        "https://raw.githubusercontent.com/test/source-fail-2.txt",
        ]

        # Should not raise despite failures
        await merger.run()

    # Verify outputs exist and contain at least the successful configs
    assert (tmp_path / "vpn_subscription_raw.txt").exists()
    raw = (tmp_path / "vpn_subscription_raw.txt").read_text(encoding="utf-8")
    assert "vmess://" in raw or "vless://" in raw
    # Ensure both success and failures were exercised
    assert calls["ok"] >= 1 and calls["fail"] >= 1


@pytest.mark.asyncio
async def test_performance_under_load_quick(tmp_path: Path):
    # Generate a reasonably large synthetic payload (50k lines) but fast to handle
    N = 50_000
    lines = []
    for i in range(N):
        if i % 3 == 0:
            lines.append("vmess://dGVzdA==")
        elif i % 3 == 1:
            lines.append("vless://12345678-90ab-12f3-a6c5-4681aaaaaaaa@test.example.com:443?security=tls")
        else:
            lines.append("trojan://testpassword@test.example.com:443")
    blob = ("\n".join(lines)).encode("utf-8")

    class _CtxResp:
        def __init__(self, body: bytes):
            self.status = 200
            self.headers = {}
            self._body = body

        async def read(self):
            return self._body

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    def _get(*args, **kwargs):
        return _CtxResp(blob)

    with patch("aiohttp.ClientSession.get", new=_get):
        import importlib.util
        root = Path(__file__).resolve().parents[1] / "vpn_merger.py"
        spec = importlib.util.spec_from_file_location("vpn_merger_app", str(root))
        vm = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(vm)

        vm.CONFIG.output_dir = str(tmp_path)
        merger = vm.UltimateVPNMerger()
        merger.sources = ["https://raw.githubusercontent.com/test/big.txt"]

        # Limit runtime by reducing internal testing and scoring work if supported
        if hasattr(merger, "max_tested_configs"):
            merger.max_tested_configs = 0

        await merger.run()

    # Validate outputs were created
    assert (tmp_path / "vpn_subscription_raw.txt").exists()
    raw = (tmp_path / "vpn_subscription_raw.txt").read_text(encoding="utf-8")
    # Spot-check sample presence
    assert "vmess://" in raw and "vless://" in raw and "trojan://" in raw


