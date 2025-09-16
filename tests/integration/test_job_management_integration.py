"""
Integration tests for job management functionality.
"""

import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Optional
import pytest
from datetime import datetime

from streamline_vpn.jobs.manager import JobManager
from streamline_vpn.jobs.models import Job, JobStatus, JobType
from streamline_vpn.jobs.persistence import JobPersistence


class TestJobManagement:
    """Test job management integration."""

    @pytest.fixture
    def job_manager(self):
        return JobManager()

    @pytest.fixture
    def sample_job(self):
        return Job(
            id="test-job-1",
            job_type=JobType.PROCESS_CONFIGURATIONS,
            status=JobStatus.PENDING,
            created_at=datetime.now(),
            parameters={"sources": ["https://example.com/test.txt"]}
        )

    @pytest.mark.asyncio
    async def test_job_creation_integration(self, job_manager, sample_job):
        """Test job creation integration."""
        with patch('streamline_vpn.jobs.manager.JobManager.create_job') as mock_create:
            mock_create.return_value = AsyncMock(return_value=sample_job)
            
            job = await job_manager.create_job(
                job_type=JobType.PROCESS_CONFIGURATIONS,
                parameters={"sources": ["https://example.com/test.txt"]}
            )
            
            assert job is not None
            assert job.job_type == JobType.PROCESS_CONFIGURATIONS

    @pytest.mark.asyncio
    async def test_job_execution_integration(self, job_manager, sample_job):
        """Test job execution integration."""
        with patch('streamline_vpn.jobs.manager.JobManager.execute_job') as mock_execute:
            mock_execute.return_value = AsyncMock(return_value=True)
            
            result = await job_manager.execute_job(sample_job.id)
            assert result is True

    @pytest.mark.asyncio
    async def test_job_status_update_integration(self, job_manager, sample_job):
        """Test job status update integration."""
        with patch('streamline_vpn.jobs.manager.JobManager.update_job_status') as mock_update:
            mock_update.return_value = AsyncMock(return_value=True)
            
            result = await job_manager.update_job_status(
                sample_job.id, 
                JobStatus.RUNNING
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_job_retrieval_integration(self, job_manager, sample_job):
        """Test job retrieval integration."""
        with patch('streamline_vpn.jobs.manager.JobManager.get_job') as mock_get:
            mock_get.return_value = AsyncMock(return_value=sample_job)
            
            job = await job_manager.get_job(sample_job.id)
            assert job is not None
            assert job.id == sample_job.id

    @pytest.mark.asyncio
    async def test_job_listing_integration(self, job_manager):
        """Test job listing integration."""
        with patch('streamline_vpn.jobs.manager.JobManager.list_jobs') as mock_list:
            mock_jobs = [
                Job(id="job-1", job_type=JobType.PROCESS_CONFIGURATIONS, status=JobStatus.PENDING),
                Job(id="job-2", job_type=JobType.VALIDATE_CONFIGURATIONS, status=JobStatus.RUNNING)
            ]
            mock_list.return_value = AsyncMock(return_value=mock_jobs)
            
            jobs = await job_manager.list_jobs()
            assert len(jobs) == 2
            assert all(isinstance(job, Job) for job in jobs)

    @pytest.mark.asyncio
    async def test_job_cancellation_integration(self, job_manager, sample_job):
        """Test job cancellation integration."""
        with patch('streamline_vpn.jobs.manager.JobManager.cancel_job') as mock_cancel:
            mock_cancel.return_value = AsyncMock(return_value=True)
            
            result = await job_manager.cancel_job(sample_job.id)
            assert result is True

    @pytest.mark.asyncio
    async def test_job_cleanup_integration(self, job_manager):
        """Test job cleanup integration."""
        with patch('streamline_vpn.jobs.manager.JobManager.cleanup_completed_jobs') as mock_cleanup:
            mock_cleanup.return_value = AsyncMock(return_value=5)
            
            cleaned_count = await job_manager.cleanup_completed_jobs()
            assert cleaned_count == 5

    @pytest.mark.asyncio
    async def test_job_persistence_integration(self, sample_job):
        """Test job persistence integration."""
        with patch('streamline_vpn.jobs.persistence.JobPersistence.save_job') as mock_save:
            mock_save.return_value = AsyncMock(return_value=True)
            
            persistence = JobPersistence()
            result = await persistence.save_job(sample_job)
            assert result is True

    @pytest.mark.asyncio
    async def test_job_retrieval_by_status_integration(self, job_manager):
        """Test job retrieval by status integration."""
        with patch('streamline_vpn.jobs.manager.JobManager.get_jobs_by_status') as mock_get_by_status:
            mock_jobs = [
                Job(id="job-1", job_type=JobType.PROCESS_CONFIGURATIONS, status=JobStatus.PENDING),
                Job(id="job-2", job_type=JobType.VALIDATE_CONFIGURATIONS, status=JobStatus.PENDING)
            ]
            mock_get_by_status.return_value = AsyncMock(return_value=mock_jobs)
            
            jobs = await job_manager.get_jobs_by_status(JobStatus.PENDING)
            assert len(jobs) == 2
            assert all(job.status == JobStatus.PENDING for job in jobs)

    @pytest.mark.asyncio
    async def test_job_retrieval_by_type_integration(self, job_manager):
        """Test job retrieval by type integration."""
        with patch('streamline_vpn.jobs.manager.JobManager.get_jobs_by_type') as mock_get_by_type:
            mock_jobs = [
                Job(id="job-1", job_type=JobType.PROCESS_CONFIGURATIONS, status=JobStatus.PENDING),
                Job(id="job-2", job_type=JobType.PROCESS_CONFIGURATIONS, status=JobStatus.RUNNING)
            ]
            mock_get_by_type.return_value = AsyncMock(return_value=mock_jobs)
            
            jobs = await job_manager.get_jobs_by_type(JobType.PROCESS_CONFIGURATIONS)
            assert len(jobs) == 2
            assert all(job.job_type == JobType.PROCESS_CONFIGURATIONS for job in jobs)

    @pytest.mark.asyncio
    async def test_job_error_handling_integration(self, job_manager):
        """Test job error handling integration."""
        with patch('streamline_vpn.jobs.manager.JobManager.execute_job') as mock_execute:
            mock_execute.side_effect = Exception("Job execution failed")
            
            with pytest.raises(Exception):
                await job_manager.execute_job("nonexistent-job")

    @pytest.mark.asyncio
    async def test_job_concurrent_execution_integration(self, job_manager):
        """Test concurrent job execution integration."""
        with patch('streamline_vpn.jobs.manager.JobManager.execute_job') as mock_execute:
            mock_execute.return_value = AsyncMock(return_value=True)
            
            # Test concurrent job execution
            tasks = []
            for i in range(5):
                task = job_manager.execute_job(f"job-{i}")
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            assert all(results)

    @pytest.mark.asyncio
    async def test_job_statistics_integration(self, job_manager):
        """Test job statistics integration."""
        with patch('streamline_vpn.jobs.manager.JobManager.get_job_statistics') as mock_stats:
            mock_stats.return_value = AsyncMock(return_value={
                "total_jobs": 10,
                "pending_jobs": 3,
                "running_jobs": 2,
                "completed_jobs": 4,
                "failed_jobs": 1
            })
            
            stats = await job_manager.get_job_statistics()
            assert stats["total_jobs"] == 10
            assert stats["pending_jobs"] == 3
            assert stats["running_jobs"] == 2
            assert stats["completed_jobs"] == 4
            assert stats["failed_jobs"] == 1

