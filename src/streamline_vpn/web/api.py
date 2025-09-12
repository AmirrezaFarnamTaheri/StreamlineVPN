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

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    FastAPI,
    HTTPException,
    status,
)
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import python_multipart  # noqa: F401 - ensure import for starlette deprecation warning
from pydantic import BaseModel

from ..core.merger import StreamlineVPNMerger
from ..jobs.pipeline_cleanup import (
    cleanup_processing_jobs,
    cleanup_processing_jobs_periodically,
    processing_jobs,
)
from ..jobs.cleanup import startup_cleanup
from ..models.formats import OutputFormat
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


# Global merger instance and service health flag
merger: Optional[StreamlineVPNMerger] = None
start_time = datetime.now()
service_healthy: bool = True


def get_merger() -> StreamlineVPNMerger:
    """Get or create merger instance (used as a dependency)."""
    global merger
    if merger is None:
        try:
            merger = StreamlineVPNMerger()
        except Exception:
            # Surface as a predictable HTTP error for clients/tests
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not initialized",
            )
    return merger


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Application lifespan context manager with proper initialization.
    
    Handles startup and shutdown operations gracefully.
    """
    # Startup phase
    logger.info("Starting API server initialization...")
    
    try:
        # Initialize cleanup task
        app.state.cleanup_task = asyncio.create_task(
            cleanup_processing_jobs_periodically()
        )
        
        # Clean up stale jobs
        await startup_cleanup()
        
        # Initialize merger with proper error handling
        global service_healthy, merger
        try:
            merger = StreamlineVPNMerger()
            if hasattr(merger, "initialize"):
                await merger.initialize()
            service_healthy = True
            logger.info("API server initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize merger: %s", e)
            service_healthy = False
            merger = None
            
        yield
        
    finally:
        # Shutdown phase
        logger.info("Shutting down API server...")
        if app.state.cleanup_task:
            app.state.cleanup_task.cancel()
            try:
                await asyncio.wait_for(app.state.cleanup_task, timeout=2)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
        
        if merger and hasattr(merger, "shutdown"):
            await merger.shutdown()


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="StreamlineVPN API",
        description="Enterprise VPN Configuration Aggregator API",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=_lifespan,
    )

    # Add CORS middleware
    try:
        cors_settings = get_settings()
        allow_origins = cors_settings.allowed_origins
        allow_credentials = cors_settings.allow_credentials
        allow_methods = cors_settings.allowed_methods
        allow_headers = cors_settings.allowed_headers
    except Exception:
        # Fallback to permissive defaults if env parsing fails in test envs
        allow_origins = ["*"]
        allow_credentials = True
        allow_methods = ["*"]
        allow_headers = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request, exc: RequestValidationError
    ) -> JSONResponse:
        """Return HTTP 400 for validation errors with clearer messages."""
        unsupported: List[str] = []
        for err in exc.errors()[:20]:
            loc = err.get("loc", [])
            if "formats" in loc:
                val = err.get("ctx", {}).get("enum_values") or err.get("input")
                if isinstance(val, list):
                    unsupported.extend(map(str, val))
                elif val is not None:
                    unsupported.append(str(val))
        if unsupported:
            detail = f"Unsupported formats: {', '.join(unsupported[:10])}"
        else:
            parts = []
            for e in exc.errors()[:20]:
                loc_str = ".".join(map(str, e.get("loc", [])))
                msg = e.get("msg", "invalid")
                parts.append(f"{loc_str}: {msg}")
            detail = "; ".join(parts)
            if len(detail) > 1024:
                detail = detail[:1021] + "..."
        return JSONResponse(status_code=400, content={"detail": detail})

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException) -> JSONResponse:
        """Uniform HTTPException payload shape."""
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception) -> JSONResponse:
        """Catch-all to avoid leaking stack traces to clients."""
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    # Lifespan now manages startup/shutdown

    @app.get("/", response_model=Dict[str, str])
    async def root():
        """Root endpoint."""
        return {
            "message": "StreamlineVPN API",
            "version": "2.0.0",
            "docs": "/docs",
        }

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """Health check endpoint for monitoring and load balancer health checks.
        
        Provides comprehensive health status information including service state,
        uptime, and version information for monitoring systems.
        
        Returns:
            HealthResponse object containing:
                - status: Current service status ("healthy" or "degraded")
                - timestamp: Current timestamp in ISO format
                - version: API version string
                - uptime: Service uptime in seconds
        
        Example:
            >>> response = await health()
            >>> print(response.status)
            "healthy"
            >>> print(response.uptime)
            3600.5
        """
        uptime = (datetime.now() - start_time).total_seconds()
        return HealthResponse(
            status="healthy" if service_healthy else "degraded",
            timestamp=datetime.now().isoformat(),
            version="2.0.0",
            uptime=uptime,
        )

    @app.post("/process", response_model=ProcessingResponse)
    async def process_configurations(
        request: ProcessingRequest, background_tasks: BackgroundTasks
    ) -> ProcessingResponse:
        """Process VPN configurations from configured sources.
        
        Initiates the complete VPN configuration processing pipeline including
        fetching from sources, parsing, validation, deduplication, and output
        generation in specified formats.
        
        Args:
            request: ProcessingRequest containing:
                - output_dir: Directory to save output files
                - formats: List of output formats (json, clash, singbox, etc.)
                - max_concurrent: Maximum concurrent processing tasks
            background_tasks: FastAPI background tasks for async operations
        
        Returns:
            ProcessingResponse containing:
                - success: Boolean indicating if processing succeeded
                - message: Human-readable status message
                - job_id: Optional job identifier for tracking
                - statistics: Optional processing statistics
        
        Raises:
            HTTPException: If processing fails
                - 500: Internal server error during processing
        
        Example:
            >>> request = ProcessingRequest(
            ...     output_dir="output",
            ...     formats=["json", "clash"],
            ...     max_concurrent=50
            ... )
            >>> response = await process_configurations(request, background_tasks)
            >>> print(response.success)
            True
        """
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

    @app.post("/pipeline/run")
    async def run_pipeline_legacy(
        background_tasks: BackgroundTasks,
        config_path: str = Body("config/sources.yaml"),
        output_dir: str = Body("output"),
        formats: List[str] = Body(["json", "clash", "singbox"])
    ):
        """Legacy pipeline run endpoint for backward compatibility."""
        try:
            # Validate formats
            allowed_formats = {"json", "clash", "singbox", "base64", "raw", "csv"}
            invalid_formats = set(formats) - allowed_formats
            if invalid_formats:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid formats: {', '.join(invalid_formats)}"
                )
            
            # Check config file exists
            config_file = Path(config_path)
            if not config_file.exists():
                # Try fallback paths
                fallback_paths = [
                    Path("config/sources.unified.yaml"),
                    Path("config/sources.yaml"),
                    Path(__file__).parent.parent.parent / "config" / "sources.yaml"
                ]
                for fallback in fallback_paths:
                    if fallback.exists():
                        config_file = fallback
                        break
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Configuration file not found: {config_path}"
                    )
            
            # Create output directory
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Generate job ID
            job_id = str(uuid.uuid4())
            
            # Initialize job status
            processing_jobs[job_id] = {
                "status": "queued",
                "progress": 0,
                "message": "Job queued for processing",
                "started_at": datetime.now().isoformat(),
            }
            
            async def run_async():
                try:
                    processing_jobs[job_id] = {
                        "status": "running",
                        "progress": 5,
                        "message": "Starting pipeline...",
                        "started_at": datetime.now().isoformat(),
                    }
                    
                    # Actually run the pipeline
                    merger = get_merger()
                    results = await merger.process_all(
                        output_dir=output_dir, formats=formats
                    )
                    
                    processing_jobs[job_id] = {
                        "status": "completed",
                        "progress": 100,
                        "message": "Pipeline completed successfully",
                        "completed_at": datetime.now().isoformat(),
                        "result": results
                    }
                    
                except Exception as e:
                    processing_jobs[job_id] = {
                        "status": "failed",
                        "error": str(e),
                        "message": f"Pipeline failed: {str(e)}",
                        "completed_at": datetime.now().isoformat(),
                    }
            
            # Start async task
            background_tasks.add_task(run_async)
            
            return {
                "status": "success",
                "message": "Pipeline started successfully",
                "job_id": job_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error starting pipeline: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
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
    async def get_configurations() -> Dict[str, Any]:
        """Get processed VPN configurations from the merger.
        
        Retrieves all currently processed VPN configurations from the merger service
        and returns them in a structured format with metadata.
        
        Returns:
            Dictionary containing:
                - count: Number of configurations available
                - configurations: List of configuration dictionaries
        
        Raises:
            HTTPException: If configurations cannot be retrieved
                - 500: Internal server error during retrieval
        
        Example:
            >>> response = await get_configurations()
            >>> print(response["count"])
            150
            >>> print(len(response["configurations"]))
            150
        """
        try:
            merger = get_merger()
            configs = await merger.get_configurations()
            return {
                "count": len(configs),
                "configurations": [config.to_dict() if hasattr(config, 'to_dict') else config for config in configs],
            }
        except Exception as e:
            logger.error("Configurations error: %s", e)
            # Return empty configurations on error
            return {
                "count": 0,
                "configurations": []
            }

    @app.get("/sources")
    async def get_sources():
        """Get source information."""
        try:
            merger = get_merger()
            if hasattr(merger, 'source_manager') and merger.source_manager:
                source_stats = merger.source_manager.get_source_statistics()
                return source_stats
            else:
                return {
                    "total_sources": 0,
                    "active_sources": 0,
                    "blacklisted_sources": 0,
                    "tier_distribution": {},
                    "average_reputation": 0.0,
                    "top_sources": []
                }
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
            if hasattr(merger, 'source_manager') and merger.source_manager:
                merger.source_manager.blacklist_source(source_url, reason)
                return {"message": f"Source {source_url} blacklisted"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Source manager not available",
                )
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
            if hasattr(merger, 'source_manager') and merger.source_manager:
                merger.source_manager.whitelist_source(source_url)
                return {"message": f"Source {source_url} whitelisted"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Source manager not available",
                )
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

    @app.get("/jobs/{job_id}")
    async def get_job_status(job_id: str):
        """Get job status."""
        if job_id not in processing_jobs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        return processing_jobs[job_id]

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
        formats: List[OutputFormat] = [
            OutputFormat.JSON,
            OutputFormat.CLASH,
        ]

    @router.post("/pipeline/run", status_code=status.HTTP_202_ACCEPTED)
    async def run_pipeline(
        background_tasks: BackgroundTasks, request: PipelineRequest
    ) -> Dict[str, Any]:
        """Run the VPN configuration pipeline in the background."""
        try:
            config_file = Path(request.config_path)
            if not config_file.is_file():
                # Fallbacks for typical dev paths
                fallback_paths = [
                    Path("config/sources.unified.yaml"),
                    Path("config/sources.yaml"),
                ]
                for fb in fallback_paths:
                    if fb.is_file():
                        config_file = fb
                        break
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=(
                            f"Configuration file not found: {request.config_path}"
                        ),
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
                    local_merger = StreamlineVPNMerger(
                        config_path=str(config_file)
                    )
                    await local_merger.initialize()
                    update_job_progress(
                        job_id, 50, "Processing configurations..."
                    )
                    formats = [fmt.value for fmt in request.formats]
                    result = await local_merger.process_all(
                        output_dir=request.output_dir, formats=formats
                    )
                    merger = local_merger
                    processing_jobs[job_id]["status"] = "completed"
                    update_job_progress(
                        job_id, 100, "Pipeline completed successfully"
                    )
                    processing_jobs[job_id]["result"] = result
                    processing_jobs[job_id][
                        "completed_at"
                    ] = datetime.now().isoformat()
                except Exception as exc:  # pragma: no cover - logging path
                    logger.error("Pipeline job %s failed: %s", job_id, exc)
                    processing_jobs[job_id]["status"] = "failed"
                    processing_jobs[job_id]["error"] = str(exc)
                    processing_jobs[job_id][
                        "completed_at"
                    ] = datetime.now().isoformat()
                    update_job_progress(job_id, 100, str(exc))

            background_tasks.add_task(process_async)
            return {"status": "accepted", "job_id": job_id}
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
    async def api_v1_statistics(merger: StreamlineVPNMerger = Depends(get_merger)) -> Dict[str, Any]:
        """Return statistics as provided by the merger (test-friendly)."""
        return await merger.get_statistics()

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
        configs = configs[offset:offset + limit]
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
        
        if hasattr(merger, 'source_manager') and merger.source_manager and hasattr(merger.source_manager, 'sources'):
            for src in merger.source_manager.sources.values():
                enabled = getattr(src, "enabled", True)
                last_check = getattr(src, "last_check", None)
                last_update = (
                    last_check.isoformat()
                    if isinstance(last_check, datetime)
                    else None
                )
                source_infos.append(
                    {
                        "url": getattr(src, "url", None),
                        "status": "active" if enabled else "disabled",
                        "configs": getattr(src, "avg_config_count", 0),
                        "last_update": last_update,
                        "success_rate": getattr(src, "reputation_score", 0.0),
                    }
                )
        else:
            # Return empty sources if source manager not available
            source_infos = []
            
        return {"sources": source_infos}

    class AddSourceRequest(BaseModel):
        url: str

    @router.post("/sources/add")
    async def api_v1_add_source(request: AddSourceRequest) -> Dict[str, Any]:
        """Add a new source to the manager."""
        merger = get_merger()
        url = request.url.strip()
        try:
            if hasattr(merger, 'source_manager') and merger.source_manager:
                await merger.source_manager.add_source(url)
                return {"status": "success", "message": f"Source added: {url}"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Source manager not available",
                )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:  # pragma: no cover - unexpected
            logger.error("Error adding source: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add source",
            )

    # Compatibility route expected by tests: POST /api/v1/sources with JSON body
    @router.post("/sources", status_code=status.HTTP_201_CREATED)
    async def api_v1_add_source_direct(
        request: AddSourceRequest,
        merger_dep: StreamlineVPNMerger = Depends(get_merger),
    ) -> Dict[str, Any]:
        try:
            await merger_dep.source_manager.add_source(request.url)
            return {"status": "success", "message": f"Source {request.url} added"}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:  # pragma: no cover - unexpected
            logger.error("Error adding source: %s", exc)
            raise HTTPException(status_code=500, detail="Failed to add source")

    app.include_router(router)

    return app
