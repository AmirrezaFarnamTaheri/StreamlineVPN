"""
Minimal in-memory job manager for long-running merges.
"""

from __future__ import annotations

import asyncio
import builtins
import json
import logging
import os
import time

try:  # allow tests to monkeypatch Path before reload
    Path  # type: ignore[name-defined]
except NameError:  # pragma: no cover
    from pathlib import Path

from ...core.source_processor import SourceProcessor
from ...monitoring.observability import get_meter_if_any

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None


class Job:
    def __init__(self, job_id: str, sources: list[str]):
        self.id = job_id
        self.sources = sources
        self.status = "pending"
        self.total_configs = 0
        self.valid_configs = 0
        self.started_at = time.time()
        self.finished_at: float | None = None
        self.progress = 0.0
        self._cancel_event = asyncio.Event()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sources": self.sources,
            "status": self.status,
            "total_configs": self.total_configs,
            "valid_configs": self.valid_configs,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "progress": self.progress,
        }

    @staticmethod
    def from_dict(d: dict) -> Job:
        j = Job(d.get("id", f"job_{int(time.time()*1000)}"), d.get("sources", []))
        j.status = d.get("status", "pending")
        j.total_configs = int(d.get("total_configs", 0))
        j.valid_configs = int(d.get("valid_configs", 0))
        j.started_at = float(d.get("started_at", time.time()))
        j.finished_at = d.get("finished_at")
        j.progress = float(d.get("progress", 0.0))
        return j


