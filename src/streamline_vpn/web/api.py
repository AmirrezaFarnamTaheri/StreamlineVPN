"""
FastAPI Web API
===============

FastAPI-based REST API for StreamlineVPN.
"""

import asyncio
import os
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import python_multipart  # noqa: F401
from pydantic import BaseModel

from ..core.merger import StreamlineVPNMerger
from ..jobs.pipeline_cleanup import (
    cleanup_processing_jobs,
    cleanup_processing_jobs_periodically,
    processing_jobs,
)
from ..models.formats import OutputFormat
from ..settings import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


# --- Pydantic Models ---
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime: float


class PipelineRequest(BaseModel):
    config_path: str = "config/sources.yaml"
    output_dir: str = "output"
    formats: List[OutputFormat] = [OutputFormat.JSON, OutputFormat.CLASH]


class AddSourceRequest(BaseModel):
    url: str


class BlacklistRequest(BaseModel):
    reason: Optional[str] = None


# --- Dependency Injection ---
async def get_merger(request: Request) -> StreamlineVPNMerger:
    """Dependency to get the shared StreamlineVPNMerger instance."""
    if not hasattr(request.app.state, "merger") or not request.app.state.merger:
        logger.error("Merger instance not available on app state.")
        raise HTTPException(
            status_code=503, detail="Service not initialized"
        )
    return request.app.state.merger


# --- Application Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown events."""
    logger.info("API is starting up...")
    # Initialize and store the merger instance on startup
    try:
        app.state.merger = StreamlineVPNMerger()
        await app.state.merger.initialize()
        logger.info("StreamlineVPNMerger initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize StreamlineVPNMerger: {e}", exc_info=True)
        app.state.merger = None

    # Start background cleanup task
    app.state.cleanup_task = asyncio.create_task(
        cleanup_processing_jobs_periodically()
    )

    start_time = datetime.now()
    app.state.start_time = start_time

    try:
        yield
    finally:
        # Shutdown
        logger.info("API is shutting down...")
        task = getattr(app.state, "cleanup_task", None)
        if task:
            task.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=2)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass

        merger_instance = getattr(app.state, "merger", None)
        if merger_instance:
            await merger_instance.shutdown()
            logger.info("StreamlineVPNMerger shut down successfully.")


