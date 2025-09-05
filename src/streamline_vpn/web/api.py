"""
FastAPI Web API
===============

FastAPI-based REST API for StreamlineVPN.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Body
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..core.merger import StreamlineVPNMerger
from ..utils.logging import get_logger
from ..settings import (
    get_fetcher_settings,
    get_security_settings,
    get_supported_protocol_prefixes,
)

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
        redoc_url="/redoc"
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
            "docs": "/docs"
        }
    
    @app.get("/health", response_model=HealthResponse)
    async def health():
        """Health check endpoint."""
        uptime = (datetime.now() - start_time).total_seconds()
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="2.0.0",
            uptime=uptime
        )
    
    @app.post("/process", response_model=ProcessingResponse)
    async def process_configurations(
        request: ProcessingRequest,
        background_tasks: BackgroundTasks
    ):
        """Process VPN configurations."""
        try:
            merger = get_merger()
            
            # Process configurations
            results = await merger.process_all(
                output_dir=request.output_dir,
                formats=request.formats
            )
            
            if results.get("success", False):
                return ProcessingResponse(
                    success=True,
                    message="Processing completed successfully",
                    statistics=results.get("statistics")
                )
            else:
                return ProcessingResponse(
                    success=False,
                    message=results.get("error", "Processing failed")
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
                "configurations": [config.to_dict() for config in configs]
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
            return {"message": "Metrics endpoint - integrate with Prometheus client"}
        except Exception as e:
            logger.error(f"Metrics error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/config/runtime")
    async def get_runtime_configuration():
        """Dump current runtime configuration (sanitized)."""
        try:
            fetcher = get_fetcher_settings()
            security = get_security_settings()
            return {
                "fetcher": {
                    "max_concurrent": fetcher.max_concurrent,
                    "timeout_seconds": fetcher.timeout_seconds,
                    "retry_attempts": fetcher.retry_attempts,
                    "retry_delay": fetcher.retry_delay,
                    "cb_failure_threshold": fetcher.cb_failure_threshold,
                    "cb_recovery_timeout_seconds": fetcher.cb_recovery_timeout_seconds,
                    "rl_max_requests": fetcher.rl_max_requests,
                    "rl_time_window_seconds": fetcher.rl_time_window_seconds,
                    "rl_burst_limit": fetcher.rl_burst_limit,
                },
                "security": {
                    "suspicious_tlds": security.suspicious_tlds,
                    "safe_protocols": security.safe_protocols,
                    "safe_encryptions": security.safe_encryptions,
                    "safe_ports": security.safe_ports,
                    "suspicious_text_patterns": security.suspicious_text_patterns,
                },
                "supported_protocol_prefixes": get_supported_protocol_prefixes(),
            }
        except Exception as e:
            logger.error(f"Runtime config error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/config/reload")
    async def reload_runtime_configuration(overrides: Optional[Dict[str, Any]] = Body(None)):
        """Reload runtime configuration by re-reading environment variables.

        Optionally accepts a JSON body of env var overrides (STREAMLINE_* keys),
        which are applied before reloading. The merger instance is re-initialized
        to ensure new settings take effect across components.
        """
        global merger
        try:
            # Apply provided overrides
            if overrides:
                for k, v in overrides.items():
                    if isinstance(k, str) and k.startswith("STREAMLINE_"):
                        os.environ[k] = str(v)

            # Recreate merger to pick up new settings
            if merger is not None:
                try:
                    await merger.shutdown()
                except Exception:
                    pass
                merger = None

            # Return the fresh settings snapshot
            fetcher = get_fetcher_settings()
            security = get_security_settings()
            return {
                "message": "Runtime configuration reloaded",
                "fetcher": {
                    "max_concurrent": fetcher.max_concurrent,
                    "timeout_seconds": fetcher.timeout_seconds,
                    "retry_attempts": fetcher.retry_attempts,
                    "retry_delay": fetcher.retry_delay,
                    "cb_failure_threshold": fetcher.cb_failure_threshold,
                    "cb_recovery_timeout_seconds": fetcher.cb_recovery_timeout_seconds,
                    "rl_max_requests": fetcher.rl_max_requests,
                    "rl_time_window_seconds": fetcher.rl_time_window_seconds,
                    "rl_burst_limit": fetcher.rl_burst_limit,
                },
                "security": {
                    "suspicious_tlds": security.suspicious_tlds,
                    "safe_protocols": security.safe_protocols,
                    "safe_encryptions": security.safe_encryptions,
                    "safe_ports": security.safe_ports,
                    "suspicious_text_patterns": security.suspicious_text_patterns,
                },
                "supported_protocol_prefixes": get_supported_protocol_prefixes(),
            }
        except Exception as e:
            logger.error(f"Reload settings error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return app
