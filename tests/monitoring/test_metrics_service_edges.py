import sys
from pathlib import Path
from types import SimpleNamespace
import asyncio

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from streamline_vpn.monitoring.metrics_service import MetricsService


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        import inspect
        if inspect.isawaitable(coro):
            return loop.run_until_complete(coro)
        return coro
    except RuntimeError:
        import inspect
        if inspect.isawaitable(coro):
            return asyncio.run(coro)
        return coro


def test_metrics_service_start_stop_and_export():
    svc = MetricsService()
    # Async stubs to satisfy awaited calls inside collect_and_export
    async def _acollect():
        return True

    async def _aexport(metrics=None):
        return True

    svc.collector = SimpleNamespace(
        is_collecting=False,
        collection_interval=1,
        collect_metrics=_acollect,
        set_collection_interval=lambda s: None,
        get_all_metrics=lambda: {},
        get_metrics_summary=lambda: {},
    )
    svc.exporter = SimpleNamespace(
        is_running=False,
        is_exporting=False,
        export_metrics=_aexport,
        is_valid_format=lambda f: True,
        is_valid_destination=lambda d: True,
        configure_export_format=lambda f: None,
        configure_export_destination=lambda d: None,
    )

    _run(svc.initialize())
    _run(svc.start_service())
    _run(svc.collect_and_export())
    _run(svc.stop_service())

    assert hasattr(svc, "is_running")
    assert svc.collector is not None and svc.exporter is not None


