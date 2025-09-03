import asyncio
import json
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_jobmanager_json_persistence_and_cleanup(tmp_path: Path, monkeypatch):
    # Arrange: force JSON storage path and short TTL
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    jobs_file = data_dir / "jobs.json"
    monkeypatch.setenv("JOBS_TTL_DAYS", "0.00001")  # very small TTL (~1s)
    monkeypatch.setenv("JOBS_CLEANUP_INTERVAL_SEC", "60")  # prevent background loop noise

    # Patch jobs module path to write into tmp data
    from vpn_merger.web.graphql import jobs as jobs_mod

    old_path = jobs_mod.Path

    class _P(old_path):
        def __new__(cls, *args, **kwargs):
            # redirect default path
            if args and args[0] == "data/jobs.json":
                return old_path(str(jobs_file))
            return old_path(*args, **kwargs)

    jobs_mod.Path = _P  # type: ignore

    try:
        # Re-import manager to pick up new path
        from importlib import reload

        reload(jobs_mod)

        manager = jobs_mod.JobManager()

        # Act: create job and complete it quickly by processing no real sources
        job = manager.create_job(["http://example.local/test.txt"])  # will run in background
        # Allow some time for job to complete
        await asyncio.sleep(0.2)

        # Assert: JSON file exists and contains job
        assert jobs_file.exists()
        payload = json.loads(jobs_file.read_text(encoding="utf-8"))
        assert "jobs" in payload and isinstance(payload["jobs"], list)
        assert any(j.get("id") == job.id for j in payload["jobs"])  # type: ignore

        # Force TTL expiration and cleanup
        # Mark job finished far in the past
        j = manager.get(job.id)
        assert j is not None
        j.finished_at = 0.0
        j.status = "completed"
        removed = manager.cleanup_now()
        assert removed >= 1

        # After cleanup, JSON should not contain the job
        payload2 = json.loads(jobs_file.read_text(encoding="utf-8"))
        assert all(entry.get("id") != job.id for entry in payload2.get("jobs", []))
    finally:
        jobs_mod.Path = old_path  # restore
