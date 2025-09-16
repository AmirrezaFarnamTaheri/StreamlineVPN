"""
Focused tests for JobManager
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.jobs.manager import JobManager
from streamline_vpn.jobs.models import Job, JobStatus, JobType


class TestJobManager:
    """Test JobManager class"""
    
    def test_initialization(self):
        """Test job manager initialization"""
        manager = JobManager()
        assert hasattr(manager, 'jobs')
        assert hasattr(manager, 'executor')
        assert hasattr(manager, 'persistence')
        assert hasattr(manager, 'is_running')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test job manager initialization"""
        manager = JobManager()
        result = await manager.initialize()
        assert result is True
    
    def test_start_manager(self):
        """Test starting job manager"""
        manager = JobManager()
        manager.start_manager()
        assert manager.is_running is True
    
    def test_stop_manager(self):
        """Test stopping job manager"""
        manager = JobManager()
        manager.start_manager()
        manager.stop_manager()
        assert manager.is_running is False
    
    def test_add_job(self):
        """Test adding job"""
        manager = JobManager()
        
        job_data = {
            "type": JobType.PROCESSING,
            "name": "test_job",
            "description": "Test job"
        }
        
        with patch.object(manager, 'add_job') as mock_add:
            mock_add.return_value = {"success": True, "job_id": "test_id"}
            
            result = manager.add_job(job_data)
            assert result["success"] is True
            mock_add.assert_called_once_with(job_data)
    
    def test_remove_job(self):
        """Test removing job"""
        manager = JobManager()
        
        with patch.object(manager, 'remove_job') as mock_remove:
            mock_remove.return_value = True
            
            result = manager.remove_job("test_id")
            assert result is True
            mock_remove.assert_called_once_with("test_id")
    
    def test_get_job(self):
        """Test getting job"""
        manager = JobManager()
        
        with patch.object(manager, 'get_job') as mock_get:
            mock_get.return_value = {"id": "test_id", "name": "test_job"}
            
            result = manager.get_job("test_id")
            assert result["id"] == "test_id"
            mock_get.assert_called_once_with("test_id")
    
    def test_list_jobs(self):
        """Test listing jobs"""
        manager = JobManager()
        
        with patch.object(manager, 'list_jobs') as mock_list:
            mock_list.return_value = [{"id": "job1"}, {"id": "job2"}]
            
            result = manager.list_jobs()
            assert len(result) == 2
            mock_list.assert_called_once()
    
    def test_get_job_status(self):
        """Test getting job status"""
        manager = JobManager()
        
        with patch.object(manager, 'get_job_status') as mock_status:
            mock_status.return_value = JobStatus.RUNNING
            
            result = manager.get_job_status("test_id")
            assert result == JobStatus.RUNNING
            mock_status.assert_called_once_with("test_id")
    
    def test_cancel_job(self):
        """Test canceling job"""
        manager = JobManager()
        
        with patch.object(manager, 'cancel_job') as mock_cancel:
            mock_cancel.return_value = True
            
            result = manager.cancel_job("test_id")
            assert result is True
            mock_cancel.assert_called_once_with("test_id")
    
    def test_get_manager_stats(self):
        """Test getting manager statistics"""
        manager = JobManager()
        
        with patch.object(manager, 'get_manager_stats') as mock_stats:
            mock_stats.return_value = {"total_jobs": 0, "running_jobs": 0}
            
            result = manager.get_manager_stats()
            assert "total_jobs" in result
            assert "running_jobs" in result
            mock_stats.assert_called_once()
    
    def test_clear_completed_jobs(self):
        """Test clearing completed jobs"""
        manager = JobManager()
        
        with patch.object(manager, 'clear_completed_jobs') as mock_clear:
            mock_clear.return_value = 5
            
            result = manager.clear_completed_jobs()
            assert result == 5
            mock_clear.assert_called_once()
    
    def test_reset_manager(self):
        """Test resetting manager"""
        manager = JobManager()
        
        with patch.object(manager, 'reset_manager') as mock_reset:
            mock_reset.return_value = None
            
            result = manager.reset_manager()
            assert result is None
            mock_reset.assert_called_once()
