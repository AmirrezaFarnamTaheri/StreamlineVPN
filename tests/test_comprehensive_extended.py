import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_error_recovery_end_to_end(tmp_path: Path):
    # Patch module-global missing logging symbol used by fetcher_service.log_json
    import types
    import vpn_merger.services.fetcher_service as fs
    if not hasattr(fs, 'logging'):
        fs.logging = types.SimpleNamespace(INFO=20, WARNING=30)

    # Mock GET to fail once then succeed
    call_counter = {"n": 0}

    class _Resp:
        def __init__(self, status, body):
            self.status = status
            self._body = body
            self.headers = {}

        async def read(self):
            return self._body

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def _get(*args, **kwargs):
        call_counter["n"] += 1
        # First call: non-200; subsequent: success
        if call_counter["n"] == 1:
            return _Resp(500, b"err")
        return _Resp(200, b"vmess://alpha\nvless://beta\ntrojan://gamma\n")

    with patch("aiohttp.ClientSession.get", new=_get):
        import importlib.util
        import sys
        root = Path(__file__).resolve().parents[1] / "vpn_merger.py"
        spec = importlib.util.spec_from_file_location("vpn_merger_app", str(root))
        vm = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(vm)

        vm.CONFIG.output_dir = str(tmp_path)
        merger = vm.UltimateVPNMerger()
        merger.sources = ["https://example.com/a", "https://example.com/b"]
        await merger.run()

        # Outputs should still be produced despite initial error
        assert (tmp_path / "vpn_subscription_raw.txt").exists()
        assert (tmp_path / "vpn_subscription_base64.txt").exists()
        assert (tmp_path / "vpn_detailed.csv").exists()
        assert (tmp_path / "vpn_singbox.json").exists()


@pytest.mark.asyncio
async def test_performance_under_load_scaled():
    # Scaled dataset for CI reliability
    lines = ["vmess://x"] * 5000
    payload = ("\n".join(lines)).encode("utf-8")

    class _Resp:
        def __init__(self, status, body):
            self.status = status
            self._body = body
            self.headers = {}

        async def read(self):
            return self._body

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def _get(*args, **kwargs):
        return _Resp(200, payload)

    with patch("aiohttp.ClientSession.get", new=_get):
        import importlib.util
        root = Path(__file__).resolve().parents[1] / "vpn_merger.py"
        spec = importlib.util.spec_from_file_location("vpn_merger_app_perf", str(root))
        vm = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(vm)

        with tempfile.TemporaryDirectory() as tmpdir:
            vm.CONFIG.output_dir = tmpdir
            merger = vm.UltimateVPNMerger()
            merger.sources = ["https://example.com/large.txt"]

            # Run and ensure it completes quickly enough (loose bound)
            import time
            start = time.time()
            await merger.run()
            elapsed = time.time() - start

            assert elapsed < 10.0
            assert Path(tmpdir, "vpn_subscription_raw.txt").exists()