# --- App Factory ---
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="StreamlineVPN API",
        description="Enterprise VPN Configuration Aggregator API",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add CORS middleware
    cors_settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_settings.allowed_origins,
        allow_credentials=cors_settings.allow_credentials,
        allow_methods=cors_settings.allowed_methods,
        allow_headers=cors_settings.allowed_headers,
    )

    # --- Exception Handlers ---
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Return HTTP 400 for validation errors with clearer messages."""
        # Custom logic to provide more helpful error messages
        # ... (implementation from original code)
        return JSONResponse(status_code=400, content={"detail": exc.errors()})

    # --- Root and Health Endpoints ---
    @app.get("/", response_model=Dict[str, str], tags=["General"])
    async def root():
        """Root endpoint providing basic API information."""
        return {
            "message": "Welcome to the StreamlineVPN API",
            "version": "2.0.0",
            "docs": app.docs_url,
        }

    @app.get("/health", response_model=HealthResponse, tags=["General"])
    async def health(request: Request):
        """Health check endpoint."""
        uptime = (datetime.now() - request.app.state.start_time).total_seconds()
        return HealthResponse(
            status="healthy" if request.app.state.merger else "degraded",
            timestamp=datetime.now().isoformat(),
            version=app.version,
            uptime=uptime,
        )

    # --- Version 1 API Router ---
    router = APIRouter(prefix="/api/v1", tags=["v1"])

    def update_job_progress(job_id: str, progress: int, message: str) -> None:
        if job_id in processing_jobs:
            processing_jobs[job_id]["progress"] = progress
            processing_jobs[job_id]["message"] = message

    # --- Pipeline Endpoints ---
    @router.post("/pipeline/run", status_code=status.HTTP_202_ACCEPTED)
    async def run_pipeline(
        request: PipelineRequest,
        background_tasks: BackgroundTasks,
        merger_instance: StreamlineVPNMerger = Depends(get_merger),
    ) -> Dict[str, Any]:
        """Run the VPN configuration pipeline in the background."""
        config_file = Path(request.config_path)
        if not config_file.is_file():
            raise HTTPException(status_code=404, detail=f"Config not found: {config_file}")

        job_id = str(uuid.uuid4())
        processing_jobs[job_id] = {
            "status": "queued",
            "progress": 0,
            "message": "Pipeline run queued",
            "started_at": datetime.now().isoformat(),
        }

        async def process_async():
            try:
                update_job_progress(job_id, 10, "Initializing merger...")
                # The main merger instance is already initialized, can create a new one or reuse
                # For simplicity, we create a new one for the job not to interfere
                local_merger = StreamlineVPNMerger(config_path=str(config_file))
                await local_merger.initialize()

                update_job_progress(job_id, 50, "Processing configurations...")
                formats = [fmt.value for fmt in request.formats]
                result = await local_merger.process_all(
                    output_dir=request.output_dir, formats=formats
                )

                # Update main merger instance with the new data
                app.state.merger = local_merger

                processing_jobs[job_id].update({
                    "status": "completed",
                    "progress": 100,
                    "message": "Pipeline completed successfully",
                    "result": result,
                    "completed_at": datetime.now().isoformat(),
                })
            except Exception as e:
                logger.error(f"Pipeline job {job_id} failed: {e}", exc_info=True)
                processing_jobs[job_id].update({
                    "status": "failed",
                    "error": str(e),
                    "completed_at": datetime.now().isoformat(),
                })

        background_tasks.add_task(process_async)
        return {"job_id": job_id, "status": "accepted"}

    @router.get("/pipeline/status/{job_id}", status_code=status.HTTP_200_OK)
    async def get_pipeline_status(job_id: str) -> Dict[str, Any]:
        """Return status of a background pipeline job."""
        if job_id not in processing_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        return processing_jobs[job_id]

    @router.post("/pipeline/cleanup", status_code=status.HTTP_200_OK)
    async def manual_pipeline_cleanup() -> Dict[str, Any]:
        """Trigger cleanup of old pipeline jobs manually."""
        removed_count = cleanup_processing_jobs()
        return {"removed_count": removed_count, "remaining_count": len(processing_jobs)}

    # --- Data Endpoints ---
    @router.get("/statistics", status_code=status.HTTP_200_OK)
    async def api_v1_statistics(
        merger_instance: StreamlineVPNMerger = Depends(get_merger),
    ) -> Dict[str, Any]:
        """Expose processing statistics."""
        return await merger_instance.get_statistics()

    @router.get("/configurations", status_code=status.HTTP_200_OK)
    async def api_v1_configurations(
        protocol: Optional[str] = None,
        location: Optional[str] = None,
        min_quality: float = 0.0,
        limit: int = 100,
        offset: int = 0,
        merger_instance: StreamlineVPNMerger = Depends(get_merger),
    ) -> Dict[str, Any]:
        """Return processed configurations with filtering and pagination."""
        configs = await merger_instance.get_configurations(
            protocol=protocol, location=location, min_quality=min_quality
        )
        total = len(configs)
        paginated_configs = configs[offset : offset + limit]
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "configurations": [c.to_dict() for c in paginated_configs],
        }

    # --- Source Management Endpoints ---
    @router.get("/sources", status_code=status.HTTP_200_OK)
    async def api_v1_sources(
        merger_instance: StreamlineVPNMerger = Depends(get_merger),
    ) -> Dict[str, Any]:
        """Return information about configured sources."""
        if not merger_instance.source_manager:
            return {"sources": []}
        return {"sources": merger_instance.source_manager.get_source_statistics()}

    @router.post("/sources", status_code=status.HTTP_201_CREATED)
    async def api_v1_add_source(
        request: AddSourceRequest,
        merger_instance: StreamlineVPNMerger = Depends(get_merger),
    ) -> Dict[str, Any]:
        """Add a new source to the manager."""
        try:
            await merger_instance.source_manager.add_source(request.url)
            return {"status": "success", "message": f"Source added: {request.url}"}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/sources/blacklist", status_code=status.HTTP_200_OK)
    async def blacklist_source(
        source_url: str,
        request: BlacklistRequest,
        merger_instance: StreamlineVPNMerger = Depends(get_merger),
    ):
        """Blacklist a source."""
        await merger_instance.source_manager.blacklist_source(source_url, request.reason)
        return {"message": f"Source {source_url} blacklisted"}

    @router.delete("/sources/blacklist/{source_url}", status_code=status.HTTP_200_OK)
    async def whitelist_source(
        source_url: str,
        merger_instance: StreamlineVPNMerger = Depends(get_merger),
    ):
        """Remove source from blacklist (whitelist)."""
        await merger_instance.source_manager.whitelist_source(source_url)
        return {"message": f"Source {source_url} whitelisted"}

    # --- Admin & Management Endpoints ---
    @router.post("/cache/clear", status_code=status.HTTP_200_OK)
    async def clear_cache(merger_instance: StreamlineVPNMerger = Depends(get_merger)):
        """Clear all caches."""
        await merger_instance.clear_cache()
        return {"message": "Cache cleared successfully"}

    @router.get("/config/runtime", status_code=status.HTTP_200_OK)
    async def get_runtime_configuration() -> Dict[str, Any]:
        """Dump current runtime configuration (sanitized)."""
        settings = get_settings()
        return {
            "fetcher": settings.fetcher.model_dump(),
            "security": settings.security.model_dump(),
            "supported_protocol_prefixes": settings.supported_protocol_prefixes,
        }

    @router.post("/config/reload", status_code=status.HTTP_200_OK)
    async def reload_runtime_configuration(
        request: Request,
        overrides: Optional[Dict[str, Any]] = Body(None),
    ):
        """Reload runtime configuration from environment variables."""
        if overrides:
            for k, v in overrides.items():
                if isinstance(k, str) and k.startswith("STREAMLINE_"):
                    os.environ[k] = str(v)

        get_settings.cache_clear()

        # Re-initialize merger
        if hasattr(request.app.state, "merger") and request.app.state.merger:
            await request.app.state.merger.shutdown()

        try:
            request.app.state.merger = StreamlineVPNMerger()
            await request.app.state.merger.initialize()
            return {"message": "Runtime configuration reloaded successfully"}
        except Exception as e:
            logger.error(f"Failed to reload and re-initialize merger: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to reload configuration")

    app.include_router(router)
    return app
