"""
FastAPI Web API
===============

FastAPI-based REST API for StreamlineVPN.
"""

import os
import uuid
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Body, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from collections import Counter

from ..core.merger import StreamlineVPNMerger
from ..settings import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


# Pydantic models for API
class ProcessingRequest(BaseModel):
    config_path: Optional[str] = "config/sources.yaml"
    output_dir: Optional[str] = "output"
    formats: Optional[List[str]] = ["json", "clash"]
    max_concurrent: Optional[int] = 50


class ProcessingResponse(BaseModel):
    success: bool
    message: str
    job_id: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime: float


# Global merger instance
merger: Optional[StreamlineVPNMerger] = None
start_time = datetime.now()

# Track background processing jobs
processing_jobs: Dict[str, Any] = {}

# Retention period for completed/failed jobs
JOB_RETENTION_PERIOD = timedelta(hours=1)


def cleanup_processing_jobs(retention: timedelta = JOB_RETENTION_PERIOD) -> int:
    """Remove completed or failed jobs older than the retention period.

    Args:
        retention: Duration to keep completed/failed jobs around.

    Returns:
        Number of jobs removed.
    """

    now = datetime.now()
    to_remove: List[str] = []
    for job_id, data in processing_jobs.items():
        status = data.get("status")
        if status not in {"completed", "failed"}:
            continue
        ts_str = data.get("completed_at") or data.get("started_at")
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str)
        except Exception:  # pragma: no cover - invalid timestamp
            continue
        if ts < now - retention:
            to_remove.append(job_id)

    for job_id in to_remove:
        processing_jobs.pop(job_id, None)
    return len(to_remove)


async def _cleanup_processing_jobs_periodically() -> None:
    """Background task that periodically cleans up old jobs."""
    while True:
        await asyncio.sleep(60)
        try:
            cleanup_processing_jobs()
        except Exception:  # pragma: no cover - logging only
            logger.exception("Background job cleanup failed")


