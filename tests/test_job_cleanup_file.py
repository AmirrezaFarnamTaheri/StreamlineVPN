from pathlib import Path
import json
from datetime import datetime, timedelta

from streamline_vpn.jobs.cleanup import JobCleanupService


def test_cleanup_handles_numeric_timestamps(tmp_path: Path):
    jobs_path = tmp_path / "jobs.json"
    now_epoch = int(datetime.now().timestamp())
    old_epoch = int((datetime.now() - timedelta(hours=48)).timestamp())

    data = {
        "jobs": [
            {
                "id": "job_epoch_running",
                "status": "running",
                "created_at": old_epoch,
                "started_at": old_epoch,
            },
            {
                "id": "job_epoch_pending",
                "status": "pending",
                "created_at": old_epoch,
            },
            {
                "id": "job_iso_completed",
                "status": "completed",
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "job_recent_running",
                "status": "running",
                "created_at": now_epoch,
                "started_at": now_epoch,
            },
        ]
    }

    jobs_path.write_text(json.dumps(data), encoding="utf-8")

    svc = JobCleanupService(jobs_file=str(jobs_path))
    stats = svc.cleanup_jobs()

    # Verify file is rewritten and statuses updated
    cleaned = json.loads(jobs_path.read_text(encoding="utf-8"))
    jobs = {j["id"]: j for j in cleaned["jobs"]}

    assert "job_epoch_running" in jobs
    assert jobs["job_epoch_running"]["status"] in {"failed", "cancelled", "timeout"}
    assert "finished_at" in jobs["job_epoch_running"]

    assert "job_epoch_pending" in jobs
    assert jobs["job_epoch_pending"]["status"] in {"failed", "cancelled", "timeout"}

    assert "job_iso_completed" in jobs
    assert jobs["job_iso_completed"]["status"] == "completed"

    # Recent running job may remain depending on cutoff; ensure it remains present
    assert "job_recent_running" in jobs

    # stats should track some fixes
    assert isinstance(stats, dict)
    assert stats.get("cleaned", 0) >= 1

