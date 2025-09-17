"""
Job Management System
=====================

Job management and persistence system for StreamlineVPN.
"""

from .cleanup import JobCleanupService
from .manager import JobManager
from .models import Job as _Job


class Job(_Job):
    def __init__(self, *args, **kwargs):
        # Backwards compatibility: map job_type -> type, job_status -> status
        if "job_type" in kwargs and "type" not in kwargs:
            val = kwargs.pop("job_type")
            try:
                from .models import JobType

                kwargs["type"] = val if isinstance(val, JobType) else JobType(val)
            except Exception:
                pass
        if "job_status" in kwargs and "status" not in kwargs:
            val = kwargs.pop("job_status")
            try:
                from .models import JobStatus

                kwargs["status"] = val if isinstance(val, JobStatus) else JobStatus(val)
            except Exception:
                pass
        super().__init__(*args, **kwargs)


from .models import JobStatus, JobType
from .persistence import JobPersistence

__all__ = [
    "JobManager",
    "Job",
    "JobStatus",
    "JobType",
    "JobPersistence",
    "JobCleanupService",
]