class JobManager:
    def __init__(self):
        self.jobs: dict[str, Job] = {}
        self._redis = None
        self._json_path = Path("data/jobs.json")
        self._ttl_days = float(os.getenv("JOBS_TTL_DAYS", "7"))
        self._logger = logging.getLogger(__name__)
        self._otel_meter = get_meter_if_any()
        self._metrics = {}
        self._init_storage()
        self._load_jobs()
        # background cleanup task
        try:
            interval = float(os.getenv("JOBS_CLEANUP_INTERVAL_SEC", "600"))
            # Don't create task in __init__ to avoid warnings
            # Task will be created when needed
        except Exception:
            pass

    def create_job(self, sources: builtins.list[str]) -> Job:
        job_id = f"job_{int(time.time() * 1000)}"
        job = Job(job_id, sources)
        self.jobs[job_id] = job
        asyncio.create_task(self._run(job))
        self._save_job(job)
        self._inc_metric("jobs_created_total", 1)
        self._logger.info("job_created", extra={"job_id": job_id, "sources": len(sources)})
        return job

    async def _run(self, job: Job):
        job.status = "running"
        async with SourceProcessor() as sp:
            # Naive progress: step through sources
            total = max(1, len(job.sources))
            results = []
            for idx, src in enumerate(job.sources):
                if job._cancel_event.is_set():
                    job.status = "cancelled"
                    self._save_job(job)
                    return
                # Use batch processing for better performance
                batch = await sp.process_sources_batch([src], batch_size=1, max_concurrent=1)
                results.extend(batch)
                job.progress = min(1.0, (idx + 1) / total)
                self._save_job(job)
        job.total_configs = len(results)
        job.valid_configs = len(results)
        job.status = "completed"
        job.finished_at = time.time()
        self._save_job(job)
        self._inc_metric("jobs_completed_total", 1)
        self._logger.info(
            "job_completed",
            extra={"job_id": job.id, "total": job.total_configs, "valid": job.valid_configs},
        )

    def get(self, job_id: str) -> Job | None:
        return self.jobs.get(job_id)

    def list(self) -> builtins.list[Job]:
        return list(self.jobs.values())

    def cancel(self, job_id: str) -> bool:
        j = self.jobs.get(job_id)
        if not j or j.status in ("completed", "cancelled"):
            return False
        j._cancel_event.set()
        self._inc_metric("jobs_cancelled_total", 1)
        self._logger.info("job_cancel_requested", extra={"job_id": job_id})
        return True

    def delete(self, job_id: str) -> bool:
        j = self.jobs.pop(job_id, None)
        if not j:
            return False
        # Remove from storage
        try:
            if self._redis is not None:
                self._redis.delete(f"job:{job_id}")
            else:
                payload = {"jobs": [x.to_dict() for x in self.jobs.values()]}
                self._json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass
        self._logger.info("job_deleted", extra={"job_id": job_id})
        return True

    # ---- Storage helpers ----
    def _init_storage(self) -> None:
        url = os.getenv("REDIS_URL")
        if url and redis is not None:
            try:
                self._redis = redis.from_url(url)
            except Exception:
                self._redis = None
        else:
            # ensure data directory exists
            self._json_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_jobs(self) -> None:
        try:
            if self._redis is not None:
                keys = [k.decode("utf-8") for k in self._redis.keys("job:*")]
                for k in keys:
                    data = self._redis.get(k)
                    if not data:
                        continue
                    d = json.loads(data)
                    j = Job.from_dict(d)
                    if not self._is_expired(j):
                        self.jobs[j.id] = j
            else:
                if self._json_path.exists():
                    d = json.loads(self._json_path.read_text(encoding="utf-8"))
                    for item in d.get("jobs", []):
                        j = Job.from_dict(item)
                        if not self._is_expired(j):
                            self.jobs[j.id] = j
        except Exception:
            # Best-effort load
            pass

    def _save_job(self, job: Job) -> None:
        try:
            if self._redis is not None:
                key = f"job:{job.id}"
                self._redis.set(key, json.dumps(job.to_dict()))
            else:
                # write all jobs to JSON
                payload = {"jobs": [j.to_dict() for j in self.jobs.values()]}
                self._json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            # Best-effort persistence
            pass

    def _is_expired(self, job: Job) -> bool:
        try:
            # Expire completed/cancelled jobs older than TTL days
            if job.status not in ("completed", "cancelled"):
                return False
            if job.finished_at is None:
                return False
            age_days = (time.time() - float(job.finished_at)) / 86400.0
            return age_days > self._ttl_days
        except Exception:
            return False

    async def _cleanup_loop(self, interval: float) -> None:
        while True:
            await asyncio.sleep(max(60.0, interval))
            removed = self.cleanup_now()
            
            # Periodic memory cleanup every 10 cleanup cycles
            if hasattr(self, '_cleanup_count'):
                self._cleanup_count += 1
            else:
                self._cleanup_count = 1
                
            if self._cleanup_count % 10 == 0:
                await self._cleanup_memory_resources()

    async def _cleanup_memory_resources(self):
        """Cleanup memory resources to prevent memory leaks."""
        try:
            # Clear metrics cache if it gets too large
            if len(self._metrics) > 50:
                # Keep only essential metrics
                essential_metrics = {}
                for name in ['jobs_completed_total', 'jobs_cancelled_total', 'jobs_cleaned_total']:
                    if name in self._metrics:
                        essential_metrics[name] = self._metrics[name]
                self._metrics.clear()
                self._metrics.update(essential_metrics)
            
            # Force garbage collection
            import gc
            gc.collect()
            
        except Exception as e:
            self._logger.warning(f"Error during memory cleanup: {e}")

    def cleanup_now(self) -> int:
        """Remove expired jobs from memory and storage. Returns count removed."""
        removed = 0
        to_delete = [jid for jid, j in self.jobs.items() if self._is_expired(j)]
        for jid in to_delete:
            if self.delete(jid):
                removed += 1
        if removed:
            self._inc_metric("jobs_cleaned_total", removed)
            self._logger.info("jobs_cleaned", extra={"count": removed, "ttl_days": self._ttl_days})
        return removed

    # ---- Metrics helpers (OTEL) ----
    def _get_counter(self, name: str):
        if not self._otel_meter:
            return None
        if name in self._metrics:
            return self._metrics[name]
        try:
            c = self._otel_meter.create_counter(
                name=name, unit="1", description=name.replace("_", " ")
            )
            self._metrics[name] = c
            return c
        except Exception:
            return None

    def _inc_metric(self, name: str, value: int):
        c = self._get_counter(name)
        if c:
            try:
                c.add(int(value))
            except Exception:
                pass


job_manager = JobManager()
