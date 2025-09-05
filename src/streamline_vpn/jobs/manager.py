"""
Job Manager (Refactored)
========================

Refactored job management system for StreamlineVPN.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import Job, JobStatus, JobType
from .persistence import JobPersistence
from .job_executor import JobExecutor
from ..utils.logging import get_logger

logger = get_logger(__name__)


class JobManager:
    """Refactored job management system."""

    def __init__(self, persistence: Optional[JobPersistence] = None):
        """Initialize job manager.
        
        Args:
            persistence: Job persistence layer
        """
        self.persistence = persistence or JobPersistence()
        self.running_jobs: Dict[str, asyncio.Task] = {}
        self.executor = JobExecutor(self)

    async def create_job(
        self, 
        job_type: JobType, 
        parameters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Job:
        """Create a new job.
        
        Args:
            job_type: Type of job to create
            parameters: Job parameters
            metadata: Additional metadata
            
        Returns:
            Created job instance
        """
        job = Job(
            type=job_type,
            parameters=parameters or {},
            metadata=metadata or {}
        )
        
        self.persistence.save_job(job)
        logger.info(f"Created job {job.id} of type {job_type.value}")
        
        return job

    async def start_job(self, job_id: str) -> bool:
        """Start a job.
        
        Args:
            job_id: Job ID to start
            
        Returns:
            True if started successfully, False otherwise
        """
        job = self.persistence.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return False

        if job.status != JobStatus.PENDING:
            logger.warning(f"Job {job_id} is not pending (status: {job.status.value})")
            return False

        if job_id in self.running_jobs:
            logger.warning(f"Job {job_id} is already running")
            return False

        # Start the job
        job.start()
        self.persistence.save_job(job)

        # Create and start async task
        task = asyncio.create_task(self.executor.execute_job(job))
        self.running_jobs[job_id] = task

        logger.info(f"Started job {job_id}")
        return True

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        if job_id not in self.running_jobs:
            logger.warning(f"Job {job_id} is not running")
            return False

        # Cancel the task
        task = self.running_jobs[job_id]
        task.cancel()

        # Update job status
        job = self.persistence.get_job(job_id)
        if job:
            job.cancel()
            self.persistence.save_job(job)

        # Remove from running jobs
        del self.running_jobs[job_id]

        logger.info(f"Cancelled job {job_id}")
        return True

    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job instance or None if not found
        """
        return self.persistence.get_job(job_id)

    async def get_jobs(
        self, 
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        limit: int = 100,
        offset: int = 0
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
        return self.persistence.get_jobs(status, job_type, limit, offset)

    async def delete_job(self, job_id: str) -> bool:
        """Delete job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if deleted, False if not found
        """
        # Cancel if running
        if job_id in self.running_jobs:
            await self.cancel_job(job_id)

        return self.persistence.delete_job(job_id)

    async def cleanup_old_jobs(self, days: int = 30) -> int:
        """Clean up old completed jobs.
        
        Args:
            days: Number of days to keep completed jobs
            
        Returns:
            Number of jobs deleted
        """
        return self.persistence.cleanup_old_jobs(days)

    async def get_statistics(self) -> Dict[str, Any]:
        """Get job statistics.
        
        Returns:
            Dictionary with job statistics
        """
        return self.persistence.get_statistics()

    async def close(self) -> None:
        """Close job manager and cleanup resources."""
        # Cancel all running jobs
        for job_id in list(self.running_jobs.keys()):
            await self.cancel_job(job_id)

        logger.info("Job manager closed")
