"""
Focused tests for Job Models
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.jobs.models import Job, JobStatus, JobType


class TestJob:
    """Test Job class"""
    
    def test_job_creation(self):
        """Test creating job"""
        job = Job(
            id="test_id",
            type=JobType.PROCESSING,
            name="test_job",
            description="Test job description"
        )
        
        assert job.id == "test_id"
        assert job.type == JobType.PROCESSING
        assert job.name == "test_job"
        assert job.description == "Test job description"
        assert job.status == JobStatus.PENDING
        assert job.created_at is not None
        assert job.updated_at is not None
    
    def test_job_with_optional_fields(self):
        """Test creating job with optional fields"""
        job = Job(
            id="test_id",
            type=JobType.PROCESSING,
            name="test_job",
            description="Test job description",
            status=JobStatus.RUNNING,
            priority=5,
            metadata={"key": "value"}
        )
        
        assert job.status == JobStatus.RUNNING
        assert job.priority == 5
        assert job.metadata == {"key": "value"}
    
    def test_job_status_update(self):
        """Test updating job status"""
        job = Job(
            id="test_id",
            type=JobType.PROCESSING,
            name="test_job",
            description="Test job description"
        )
        
        job.status = JobStatus.RUNNING
        assert job.status == JobStatus.RUNNING
        assert job.updated_at is not None
    
    def test_job_to_dict(self):
        """Test converting job to dictionary"""
        job = Job(
            id="test_id",
            type=JobType.PROCESSING,
            name="test_job",
            description="Test job description"
        )
        
        job_dict = job.to_dict()
        assert isinstance(job_dict, dict)
        assert job_dict["id"] == "test_id"
        assert job_dict["type"] == JobType.PROCESSING
        assert job_dict["name"] == "test_job"
        assert job_dict["status"] == JobStatus.PENDING
    
    def test_job_from_dict(self):
        """Test creating job from dictionary"""
        job_data = {
            "id": "test_id",
            "type": JobType.PROCESSING,
            "name": "test_job",
            "description": "Test job description",
            "status": JobStatus.RUNNING,
            "priority": 3,
            "metadata": {"key": "value"}
        }
        
        job = Job.from_dict(job_data)
        assert job.id == "test_id"
        assert job.type == JobType.PROCESSING
        assert job.name == "test_job"
        assert job.status == JobStatus.RUNNING
        assert job.priority == 3
        assert job.metadata == {"key": "value"}


class TestJobStatus:
    """Test JobStatus enum"""
    
    def test_job_status_values(self):
        """Test job status enum values"""
        assert JobStatus.PENDING == "pending"
        assert JobStatus.RUNNING == "running"
        assert JobStatus.COMPLETED == "completed"
        assert JobStatus.FAILED == "failed"
        assert JobStatus.CANCELLED == "cancelled"
    
    def test_job_status_enum_membership(self):
        """Test job status enum membership"""
        assert "pending" in [e.value for e in JobStatus]
        assert "running" in [e.value for e in JobStatus]
        assert "completed" in [e.value for e in JobStatus]
        assert "failed" in [e.value for e in JobStatus]
        assert "cancelled" in [e.value for e in JobStatus]


class TestJobType:
    """Test JobType enum"""
    
    def test_job_type_values(self):
        """Test job type enum values"""
        assert JobType.PROCESSING == "processing"
        assert JobType.CLEANUP == "cleanup"
        assert JobType.MAINTENANCE == "maintenance"
        assert JobType.BACKUP == "backup"
        assert JobType.SYNC == "sync"
    
    def test_job_type_enum_membership(self):
        """Test job type enum membership"""
        assert "processing" in [e.value for e in JobType]
        assert "process_configurations" in [e.value for e in JobType]
        assert "discover_sources" in [e.value for e in JobType]
        assert "update_sources" in [e.value for e in JobType]
        assert "clear_cache" in [e.value for e in JobType]
