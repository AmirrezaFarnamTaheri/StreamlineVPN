"""
Unified StreamlineVPN API Server
================================

Consolidated and fixed API implementation combining all functionality.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..core.merger import StreamlineVPNMerger
from ..models.formats import OutputFormat
from ..utils.logging import get_logger

logger = get_logger(__name__)

# =======================
# Configuration Manager
# =======================

class ConfigManager:
    """Centralized configuration management."""
    
    @staticmethod
    def find_config_path() -> Path:
        """Find configuration file with proper fallback logic."""
        # Priority order for config search
        search_paths = [
            Path(os.getenv("APP_CONFIG_PATH", "")),
            Path.cwd() / "config" / "sources.unified.yaml",
            Path.cwd() / "config" / "sources.yaml",
            Path(__file__).parent.parent.parent.parent / "config" / "sources.unified.yaml",
            Path(__file__).parent.parent.parent.parent / "config" / "sources.yaml",
        ]
        
        for path in search_paths:
            if path and path.exists():
                logger.info(f"Using configuration: {path}")
                return path.resolve()
        
        # Create default config if none exists
        default_path = Path.cwd() / "config" / "sources.yaml"
        default_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            "sources": {
                "free": [
                    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt"
                ]
            }
        }
        
        import yaml
        with open(default_path, 'w') as f:
            yaml.dump(default_config, f)
        
        logger.info(f"Created default configuration: {default_path}")
        return default_path

# =======================
# Job Management
# =======================

class JobManager:
    """Centralized job management with automatic cleanup."""
    
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self._load_jobs()
        
    def _load_jobs(self):
        """Load existing jobs from storage."""
        jobs_file = Path("data/jobs.json")
        if jobs_file.exists():
            try:
                with open(jobs_file, 'r') as f:
                    data = json.load(f)
                    # Clean up stale jobs on load
                    for job in data.get("jobs", []):
                        job_id = job.get("id")
                        if job.get("status") in ["completed", "failed"]:
                            self.jobs[job_id] = job
                        # Mark stale running/pending jobs as failed
                        elif job.get("status") in ["running", "pending"]:
                            job["status"] = "failed"
                            job["error"] = "Job terminated on restart"
                            job["finished_at"] = datetime.now().timestamp()
                            self.jobs[job_id] = job
            except Exception as e:
                logger.error(f"Failed to load jobs: {e}")
    
    def _save_jobs(self):
        """Persist jobs to storage."""
        jobs_file = Path("data/jobs.json")
        jobs_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(jobs_file, 'w') as f:
                json.dump({
                    "jobs": list(self.jobs.values())
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save jobs: {e}")
    
    def create_job(self, job_type: str, config: Dict[str, Any]) -> str:
        """Create a new job."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        
        self.jobs[job_id] = {
            "id": job_id,
            "type": job_type,
            "config": config,
            "status": "pending",
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        self._save_jobs()
        return job_id
    
    def update_job(self, job_id: str, updates: Dict[str, Any]):
        """Update job status."""
        if job_id in self.jobs:
            self.jobs[job_id].update(updates)
            self.jobs[job_id]["updated_at"] = datetime.now().isoformat()
            self._save_jobs()
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID."""
        return self.jobs.get(job_id)
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Remove old completed jobs."""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        jobs_to_remove = []
        for job_id, job in self.jobs.items():
            if job.get("status") in ["completed", "failed"]:
                created = datetime.fromisoformat(job.get("created_at", datetime.now().isoformat()))
                if created < cutoff:
                    jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            if job_id in self.tasks:
                del self.tasks[job_id]
        
        if jobs_to_remove:
            self._save_jobs()
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")

# =======================
# Request/Response Models
# =======================

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime: float

class PipelineRequest(BaseModel):
    config_path: Optional[str] = None
    output_dir: str = "output"
    formats: List[str] = ["json", "clash", "singbox"]

class PipelineResponse(BaseModel):
    status: str
    message: str
    job_id: str

class StatisticsResponse(BaseModel):
    total_sources: int
    active_sources: int
    total_configs: int
    success_rate: float
    last_update: str

# =======================
# Unified API Application
# =======================

class UnifiedAPI:
    """Unified API server with all functionality consolidated."""
    
    def __init__(self):
        self.merger: Optional[StreamlineVPNMerger] = None
        self.job_manager = JobManager()
        self.config_manager = ConfigManager()
        self.start_time = datetime.now()
        self.app = self._create_app()
        
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Application lifecycle management."""
        logger.info("Starting StreamlineVPN Unified API...")
        
        # Initialize merger
        try:
            config_path = self.config_manager.find_config_path()
            self.merger = StreamlineVPNMerger(config_path=str(config_path))
            await self.merger.initialize()
            logger.info("Merger initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize merger: {e}")
            self.merger = None
        
        # Start cleanup task
        cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        yield
        
        # Shutdown
        logger.info("Shutting down StreamlineVPN API...")
        cleanup_task.cancel()
        
        if self.merger:
            await self.merger.shutdown()
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old jobs."""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                self.job_manager.cleanup_old_jobs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def _create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        app = FastAPI(
            title="StreamlineVPN Unified API",
            description="Consolidated VPN Configuration Aggregator API",
            version="3.0.0",
            lifespan=self.lifespan,
        )
        
        # Configure CORS once
        self._setup_cors(app)
        
        # Setup routes
        self._setup_routes(app)
        
        # Setup exception handlers
        self._setup_exception_handlers(app)
        
        # Mount static files for web interface
        self._setup_static_files(app)
        
        return app
    
    def _setup_cors(self, app: FastAPI):
        """Setup CORS middleware once."""
        origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins if origins != ["*"] else ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )
    
    def _setup_routes(self, app: FastAPI):
        """Setup all API routes."""
        
        # Health endpoints
        @app.get("/", tags=["General"])
        async def root():
            return {
                "message": "StreamlineVPN Unified API",
                "version": "3.0.0",
                "docs": "/docs",
            }
        
        @app.get("/health", response_model=HealthResponse, tags=["General"])
        async def health():
            uptime = (datetime.now() - self.start_time).total_seconds()
            return HealthResponse(
                status="healthy" if self.merger else "degraded",
                timestamp=datetime.now().isoformat(),
                version="3.0.0",
                uptime=uptime,
            )
        
        # Pipeline endpoints
        @app.post("/api/v1/pipeline/run", 
                  response_model=PipelineResponse,
                  status_code=status.HTTP_202_ACCEPTED,
                  tags=["Pipeline"])
        async def run_pipeline(
            request: PipelineRequest,
            background_tasks: BackgroundTasks,
        ):
            """Run the VPN configuration pipeline."""
            if not self.merger:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Service not initialized"
                )
            
            # Validate formats
            valid_formats = {f.value for f in OutputFormat}
            invalid = [f for f in request.formats if f not in valid_formats]
            if invalid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid formats: {', '.join(invalid)}"
                )
            
            # Create job
            job_id = self.job_manager.create_job("pipeline", request.dict())
            
            # Run in background
            async def run_job():
                try:
                    self.job_manager.update_job(job_id, {
                        "status": "running",
                        "started_at": datetime.now().isoformat(),
                    })
                    
                    result = await self.merger.process_all(
                        output_dir=request.output_dir,
                        formats=request.formats,
                    )
                    
                    self.job_manager.update_job(job_id, {
                        "status": "completed",
                        "result": result,
                        "finished_at": datetime.now().isoformat(),
                        "progress": 100,
                    })
                    
                except Exception as e:
                    logger.error(f"Job {job_id} failed: {e}")
                    self.job_manager.update_job(job_id, {
                        "status": "failed",
                        "error": str(e),
                        "finished_at": datetime.now().isoformat(),
                    })
            
            background_tasks.add_task(run_job)
            
            return PipelineResponse(
                status="accepted",
                message=f"Pipeline job {job_id} started",
                job_id=job_id,
            )
        
        @app.get("/api/v1/pipeline/status/{job_id}", tags=["Pipeline"])
        async def get_job_status(job_id: str):
            """Get pipeline job status."""
            job = self.job_manager.get_job(job_id)
            if not job:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Job {job_id} not found"
                )
            return job
        
        # Statistics endpoint
        @app.get("/api/v1/statistics", 
                 response_model=StatisticsResponse,
                 tags=["Statistics"])
        async def get_statistics():
            """Get current statistics."""
            if not self.merger:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Service not initialized"
                )
            
            stats = await self.merger.get_statistics()
            
            return StatisticsResponse(
                total_sources=stats.get("total_sources", 0),
                active_sources=stats.get("active_sources", 0),
                total_configs=stats.get("total_configs", 0),
                success_rate=stats.get("success_rate", 0.0),
                last_update=stats.get("last_update", datetime.now().isoformat()),
            )
        
        # Configuration endpoints
        @app.get("/api/v1/configurations", tags=["Configurations"])
        async def get_configurations(
            limit: int = 100,
            offset: int = 0,
            protocol: Optional[str] = None,
        ):
            """Get processed configurations."""
            if not self.merger:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Service not initialized"
                )
            
            configs = await self.merger.get_configurations()
            
            # Filter by protocol if specified
            if protocol:
                configs = [c for c in configs if c.protocol == protocol]
            
            # Pagination
            total = len(configs)
            configs = configs[offset:offset + limit]
            
            return {
                "total": total,
                "offset": offset,
                "limit": limit,
                "configurations": [c.to_dict() for c in configs],
            }
        
        # Source management
        @app.get("/api/v1/sources", tags=["Sources"])
        async def get_sources():
            """Get configured sources."""
            if not self.merger:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Service not initialized"
                )
            
            sources = await self.merger.source_manager.get_active_sources()
            
            return {
                "sources": [
                    {
                        "url": source,
                        "status": "active",
                        "configs": 0,  # Would need to track this
                    }
                    for source in sources
                ]
            }
        
        @app.post("/api/v1/sources", tags=["Sources"])
        async def add_source(url: str):
            """Add a new source."""
            if not self.merger:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Service not initialized"
                )
            
            try:
                await self.merger.source_manager.add_source(url)
                return {"status": "success", "message": f"Source {url} added"}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        
        # WebSocket endpoint for real-time updates
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates."""
            await websocket.accept()
            try:
                while True:
                    # Send periodic updates
                    if self.merger:
                        stats = await self.merger.get_statistics()
                        await websocket.send_json({
                            "type": "statistics",
                            "data": stats,
                            "timestamp": datetime.now().isoformat(),
                        })
                    await asyncio.sleep(5)
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
    
    def _setup_exception_handlers(self, app: FastAPI):
        """Setup exception handlers."""
        
        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "detail": exc.errors(),
                    "body": exc.body if hasattr(exc, 'body') else None,
                }
            )
        
        @app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail}
            )
        
        @app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )
    
    def _setup_static_files(self, app: FastAPI):
        """Setup static file serving for web interface."""
        docs_path = Path(__file__).parent.parent.parent.parent / "docs"
        if docs_path.exists():
            app.mount("/static", StaticFiles(directory=str(docs_path)), name="static")
            
            @app.get("/web", include_in_schema=False)
            async def serve_web():
                index_file = docs_path / "index.html"
                if index_file.exists():
                    return FileResponse(str(index_file))
                return {"message": "Web interface not found"}

# =======================
# Factory Function
# =======================

def create_unified_app() -> FastAPI:
    """Create the unified API application."""
    api = UnifiedAPI()
    return api.app

# =======================
# Main Entry Point
# =======================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8080"))
    
    app = create_unified_app()
    
    logger.info(f"Starting Unified API Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