def get_merger() -> StreamlineVPNMerger:
    """Get or create merger instance."""
    global merger
    if merger is None:
        merger = StreamlineVPNMerger()
    return merger


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="StreamlineVPN API",
        description="Enterprise VPN Configuration Aggregator API",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def _startup_cleanup() -> None:
        app.state.cleanup_task = asyncio.create_task(
            _cleanup_processing_jobs_periodically()
        )

    @app.on_event("shutdown")
    async def _shutdown_cleanup() -> None:
        task = getattr(app.state, "cleanup_task", None)
        if task:
            task.cancel()
            try:
                await task
            except BaseException:  # pragma: no cover - cancellation only
                pass

    @app.get("/", response_model=Dict[str, str])
    async def root():
        """Root endpoint."""
        return {
            "message": "StreamlineVPN API",
            "version": "2.0.0",
            "docs": "/docs",
        }

    @app.get("/health", response_model=HealthResponse)
    async def health():
        """Health check endpoint."""
        uptime = (datetime.now() - start_time).total_seconds()
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="2.0.0",
            uptime=uptime,
        )

    @app.post("/process", response_model=ProcessingResponse)
    async def process_configurations(
        request: ProcessingRequest, background_tasks: BackgroundTasks
    ):
        """Process VPN configurations."""
        try:
            merger = get_merger()

            # Process configurations
            results = await merger.process_all(
                output_dir=request.output_dir, formats=request.formats
            )

            if not results.get("success", False):
                logger.error(
                    "Processing failed: %s",
                    results.get("error", "unknown error"),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Processing failed",
                )
            return ProcessingResponse(
                success=True,
                message="Processing completed successfully",
                statistics=results.get("statistics"),
            )

        except Exception as e:
            logger.error("Processing error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Processing failed",
            )

    @app.get("/statistics")
    async def get_statistics():
        """Get processing statistics."""
        try:
            merger = get_merger()
            stats = await merger.get_statistics()
            return stats
        except Exception as e:
            logger.error("Statistics error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @app.get("/configurations")
    async def get_configurations():
        """Get processed configurations."""
        try:
            merger = get_merger()
            configs = await merger.get_configurations()
            return {
                "count": len(configs),
                "configurations": [config.to_dict() for config in configs],
            }
        except Exception as e:
            logger.error("Configurations error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @app.get("/sources")
    async def get_sources():
        """Get source information."""
        try:
            merger = get_merger()
            source_stats = merger.source_manager.get_source_statistics()
            return source_stats
        except Exception as e:
            logger.error("Sources error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @app.post("/sources/{source_url}/blacklist")
    async def blacklist_source(source_url: str, reason: str = ""):
        """Blacklist a source."""
        try:
            merger = get_merger()
            merger.source_manager.blacklist_source(source_url, reason)
            return {"message": f"Source {source_url} blacklisted"}
        except Exception as e:
            logger.error("Blacklist error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @app.post("/sources/{source_url}/whitelist")
    async def whitelist_source(source_url: str):
        """Remove source from blacklist."""
        try:
            merger = get_merger()
            merger.source_manager.whitelist_source(source_url)
            return {"message": f"Source {source_url} whitelisted"}
        except Exception as e:
            logger.error("Whitelist error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @app.post("/cache/clear")
    async def clear_cache():
        """Clear all caches."""
        try:
            merger = get_merger()
            await merger.clear_cache()
            return {"message": "Cache cleared successfully"}
        except Exception as e:
            logger.error("Cache clear error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @app.get("/metrics")
    async def get_metrics():
        """Get Prometheus metrics."""
        try:
            # This would integrate with Prometheus client
            return {
                "message": "Metrics endpoint - integrate with "
                "Prometheus client"
            }
        except Exception as e:
            logger.error("Metrics error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @app.get("/config/runtime")
    async def get_runtime_configuration():
        """Dump current runtime configuration (sanitized)."""
        try:
            settings = get_settings()
            return {
                "fetcher": settings.fetcher.model_dump(),
                "security": settings.security.model_dump(),
                "supported_protocol_prefixes": (
                    settings.supported_protocol_prefixes
                ),
            }
        except Exception as e:
            logger.error("Runtime config error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @app.post("/config/reload")
    async def reload_runtime_configuration(
        overrides: Optional[Dict[str, Any]] = Body(None),
    ):
        """Reload runtime configuration by re-reading environment variables."""
        global merger
        try:
            # Apply provided overrides
            if overrides:
                for k, v in overrides.items():
                    if isinstance(k, str) and k.startswith("STREAMLINE_"):
                        os.environ[k] = str(v)

            # Clear cached settings to pick up new env
            try:
                get_settings.cache_clear()  # type: ignore[attr-defined]
            except Exception:
                pass

            # Recreate merger to pick up new settings
            if merger is not None:
                try:
                    await merger.shutdown()
                except Exception:
                    pass
                merger = None

            # Re-initialize merger with fresh settings
            merger = StreamlineVPNMerger()

            # Return the fresh settings snapshot
            settings = get_settings()
            return {
                "message": "Runtime configuration reloaded",
                "fetcher": settings.fetcher.model_dump(),
                "security": settings.security.model_dump(),
                "supported_protocol_prefixes": (
                    settings.supported_protocol_prefixes
                ),
            }
        except Exception as e:
            logger.error("Reload settings error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    # ------------------------------------------------------------------
    # Enhanced pipeline endpoints (versioned API)
    # ------------------------------------------------------------------

    router = APIRouter(prefix="/api/v1")

    def update_job_progress(job_id: str, progress: int, message: str) -> None:
        if job_id in processing_jobs:
            processing_jobs[job_id]["progress"] = progress
            processing_jobs[job_id]["message"] = message

    class PipelineRequest(BaseModel):
        config_path: str = "config/sources.yaml"
        output_dir: str = "output"
        formats: List[str] = ["json", "clash"]

    @router.post("/pipeline/run", status_code=status.HTTP_200_OK)
    async def run_pipeline(
        background_tasks: BackgroundTasks, request: PipelineRequest
    ) -> Dict[str, Any]:
        """Run the VPN configuration pipeline in the background."""
        try:
            config_file = Path(request.config_path)
            if not config_file.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Configuration file not found: {request.config_path}",
                )

            Path(request.output_dir).mkdir(parents=True, exist_ok=True)

            job_id = str(uuid.uuid4())
            processing_jobs[job_id] = {
                "status": "running",
                "progress": 0,
                "message": "Starting pipeline...",
                "started_at": datetime.now().isoformat(),
            }

            async def process_async() -> None:
                global merger
                try:
                    update_job_progress(job_id, 10, "Initializing merger...")
                    local_merger = StreamlineVPNMerger(config_path=str(config_file))
                    await local_merger.initialize()
                    update_job_progress(job_id, 50, "Processing configurations...")
                    result = await local_merger.process_all(
                        output_dir=request.output_dir, formats=request.formats
                    )
                    merger = local_merger
                    processing_jobs[job_id]["status"] = "completed"
                    update_job_progress(job_id, 100, "Pipeline completed successfully")
                    processing_jobs[job_id]["result"] = result
                    processing_jobs[job_id]["completed_at"] = datetime.now().isoformat()
                except Exception as exc:  # pragma: no cover - logging path
                    logger.error("Pipeline job %s failed: %s", job_id, exc)
                    processing_jobs[job_id]["status"] = "failed"
                    processing_jobs[job_id]["error"] = str(exc)
                    processing_jobs[job_id]["completed_at"] = datetime.now().isoformat()
                    update_job_progress(job_id, 100, str(exc))

            background_tasks.add_task(process_async)
            return {
                "status": "success",
                "message": "Pipeline started successfully",
                "job_id": job_id,
            }
        except HTTPException:
            raise
        except Exception as exc:  # pragma: no cover - unexpected
            logger.error("Error starting pipeline: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start pipeline: {exc}",
            )

    @router.get("/pipeline/status/{job_id}")
    async def get_pipeline_status(job_id: str) -> Dict[str, Any]:
        """Return status of a background pipeline job."""
        if job_id not in processing_jobs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job not found: {job_id}",
            )
        return processing_jobs[job_id]

    @router.post("/pipeline/cleanup")
    async def manual_pipeline_cleanup() -> Dict[str, Any]:
        """Trigger cleanup of old pipeline jobs manually."""
        removed = cleanup_processing_jobs()
        return {"removed": removed, "remaining": len(processing_jobs)}

    @router.get("/statistics")
    async def api_v1_statistics() -> Dict[str, Any]:
        """Expose statistics with /api/v1 prefix."""
        merger = get_merger()
        stats = await merger.get_statistics()
        configs = await merger.get_configurations()
        avg_quality = (
            sum(c.quality_score for c in configs) / len(configs)
            if configs
            else 0.0
        )
        protocol_counts = Counter(c.protocol.value for c in configs)
        location_counts = Counter(
            c.metadata.get("location", "unknown") for c in configs
        )
        return {
            "total_configs": stats.get("total_configs", 0),
            "successful_sources": stats.get("successful_sources", 0),
            "success_rate": stats.get("success_rate", 0.0),
            "avg_quality": avg_quality,
            "last_update": stats.get("end_time"),
            "protocols": dict(protocol_counts),
            "locations": dict(location_counts),
        }

    @router.get("/configurations")
    async def api_v1_configurations(
        protocol: Optional[str] = None,
        location: Optional[str] = None,
        min_quality: float = 0.0,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Return processed configurations with filtering and pagination."""
        merger = get_merger()
        configs = await merger.get_configurations()
        if protocol:
            configs = [c for c in configs if c.protocol.value == protocol]
        if location:
            configs = [
                c for c in configs if c.metadata.get("location") == location
            ]
        if min_quality > 0:
            configs = [c for c in configs if c.quality_score >= min_quality]
        total = len(configs)
        configs = configs[offset : offset + limit]
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "configurations": [c.to_dict() for c in configs],
        }

    @router.get("/sources")
    async def api_v1_sources() -> Dict[str, Any]:
        """Return information about configured sources."""
        merger = get_merger()
        source_infos = []
        for src in merger.source_manager.sources.values():
            enabled = getattr(src, "enabled", True)
            last_check = getattr(src, "last_check", None)
            last_update = last_check.isoformat() if isinstance(last_check, datetime) else None
            source_infos.append(
                {
                    "url": getattr(src, "url", None),
                    "status": "active" if enabled else "disabled",
                    "configs": getattr(src, "avg_config_count", 0),
                    "last_update": last_update,
                    "success_rate": getattr(src, "reputation_score", 0.0),
                }
            )
        return {"sources": source_infos}

    class AddSourceRequest(BaseModel):
        url: str

    @router.post("/sources/add")
    async def api_v1_add_source(request: AddSourceRequest) -> Dict[str, Any]:
        """Add a new source to the manager."""
        merger = get_merger()
        url = request.url.strip()
        try:
            await merger.source_manager.add_source(url)
            return {"status": "success", "message": f"Source added: {url}"}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:  # pragma: no cover - unexpected
            logger.error("Error adding source: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add source",
            )

    app.include_router(router)

    return app
