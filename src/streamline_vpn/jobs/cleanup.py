"""Job cleanup utilities for StreamlineVPN."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

from ..utils.logging import get_logger

logger = get_logger(__name__)


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
        logger.info("Starting job cleanup - File: %s", self.jobs_file)

        if not self.jobs_file.exists():
            logger.info("Jobs file does not exist, no cleanup needed")
            return {"cleaned": 0, "fixed": 0, "removed": 0}

        stats: Dict[str, Any] = {"cleaned": 0, "fixed": 0, "removed": 0}

        try:
            with open(self.jobs_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            jobs = data.get("jobs", [])
            logger.info("Found %d jobs to process", len(jobs))

            now = datetime.now()
            cutoff_date = now - timedelta(days=self.max_job_age_days)
            stale_cutoff = now - timedelta(hours=self.stale_timeout_hours)

            logger.debug(
                "Cleanup thresholds - Max age: %s, Stale timeout: %s",
                cutoff_date,
                stale_cutoff,
            )

            cleaned_jobs = []

            def _to_dt(value: Any, default: datetime) -> datetime:
                """Best-effort conversion of different timestamp formats to datetime.

                Supports ISO8601 strings and UNIX epoch (int/float). Falls back to default.
                """
                if value is None:
                    return default
                try:
                    if isinstance(value, (int, float)):
                        return datetime.fromtimestamp(float(value))
                    if isinstance(value, str) and value:
                        # Some historical values may already be ISO formatted
                        return datetime.fromisoformat(value)
                except Exception:
                    pass
                return default

            for job in jobs:
                created_at_raw = job.get("created_at")
                # Prefer created_at; if missing, derive from started_at or fallback to now
                created_at = _to_dt(created_at_raw, now)
                started_at = _to_dt(job.get("started_at"), created_at)

                # Normalize fields for future reads
                job.setdefault("created_at", created_at.isoformat())

                if job.get("status") in {"running", "pending"}:
                    # Treat long-running/pending jobs as failed on restart/timeout
                    if started_at < stale_cutoff:
                        job["status"] = "failed"
                        job["finished_at"] = now.isoformat()
                        job["error"] = "Job terminated on cleanup due to staleness"
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
                cleaned_jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
                removed_count = len(cleaned_jobs) - self.max_jobs_to_keep
                cleaned_jobs = cleaned_jobs[: self.max_jobs_to_keep]
                stats["removed"] += removed_count

            data["jobs"] = cleaned_jobs
            data["last_cleanup"] = now.isoformat()

            with open(self.jobs_file, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)

            logger.info("Job cleanup complete: %s", stats)
            return stats
        except Exception as exc:  # pragma: no cover - logging only
            logger.error("Error during job cleanup: %s", exc, exc_info=True)
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
            logger.error("Error getting job statistics: %s", exc, exc_info=True)
            return {}


async def startup_cleanup() -> Dict[str, Any]:
    """Run cleanup on application startup."""
    cleanup_service = JobCleanupService()

    stats = cleanup_service.cleanup_jobs()
    job_stats = cleanup_service.get_job_statistics()

    logger.info("Startup job cleanup completed")
    logger.info("Cleanup stats: %s", stats)
    logger.info("Job statistics: %s", job_stats)
    return stats


async def periodic_cleanup_task() -> None:
    """Run periodic cleanup every hour."""
    cleanup_service = JobCleanupService()

    while True:
        await asyncio.sleep(3600)
        try:
            stats = cleanup_service.cleanup_jobs()
            logger.info("Periodic cleanup completed: %s", stats)
        except Exception as exc:  # pragma: no cover - logging only
            logger.error("Periodic cleanup failed: %s", exc, exc_info=True)


if __name__ == "__main__":  # pragma: no cover - manual execution only
    service = JobCleanupService()
    STATS = service.cleanup_jobs()
    logger.info("Cleanup completed: %s", STATS)
    JOB_STATS = service.get_job_statistics()
    logger.info("Current job statistics: %s", JOB_STATS)
