"""
Job Executor
============

Handles job execution logic.
"""

import asyncio
from typing import Dict, Any, Callable

from .models import Job, JobType
from ..utils.logging import get_logger

logger = get_logger(__name__)


class JobExecutor:
    """Handles job execution logic."""

    def __init__(self, job_manager):
        """Initialize job executor.

        Args:
            job_manager: Parent job manager instance
        """
        self.job_manager = job_manager
        self.job_handlers: Dict[JobType, Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default job handlers."""
        self.job_handlers = {
            JobType.PROCESS_CONFIGURATIONS: (
                self._handle_process_configurations
            ),
            JobType.DISCOVER_SOURCES: self._handle_discover_sources,
            JobType.UPDATE_SOURCES: self._handle_update_sources,
            JobType.CLEAR_CACHE: self._handle_clear_cache,
            JobType.EXPORT_CONFIGURATIONS: (
                self._handle_export_configurations
            ),
        }

    async def execute_job(self, job: Job) -> None:
        """Execute a job.

        Args:
            job: Job to execute
        """
        try:
            # Get job handler
            handler = self.job_handlers.get(job.type)
            if not handler:
                raise ValueError(f"No handler for job type {job.type.value}")

            # Run the job
            result = await handler(job)

            # Mark as completed
            job.complete(result)
            self.job_manager.persistence.save_job(job)

            logger.info("Completed job %s", job.id)

        except asyncio.CancelledError:
            # Job was cancelled
            job.cancel()
            self.job_manager.persistence.save_job(job)
            logger.info("Cancelled job %s", job.id)

        except Exception as e:
            # Job failed
            job.fail(str(e))
            self.job_manager.persistence.save_job(job)
            logger.error("Job %s failed: %s", job.id, e, exc_info=True)

    async def _handle_process_configurations(self, job: Job) -> Dict[str, Any]:
        """Handle process configurations job."""
        from ..core.merger import StreamlineVPNMerger

        merger = StreamlineVPNMerger()

        # Update progress
        job.update_progress(10)
        self.job_manager.persistence.save_job(job)

        # Process configurations
        results = await merger.process_all(
            output_dir=job.parameters.get("output_dir", "output"),
            formats=job.parameters.get("formats", ["json", "clash"]),
        )

        # Update progress
        job.update_progress(90)
        self.job_manager.persistence.save_job(job)

        return results

    async def _handle_discover_sources(self, job: Job) -> Dict[str, Any]:
        """Handle discover sources job."""
        from ..discovery.manager import DiscoveryManager

        discovery = DiscoveryManager()

        # Update progress
        job.update_progress(20)
        self.job_manager.persistence.save_job(job)

        # Discover sources
        sources = await discovery.discover_sources()

        # Update progress
        job.update_progress(80)
        self.job_manager.persistence.save_job(job)

        return {"discovered_sources": sources, "count": len(sources)}

    async def _handle_update_sources(self, job: Job) -> Dict[str, Any]:
        """Handle update sources job."""
        from ..core.merger import StreamlineVPNMerger

        merger = StreamlineVPNMerger()

        # Update progress
        job.update_progress(30)
        self.job_manager.persistence.save_job(job)

        # Update sources
        sources = await merger.source_manager.get_active_sources()

        # Update progress
        job.update_progress(70)
        self.job_manager.persistence.save_job(job)

        return {"updated_sources": sources, "count": len(sources)}

    async def _handle_clear_cache(self, job: Job) -> Dict[str, Any]:
        """Handle clear cache job."""
        from ..core.merger import StreamlineVPNMerger

        merger = StreamlineVPNMerger()

        # Update progress
        job.update_progress(50)
        self.job_manager.persistence.save_job(job)

        # Clear cache
        await merger.clear_cache()

        return {"message": "Cache cleared successfully"}

    async def _handle_export_configurations(self, job: Job) -> Dict[str, Any]:
        """Handle export configurations job."""
        from ..core.merger import StreamlineVPNMerger

        merger = StreamlineVPNMerger()

        # Update progress
        job.update_progress(20)
        self.job_manager.persistence.save_job(job)

        # Get configurations
        configs = await merger.get_configurations()

        # Update progress
        job.update_progress(60)
        self.job_manager.persistence.save_job(job)

        # Export configurations
        output_dir = job.parameters.get("output_dir", "output")
        formats = job.parameters.get("formats", ["json", "clash"])

        merger.save_results(output_dir)

        return {
            "exported_configurations": len(configs),
            "output_dir": output_dir,
            "formats": formats,
        }
