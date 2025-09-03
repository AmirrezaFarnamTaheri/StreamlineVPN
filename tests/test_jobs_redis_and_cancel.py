import asyncio
import os

import pytest


def _has_redis():
    return bool(os.getenv("REDIS_URL"))


@pytest.mark.asyncio
@pytest.mark.skipif(not _has_redis(), reason="REDIS_URL not set for Redis-backed test")
async def test_jobmanager_redis_persistence_and_cancel(monkeypatch):
    # Force TTL long to avoid interference
    monkeypatch.setenv("JOBS_TTL_DAYS", "365")
    monkeypatch.setenv("JOBS_CLEANUP_INTERVAL_SEC", "600")

    # Recreate manager after env set
    from importlib import reload

    from vpn_merger.web.graphql import jobs as jobs_mod

    reload(jobs_mod)
    manager = jobs_mod.JobManager()

    # Ensure Redis is available
    assert manager._redis is not None

    # Create a job with multiple sources to allow cancellation mid-run
    job = manager.create_job(
        [
            "http://example.local/a.txt",
            "http://example.local/b.txt",
            "http://example.local/c.txt",
        ]
    )

    # Wait a moment, then cancel
    await asyncio.sleep(0.05)
    cancelled = manager.cancel(job.id)
    assert cancelled is True

    # Allow runner to observe cancel
    await asyncio.sleep(0.1)
    state = manager.get(job.id)
    assert state is not None
    assert state.status in ("cancelled", "completed")

    # Delete job and ensure Redis key gone
    deleted = manager.delete(job.id)
    assert deleted is True

    if manager._redis is not None:
        assert manager._redis.get(f"job:{job.id}") is None


@pytest.mark.asyncio
async def test_cleanup_loop_manual_trigger(monkeypatch):
    # Use JSON fallback; reuse existing test to ensure cleanup_now works without Redis
    from importlib import reload

    from vpn_merger.web.graphql import jobs as jobs_mod

    reload(jobs_mod)
    mgr = jobs_mod.JobManager()
    j = mgr.create_job(["http://example.local/x.txt"])
    await asyncio.sleep(0.2)
    # set finished long ago
    jj = mgr.get(j.id)
    assert jj is not None
    jj.finished_at = 0.0
    jj.status = "completed"
    removed = mgr.cleanup_now()
    assert removed >= 1
