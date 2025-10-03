import os
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status, Request

from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.settings import get_settings
from ..dependencies import get_merger
from ..models import HealthResponse

system_router = APIRouter()
start_time = datetime.now()


@system_router.get("/", response_model=Dict[str, str], tags=["System"])
async def root():
    """Root endpoint providing basic API information."""
    return {
        "message": "StreamlineVPN API",
        "version": "2.0.0",
        "docs": "/docs",
    }


@system_router.get("/health", response_model=HealthResponse, tags=["System"])
async def health(request: Request) -> HealthResponse:
    """Health check endpoint for monitoring."""
    uptime = (datetime.now() - start_time).total_seconds()
    service_healthy = hasattr(request.app.state, "merger") and request.app.state.merger is not None
    return HealthResponse(
        status="healthy" if service_healthy else "degraded",
        timestamp=datetime.now().isoformat(),
        version="2.0.0",
        uptime=uptime,
    )


@system_router.get("/metrics", tags=["System"])
async def get_metrics():
    """Placeholder for Prometheus metrics integration."""
    return {"message": "Metrics endpoint - integrate with Prometheus client"}


@system_router.get("/config/runtime", tags=["System"])
async def get_runtime_configuration():
    """Dump current sanitized runtime configuration."""
    settings = get_settings()
    return {
        "fetcher": settings.fetcher.model_dump(),
        "security": settings.security.model_dump(),
        "supported_protocol_prefixes": settings.supported_protocol_prefixes,
    }


@system_router.post("/config/reload", tags=["System"])
async def reload_runtime_configuration(
    request: Request,
    overrides: Optional[Dict[str, Any]] = Body(None),
):
    """Reload runtime configuration by re-reading environment variables and re-initializing the merger."""
    try:
        # Apply provided overrides to environment
        if overrides:
            for k, v in overrides.items():
                if isinstance(k, str) and k.startswith("STREAMLINE_"):
                    os.environ[k] = str(v)

        # Clear cached settings to pick up new env
        get_settings.cache_clear()

        # Re-initialize merger with fresh settings
        if hasattr(request.app.state, "merger") and request.app.state.merger:
            await request.app.state.merger.shutdown()

        session = request.app.state.http_session
        new_merger = StreamlineVPNMerger(session=session)
        await new_merger.initialize()
        request.app.state.merger = new_merger

        settings = get_settings()
        return {
            "message": "Runtime configuration reloaded",
            "fetcher": settings.fetcher.model_dump(),
            "security": settings.security.model_dump(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload configuration: {e}",
        )