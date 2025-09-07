"""Job cleanup utilities for StreamlineVPN."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict


class JobCleanupService:
    """Service to clean up stale jobs and maintain job history."""

    def __init__(self, jobs_file: str = "data/jobs.json") -> None:
        self.jobs_file = Path(jobs_file)
        self.max_job_age_days = 30
        self.max_jobs_to_keep = 1000
        self.stale_timeout_hours = 24

    def cleanup_jobs(self) -> Dict[str, Any]:
        """Clean up stale and old jobs.

        Returns
        -------
        Dict[str, Any]
            Statistics about the cleanup process.
        """
        if not self.jobs_file.exists():
            return {"cleaned": 0, "fixed": 0, "removed": 0}

        stats: Dict[str, Any] = {"cleaned": 0, "fixed": 0, "removed": 0}

        try:
            with open(self.jobs_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            jobs = data.get("jobs", [])
            now = datetime.now()
            cutoff_date = now - timedelta(days=self.max_job_age_days)
            stale_cutoff = now - timedelta(hours=self.stale_timeout_hours)

            cleaned_jobs = []

            for job in jobs:
                created_at = datetime.fromisoformat(
                    job.get("created_at", now.isoformat())
                )
                started_at = job.get("started_at")

                if job.get("status") in {"running", "pending"}:
                    if started_at:
                        started_time = datetime.fromisoformat(started_at)
                        if started_time < stale_cutoff:
                            job["status"] = "timeout"
                            job["finished_at"] = now.isoformat()
                            job["error"] = (
                                "Job timeout - exceeded maximum runtime"
                            )
                            stats["fixed"] += 1
                    elif created_at < stale_cutoff:
                        job["status"] = "cancelled"
                        job["finished_at"] = now.isoformat()
                        job["error"] = "Job cancelled - never started"
                        stats["fixed"] += 1

                if created_at < cutoff_date:
                    stats["removed"] += 1
                    continue

                cleaned_jobs.append(job)
                stats["cleaned"] += 1

            if len(cleaned_jobs) > self.max_jobs_to_keep:
                cleaned_jobs.sort(
                    key=lambda j: j.get("created_at", ""), reverse=True
                )
                removed_count = len(cleaned_jobs) - self.max_jobs_to_keep
                cleaned_jobs = cleaned_jobs[: self.max_jobs_to_keep]
                stats["removed"] += removed_count

            data["jobs"] = cleaned_jobs
            data["last_cleanup"] = now.isoformat()

            with open(self.jobs_file, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)

            print(f"Job cleanup complete: {stats}")
            return stats
        except Exception as exc:  # pragma: no cover - logging only
            print(f"Error during job cleanup: {exc}")
            return stats

    def get_job_statistics(self) -> Dict[str, Any]:
        """Get statistics about jobs."""
        if not self.jobs_file.exists():
            return {}

        try:
            with open(self.jobs_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            jobs = data.get("jobs", [])

            stats: Dict[str, Any] = {
                "total_jobs": len(jobs),
                "status_counts": {},
                "age_distribution": {
                    "last_hour": 0,
                    "last_day": 0,
                    "last_week": 0,
                    "older": 0,
                },
            }

            now = datetime.now()
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)
            week_ago = now - timedelta(days=7)

            for job in jobs:
                status = job.get("status", "unknown")
                stats["status_counts"][status] = (
                    stats["status_counts"].get(status, 0) + 1
                )

                created_at = datetime.fromisoformat(
                    job.get("created_at", now.isoformat())
                )
                if created_at > hour_ago:
                    stats["age_distribution"]["last_hour"] += 1
                elif created_at > day_ago:
                    stats["age_distribution"]["last_day"] += 1
                elif created_at > week_ago:
                    stats["age_distribution"]["last_week"] += 1
                else:
                    stats["age_distribution"]["older"] += 1

            return stats
        except Exception as exc:  # pragma: no cover - logging only
            print(f"Error getting job statistics: {exc}")
            return {}


async def startup_cleanup() -> Dict[str, Any]:
    """Run cleanup on application startup."""
    cleanup_service = JobCleanupService()

    stats = cleanup_service.cleanup_jobs()
    job_stats = cleanup_service.get_job_statistics()

    print("Startup job cleanup completed")
    print(f"Cleanup stats: {stats}")
    print(f"Job statistics: {job_stats}")
    return stats


async def periodic_cleanup_task() -> None:
    """Run periodic cleanup every hour."""
    cleanup_service = JobCleanupService()

    while True:
        await asyncio.sleep(3600)
        try:
            stats = cleanup_service.cleanup_jobs()
            print(f"Periodic cleanup completed: {stats}")
        except Exception as exc:  # pragma: no cover - logging only
            print(f"Periodic cleanup failed: {exc}")


if __name__ == "__main__":  # pragma: no cover - manual execution only
    service = JobCleanupService()
    STATS = service.cleanup_jobs()
    print(f"Cleanup completed: {STATS}")
    JOB_STATS = service.get_job_statistics()
    print(f"Current job statistics: {JOB_STATS}")
