import asyncio
import pytest

from streamline_vpn import scheduler as scheduler_mod


def test_setup_scheduler_creates_job():
    sched = scheduler_mod.setup_scheduler()
    assert sched is not None
    jobs = [j for j in sched.get_jobs() if j.id == "process_sources"]
    assert len(jobs) == 1


@pytest.mark.asyncio
async def test_run_processing_invokes_merger(monkeypatch):
    calls = {"initialized": False, "processed": False}

    class FakeMerger:
        async def initialize(self):
            calls["initialized"] = True

        async def process_all(self):
            calls["processed"] = True
            return {"success": True}

    # Patch the scheduler module's reference
    monkeypatch.setattr(scheduler_mod, "StreamlineVPNMerger", FakeMerger)
    await scheduler_mod.run_processing()
    assert calls["initialized"] and calls["processed"]


@pytest.mark.asyncio
async def test_start_scheduler_runs_when_loop_present():
    # Ensure scheduler is created
    scheduler_mod.setup_scheduler()
    # Should not raise on event loop presence
    sched = scheduler_mod.start_scheduler()
    assert sched is not None


def test_start_scheduler_when_no_event_loop():
    # Calling outside of an event loop should hit the warning path
    sched = scheduler_mod.start_scheduler()
    assert sched is not None


@pytest.mark.asyncio
async def test_run_processing_handles_exception(monkeypatch):
    class FailMerger:
        async def initialize(self):
            pass
        async def process_all(self):
            raise RuntimeError("failure")

    monkeypatch.setattr(scheduler_mod, "StreamlineVPNMerger", FailMerger)
    # Should not raise
    await scheduler_mod.run_processing()
