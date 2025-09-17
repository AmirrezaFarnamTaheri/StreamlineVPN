"""
Job Models
==========

Data models for job management system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any
import json
import uuid


class JobStatus(Enum):
    """Job status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    def __eq__(self, other):
        """Allow comparison with string values."""
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)

    # Restore hashability after overriding __eq__
    __hash__ = Enum.__hash__

    def __contains__(self, item):
        """Allow 'in' operator with string values."""
        if isinstance(item, str):
            return item in [e.value for e in JobStatus]
        return super().__contains__(item)

    @classmethod
    def contains_value(cls, item):
        """Check if a string value is in the enum."""
        if isinstance(item, str):
            return item in [e.value for e in cls]
        return False


class JobType(Enum):
    """Job type enumeration."""

    PROCESS_CONFIGURATIONS = "process_configurations"
    DISCOVER_SOURCES = "discover_sources"
    UPDATE_SOURCES = "update_sources"
    CLEAR_CACHE = "clear_cache"
    EXPORT_CONFIGURATIONS = "export_configurations"
    # Backwards-compat alias used by some tests
    PROCESSING = "processing"
    # Additional types used by tests
    VALIDATE_CONFIGURATIONS = "validate_configurations"
    CLEANUP = "cleanup"
    MAINTENANCE = "maintenance"
    BACKUP = "backup"
    SYNC = "sync"

    def __eq__(self, other):
        """Allow comparison with string values."""
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)

    # Restore hashability after overriding __eq__
    __hash__ = Enum.__hash__

    def __contains__(self, item):
        """Allow 'in' operator with string values."""
        if isinstance(item, str):
            return item in [e.value for e in JobType]
        return super().__contains__(item)

    @classmethod
    def contains_value(cls, item):
        """Check if a string value is in the enum."""
        if isinstance(item, str):
            return item in [e.value for e in cls]
        return False


@dataclass(init=False)
class Job:
    """Job data model.

    Attributes:
        id: Unique job identifier
        type: Type of job
        status: Current job status
        parameters: Job parameters
        result: Job result data
        error: Error message if failed
        created_at: Job creation timestamp
        started_at: Job start timestamp
        completed_at: Job completion timestamp
        progress: Job progress (0-100)
        metadata: Additional job metadata
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    type: JobType = JobType.PROCESS_CONFIGURATIONS
    status: JobStatus = JobStatus.PENDING
    description: Optional[str] = None  # Added for test compatibility
    priority: int = 1  # Added for test compatibility
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None  # Added for test compatibility
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        type: Optional[JobType] = None,
        job_type: Optional[JobType] = None,
        status: JobStatus = JobStatus.PENDING,
        description: Optional[str] = None,
        priority: int = 1,
        parameters: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        progress: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        # Accept alternate keyword names: job_type -> type
        resolved_type = type or job_type or JobType.PROCESS_CONFIGURATIONS
        if not isinstance(resolved_type, JobType):
            try:
                resolved_type = JobType(resolved_type)
            except Exception:
                resolved_type = JobType.PROCESS_CONFIGURATIONS

        self.id = id or str(uuid.uuid4())
        self.name = name
        self.type = resolved_type
        self.status = (
            status if isinstance(status, JobStatus) else JobStatus(str(status))
        )
        self.description = description
        self.priority = int(priority)
        self.parameters = parameters or {}
        self.result = result
        self.error = error
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.started_at = started_at
        self.completed_at = completed_at
        self.progress = int(progress)
        self.metadata = metadata or {}

    def __post_init__(self):
        """Validate job after initialization."""
        # Accept alternate input names by shadowing dataclass init via kwargs
        # If an alternate name was used via from_dict/create, the mapping handled it.
        if not (0 <= self.progress <= 100):
            raise ValueError("Progress must be between 0 and 100")

    def start(self) -> None:
        """Mark job as started."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark job as completed.

        Args:
            result: Job result data
        """
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now()
        self.progress = 100
        if result:
            self.result = result

    def fail(self, error: str) -> None:
        """Mark job as failed.

        Args:
            error: Error message
        """
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error

    def cancel(self) -> None:
        """Mark job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now()

    def update_progress(self, progress: int) -> None:
        """Update job progress.

        Args:
            progress: Progress percentage (0-100)
        """
        if not (0 <= progress <= 100):
            raise ValueError("Progress must be between 0 and 100")
        self.progress = progress

    @property
    def duration(self) -> Optional[float]:
        """Get job duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_finished(self) -> bool:
        """Check if job is finished (completed, failed, or cancelled)."""
        return self.status in [
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        ]

    @property
    def job_type(self) -> JobType:
        """Backwards-compatible alias for type."""
        return self.type

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "status": self.status.value,
            "description": self.description,
            "priority": self.priority,
            "parameters": self.parameters,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": (self.updated_at.isoformat() if self.updated_at else None),
            "started_at": (self.started_at.isoformat() if self.started_at else None),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "progress": self.progress,
            "duration": self.duration,
            "is_finished": self.is_finished,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        """Create from dictionary."""
        data = data.copy()
        data["type"] = JobType(data["type"])
        data["status"] = JobStatus(data["status"])

        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if (
            "updated_at" in data
            and data["updated_at"]
            and isinstance(data["updated_at"], str)
        ):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if (
            "started_at" in data
            and data["started_at"]
            and isinstance(data["started_at"], str)
        ):
            data["started_at"] = datetime.fromisoformat(data["started_at"])
        if (
            "completed_at" in data
            and data["completed_at"]
            and isinstance(data["completed_at"], str)
        ):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])

        # Remove read-only/computed fields not accepted by the constructor
        data.pop("duration", None)
        data.pop("is_finished", None)
        return cls(**data)

    # Backwards-compatibility: allow alternative argument names in constructor via classmethod
    @classmethod
    def create(cls, **kwargs: Any) -> "Job":
        # Map job_type -> type
        if "job_type" in kwargs and "type" not in kwargs:
            val = kwargs.pop("job_type")
            try:
                kwargs["type"] = val if isinstance(val, JobType) else JobType(val)
            except Exception:
                kwargs["type"] = JobType.PROCESS_CONFIGURATIONS
        # Map job_status -> status
        if "job_status" in kwargs and "status" not in kwargs:
            val = kwargs.pop("job_status")
            try:
                kwargs["status"] = val if isinstance(val, JobStatus) else JobStatus(val)
            except Exception:
                kwargs["status"] = JobStatus.PENDING
        return cls(**kwargs)

    @classmethod
    def from_json(cls, json_str: str) -> "Job":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def __str__(self) -> str:
        """String representation."""
        return f"Job({self.id[:8]}...): {self.type.value} - {self.status.value}"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"Job(id={self.id}, type={self.type.value}, "
            f"status={self.status.value}, progress={self.progress}%)"
        )
