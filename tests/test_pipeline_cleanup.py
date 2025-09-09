"""Tests for background job cleanup logic."""

from datetime import datetime, timedelta
from unittest.mock import patch

from streamline_vpn.jobs.pipeline_cleanup import cleanup_processing_jobs


def test_cleanup_function_directly():
    """
    Test the cleanup_processing_jobs function directly to ensure its logic is correct.
    """
    now = datetime.now()

    # Mock data for the processing_jobs dictionary
    test_jobs = {
        "old_completed_job": {
            "status": "completed",
            "completed_at": (now - timedelta(hours=2)).isoformat(),
        },
        "recent_completed_job": {
            "status": "completed",
            "completed_at": (now - timedelta(seconds=1)).isoformat(),
        },
        "running_job": {
            "status": "running",
            "started_at": now.isoformat(),
        },
        "failed_job_old": {
            "status": "failed",
            "completed_at": (now - timedelta(days=1)).isoformat(),
        },
    }

    # Use patch to control the state of processing_jobs for this test
    with patch("streamline_vpn.jobs.pipeline_cleanup.processing_jobs", test_jobs):
        removed_count = cleanup_processing_jobs()

        # Verify the number of removed jobs
        assert removed_count == 2

        # Verify the state of the patched dictionary
        assert len(test_jobs) == 2
        assert "old_completed_job" not in test_jobs
        assert "failed_job_old" not in test_jobs
        assert "recent_completed_job" in test_jobs
        assert "running_job" in test_jobs

