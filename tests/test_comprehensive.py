import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_full_processing_pipeline(tmp_path: Path):
    # Mock two sources
    mock_sources = [
        "https://example.com/source1.txt",
        "https://example.com/source2.txt",
    ]

    # Mock response payload
    mock_configs = [
        "vmess://eyJhZGQiOiAiZXhhbXBsZS5jb20iLCAicG9ydCI6IDQ0M30=",
        "vless://uuid@example.com:443?security=tls",
        "trojan://password@example.com:443",
    ]
    payload = ("\n".join(mock_configs)).encode("utf-8")

    # Build a mock response that looks like aiohttp response
    class _CtxResp:
        def __init__(self):
            self.status = 200
            self.headers = {}

        async def read(self):
            return payload

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    def _get(*args, **kwargs):
        return _CtxResp()

    with patch("aiohttp.ClientSession.get", new=_get):
        # Import root module explicitly (avoid package name clash)
        import importlib.util, sys
        root = Path(__file__).resolve().parents[1] / "vpn_merger.py"
        spec = importlib.util.spec_from_file_location("vpn_merger_app", str(root))
        vm = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(vm)

        vm.CONFIG.output_dir = str(tmp_path)

        merger = vm.UltimateVPNMerger()
        merger.sources = mock_sources
        await merger.run()

        # Verify outputs exist
        assert (tmp_path / "vpn_subscription_raw.txt").exists()
        assert (tmp_path / "vpn_subscription_base64.txt").exists()
        assert (tmp_path / "vpn_detailed.csv").exists()
        assert (tmp_path / "vpn_singbox.json").exists()

        raw_content = (tmp_path / "vpn_subscription_raw.txt").read_text(encoding="utf-8")
        assert "vmess://" in raw_content
        assert "vless://" in raw_content
        assert "trojan://" in raw_content
