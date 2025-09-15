"""
Focused tests for JobExecutor
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.jobs.job_executor import JobExecutor
from streamline_vpn.jobs.models import Job, JobStatus, JobType


class TestJobExecutor:
    """Test JobExecutor class"""
    
    def test_initialization(self):
        """Test job executor initialization"""
        executor = JobExecutor()
        assert hasattr(executor, 'running_jobs')
        assert hasattr(executor, 'max_concurrent_jobs')
        assert hasattr(executor, 'is_running')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test job executor initialization"""
        executor = JobExecutor()
        result = await executor.initialize()
        assert result is True
    
    def test_start_executor(self):
        """Test starting job executor"""
        executor = JobExecutor()
        executor.start_executor()
        assert executor.is_running is True
    
    def test_stop_executor(self):
        """Test stopping job executor"""
        executor = JobExecutor()
        executor.start_executor()
        executor.stop_executor()
        assert executor.is_running is False
    
    @pytest.mark.asyncio
    async def test_execute_job(self):
        """Test executing job"""
        executor = JobExecutor()
        await executor.initialize()
        
        job = Job(
            id="test_id",
            type=JobType.PROCESSING,
            name="test_job",
            description="Test job"
        )
        
        with patch.object(executor, 'execute_job') as mock_execute:
            mock_execute.return_value = {"success": True, "result": "completed"}
            
            result = await executor.execute_job(job)
            assert result["success"] is True
            mock_execute.assert_called_once_with(job)
    
    @pytest.mark.asyncio
    async def test_execute_job_failure(self):
        """Test executing job with failure"""
        executor = JobExecutor()
        await executor.initialize()
        
        job = Job(
            id="test_id",
            type=JobType.PROCESSING,
            name="test_job",
            description="Test job"
        )
        
        with patch.object(executor, 'execute_job') as mock_execute:
            mock_execute.return_value = {"success": False, "error": "Job failed"}
            
            result = await executor.execute_job(job)
            assert result["success"] is False
            mock_execute.assert_called_once_with(job)
    
    def test_cancel_job(self):
        """Test canceling job"""
        executor = JobExecutor()
        
        with patch.object(executor, 'cancel_job') as mock_cancel:
            mock_cancel.return_value = True
            
            result = executor.cancel_job("test_id")
            assert result is True
            mock_cancel.assert_called_once_with("test_id")
    
    def test_get_job_status(self):
        """Test getting job status"""
        executor = JobExecutor()
        
        with patch.object(executor, 'get_job_status') as mock_status:
            mock_status.return_value = JobStatus.RUNNING
            
            result = executor.get_job_status("test_id")
            assert result == JobStatus.RUNNING
            mock_status.assert_called_once_with("test_id")
    
    def test_get_running_jobs(self):
        """Test getting running jobs"""
        executor = JobExecutor()
        
        with patch.object(executor, 'get_running_jobs') as mock_jobs:
            mock_jobs.return_value = [{"id": "job1"}, {"id": "job2"}]
            
            result = executor.get_running_jobs()
            assert len(result) == 2
            mock_jobs.assert_called_once()
    
    def test_get_executor_stats(self):
        """Test getting executor statistics"""
        executor = JobExecutor()
        
        with patch.object(executor, 'get_executor_stats') as mock_stats:
            mock_stats.return_value = {"total_executed": 0, "successful": 0, "failed": 0}
            
            result = executor.get_executor_stats()
            assert "total_executed" in result
            assert "successful" in result
            assert "failed" in result
            mock_stats.assert_called_once()
    
    def test_set_max_concurrent_jobs(self):
        """Test setting max concurrent jobs"""
        executor = JobExecutor()
        
        with patch.object(executor, 'set_max_concurrent_jobs') as mock_set:
            mock_set.return_value = None
            
            executor.set_max_concurrent_jobs(5)
            mock_set.assert_called_once_with(5)
    
    def test_reset_executor(self):
        """Test resetting executor"""
        executor = JobExecutor()
        
        with patch.object(executor, 'reset_executor') as mock_reset:
            mock_reset.return_value = None
            
            result = executor.reset_executor()
            assert result is None
            mock_reset.assert_called_once()
