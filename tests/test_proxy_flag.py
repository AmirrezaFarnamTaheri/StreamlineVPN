import sys
import types
import asyncio
import importlib


def test_proxy_updates_config(monkeypatch):
    stub = types.ModuleType("vpn_merger")
    stub.CONFIG = types.SimpleNamespace(proxy=None)
    monkeypatch.setitem(sys.modules, "vpn_merger", stub)

    import advanced_methods.argo_merger as argo
    
    async def dummy_async(*args, **kwargs):
        return None
    monkeypatch.setattr(argo, "main_async", dummy_async)
    monkeypatch.setattr(asyncio, "run", lambda coro: asyncio.get_event_loop().run_until_complete(coro))

    monkeypatch.setattr(sys, "argv", ["argo_merger.py", "--proxy", "http://proxy"])
    argo.main()
    assert stub.CONFIG.proxy == "http://proxy"
