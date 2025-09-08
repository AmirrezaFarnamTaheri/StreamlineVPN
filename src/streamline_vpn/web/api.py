"""
FastAPI Web API
===============

FastAPI-based REST API for StreamlineVPN.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, Body, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=results.get("error", "Processing failed"),
                )
            return ProcessingResponse(
                success=True,
                message="Processing completed successfully",
                statistics=results.get("statistics"),
            )

        except Exception as e:
            logger.error(f"Processing error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/statistics")
    async def get_statistics():
        """Get processing statistics."""
        try:
            merger = get_merger()
            stats = await merger.get_statistics()
            return stats
        except Exception as e:
            logger.error(f"Statistics error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

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
            logger.error(f"Configurations error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/sources")
    async def get_sources():
        """Get source information."""
        try:
            merger = get_merger()
            source_stats = merger.source_manager.get_source_statistics()
            return source_stats
        except Exception as e:
            logger.error(f"Sources error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/sources/{source_url}/blacklist")
    async def blacklist_source(source_url: str, reason: str = ""):
        """Blacklist a source."""
        try:
            merger = get_merger()
            merger.source_manager.blacklist_source(source_url, reason)
            return {"message": f"Source {source_url} blacklisted"}
        except Exception as e:
            logger.error(f"Blacklist error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/sources/{source_url}/whitelist")
    async def whitelist_source(source_url: str):
        """Remove source from blacklist."""
        try:
            merger = get_merger()
            merger.source_manager.whitelist_source(source_url)
            return {"message": f"Source {source_url} whitelisted"}
        except Exception as e:
            logger.error(f"Whitelist error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/cache/clear")
    async def clear_cache():
        """Clear all caches."""
        try:
            merger = get_merger()
            await merger.clear_cache()
            return {"message": "Cache cleared successfully"}
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

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
            logger.error(f"Metrics error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

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
            logger.error(f"Runtime config error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

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
            logger.error(f"Reload settings error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return app
