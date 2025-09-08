"""
Job Persistence
===============

Job persistence layer for storing and retrieving jobs.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...utils.logging import get_logger
from .models import Job, JobStatus, JobType

logger = get_logger(__name__)


class JobPersistence:
    """Job persistence layer using SQLite."""

    def __init__(self, db_path: str = "data/jobs.db"):
        """Initialize job persistence.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()

            # Create jobs table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    parameters TEXT,
                    result TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    progress INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """
            )

            # Create indexes
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(type)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_created_at "
                "ON jobs(created_at)"
            )

            conn.commit()

    def save_job(self, job: Job) -> None:
        """Save job to database.

        Args:
            job: Job to save
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO jobs
                    (id, type, status, parameters, result, error, created_at,
                     started_at, completed_at, progress, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        job.id,
                        job.type.value,
                        job.status.value,
                        json.dumps(job.parameters),
                        json.dumps(job.result) if job.result else None,
                        job.error,
                        job.created_at.isoformat(),
                        job.started_at.isoformat()
                        if job.started_at
                        else None,
                        (
                            job.completed_at.isoformat()
                            if job.completed_at
                            else None
                        ),
                        job.progress,
                        json.dumps(job.metadata),
                    ),
                )

                conn.commit()
                logger.debug(f"Saved job {job.id}")

        except Exception as e:
            logger.error(f"Error saving job {job.id}: {e}")
            raise

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job instance or None if not found
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
                row = cursor.fetchone()

                if row:
                    return self._row_to_job(row)
                return None

        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return None

    def get_jobs(
        self,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Job]:
        """Get jobs with optional filtering.

        Args:
            status: Filter by job status
            job_type: Filter by job type
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            List of job instances
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM jobs WHERE 1=1"
                params = []

                if status:
                    query += " AND status = ?"
                    params.append(status.value)

                if job_type:
                    query += " AND type = ?"
                    params.append(job_type.value)

                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [self._row_to_job(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            return []

    def delete_job(self, job_id: str) -> bool:
        """Delete job by ID.

        Args:
            job_id: Job ID

        Returns:
            True if deleted, False if not found
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()

                cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
                deleted = cursor.rowcount > 0
                conn.commit()

                if deleted:
                    logger.debug(f"Deleted job {job_id}")
                return deleted

        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {e}")
            return False

    def cleanup_old_jobs(self, days: int = 30) -> int:
        """Clean up old completed jobs.

        Args:
            days: Number of days to keep completed jobs

        Returns:
            Number of jobs deleted
        """
        try:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()

            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    DELETE FROM jobs
                    WHERE status IN (?, ?, ?)
                    AND created_at < ?
                    """,
                    (
                        JobStatus.COMPLETED.value,
                        JobStatus.FAILED.value,
                        JobStatus.CANCELLED.value,
                        cutoff_iso,
                    ),
                )

                deleted = cursor.rowcount
                conn.commit()

                if deleted > 0:
                    logger.info(f"Cleaned up {deleted} old jobs")
                return deleted

        except Exception as e:
            logger.error(f"Error cleaning up old jobs: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """Get job statistics.

        Returns:
            Dictionary with job statistics
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()

                # Total jobs
                cursor.execute("SELECT COUNT(*) FROM jobs")
                total_jobs = cursor.fetchone()[0]

                # Jobs by status
                cursor.execute(
                    """
                    SELECT status, COUNT(*)
                    FROM jobs
                    GROUP BY status
                """
                )
                status_counts = dict(cursor.fetchall())

                # Jobs by type
                cursor.execute(
                    """
                    SELECT type, COUNT(*)
                    FROM jobs
                    GROUP BY type
                """
                )
                type_counts = dict(cursor.fetchall())

                # Recent jobs (last 24 hours)
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM jobs
                    WHERE created_at > datetime('now', '-1 day')
                """
                )
                recent_jobs = cursor.fetchone()[0]

                return {
                    "total_jobs": total_jobs,
                    "status_counts": status_counts,
                    "type_counts": type_counts,
                    "recent_jobs": recent_jobs,
                }

        except Exception as e:
            logger.error(f"Error getting job statistics: {e}")
            return {}

    def _row_to_job(self, row: tuple) -> Job:
        """Convert database row to Job instance.

        Args:
            row: Database row tuple

        Returns:
            Job instance
        """
        job_data = {
            "id": row[0],
            "type": JobType(row[1]),
            "status": JobStatus(row[2]),
            "parameters": json.loads(row[3]) if row[3] else {},
            "result": json.loads(row[4]) if row[4] else None,
            "error": row[5],
            "created_at": datetime.fromisoformat(row[6]),
            "started_at": datetime.fromisoformat(row[7]) if row[7] else None,
            "completed_at": (
                datetime.fromisoformat(row[8]) if row[8] else None
            ),
            "progress": row[9],
            "metadata": json.loads(row[10]) if row[10] else {},
        }

        return Job(**job_data)
