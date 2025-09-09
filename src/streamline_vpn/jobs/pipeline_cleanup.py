"""Utilities for cleaning up pipeline processing jobs."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..utils.logging import get_logger

logger = get_logger(__name__)

processing_jobs: Dict[str, Any] = {}
JOB_RETENTION_PERIOD = timedelta(hours=1)


def cleanup_processing_jobs(
    retention: timedelta = JOB_RETENTION_PERIOD,
) -> int:
    """Remove completed or failed jobs older than *retention*."""
    now = datetime.now()
    to_remove: List[str] = []
    for job_id, data in list(processing_jobs.items()):
        status = data.get("status")
        if status not in {"completed", "failed"}:
            continue
        ts_str = data.get("completed_at") or data.get("started_at")
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str)
        except Exception:  # pragma: no cover - invalid timestamp
            continue
        if ts < now - retention:
            to_remove.append(job_id)

    for job_id in to_remove:
        processing_jobs.pop(job_id, None)
    return len(to_remove)


async def cleanup_processing_jobs_periodically() -> None:
    """Background task that periodically cleans up old jobs."""
    try:
        while True:
            await asyncio.sleep(60)
            try:
                cleanup_processing_jobs()
            except Exception:  # pragma: no cover - logging only
                logger.exception("Background job cleanup failed")
    except asyncio.CancelledError:  # graceful cancellation
        return


__all__ = [
    "processing_jobs",
    "JOB_RETENTION_PERIOD",
    "cleanup_processing_jobs",
    "cleanup_processing_jobs_periodically",
]
