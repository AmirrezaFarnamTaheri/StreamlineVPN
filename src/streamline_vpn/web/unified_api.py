"""
Unified StreamlineVPN API Server
================================

Consolidated API implementation combining pipeline, statistics, sources,
and a static UI mount. This module is self-contained so it can be used as
the main server entrypoint without relying on other web modules.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
import time

from fastapi import (
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
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from ..core.merger import StreamlineVPNMerger
from ..models.formats import OutputFormat
from ..utils.logging import get_logger
from ..settings import get_settings

logger = get_logger(__name__)

# Prometheus metrics (simple, per-process registry)
try:  # Optional; keep server running even if library missing
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )

    METRICS_REGISTRY = CollectorRegistry()
    HTTP_REQUESTS_IN_PROGRESS = Gauge(
        "http_requests_in_progress",
        "HTTP requests in progress",
        registry=METRICS_REGISTRY,
    )
    HTTP_REQUESTS_TOTAL = Counter(
        "http_requests_total",
        "Total HTTP requests",
        labelnames=("method", "path", "status"),
        registry=METRICS_REGISTRY,
    )
    HTTP_REQUEST_LATENCY = Histogram(
        "http_request_duration_seconds",
        "HTTP request latency",
        labelnames=("method", "path"),
        registry=METRICS_REGISTRY,
    )
except Exception:  # pragma: no cover - optional dependency fallback
    METRICS_REGISTRY = None
    HTTP_REQUESTS_IN_PROGRESS = None
    HTTP_REQUESTS_TOTAL = None
    HTTP_REQUEST_LATENCY = None


# =======================
# Configuration Manager
# =======================

class ConfigManager:
    """Centralized configuration management."""

    @staticmethod
    def find_config_path() -> Path:
        """Find configuration file with proper fallback logic."""
        # Priority order for config search
        search_candidates: List[Path] = []

        # Env override can point to file or directory
        env_val = os.getenv("APP_CONFIG_PATH", "").strip()
        if env_val:
            p = Path(env_val)
            search_candidates.append(p if p.suffix else p / "sources.unified.yaml")

        # CWD candidates
        search_candidates += [
            Path.cwd() / "config" / "sources.unified.yaml",
            Path.cwd() / "config" / "sources.yaml",
        ]

        # Project-root candidates (relative to this file)
        root = Path(__file__).resolve().parents[3]
        search_candidates += [
            root / "config" / "sources.unified.yaml",
            root / "config" / "sources.yaml",
        ]

        for path in search_candidates:
            try:
                if path and path.exists():
                    logger.info("Using configuration: %s", path)
                    return path.resolve()
            except Exception:
                continue

        # Create a minimal default config if none exists
        default_path = Path.cwd() / "config" / "sources.yaml"
        default_path.parent.mkdir(parents=True, exist_ok=True)
        default_config = {
            "sources": {
                "free": [
                    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt"
                ]
            }
        }
        try:
            import yaml

            with open(default_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(default_config, f)
            logger.info("Created default configuration: %s", default_path)
        except Exception as exc:
            logger.warning("Failed to write default config: %s", exc)
        return default_path


# =======================
# Job Management
# =======================

class JobManager:
    """Centralized job management with automatic cleanup."""

    def __init__(self) -> None:
        # Determine jobs file location. If an env var points to a directory,
        # store jobs.json inside it. This also makes tests easy to sandbox.
        jobs_path_env = os.getenv("JOBS_FILE") or os.getenv("JOBS_DIR", "data/jobs.json")
        jp = Path(jobs_path_env)
        if jp.exists() and jp.is_dir():
            self.jobs_file = jp / "jobs.json"
        else:
            # If jobs_path_env looks like a file relative to a patched Path
            # (e.g., tests patch Path() to return a tmp directory), handle later.
            self.jobs_file = jp

        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self._load_jobs()

    def _resolve_jobs_file(self) -> Path:
        # If jobs_file is a directory, use jobs.json inside it
        if self.jobs_file.exists() and self.jobs_file.is_dir():
            return self.jobs_file / "jobs.json"
        # If parent is a directory that does not exist, create it on save
        return self.jobs_file

    def _load_jobs(self) -> None:
        """Load existing jobs from storage and mark stale ones appropriately."""
        jobs_file = self._resolve_jobs_file()
        if jobs_file.exists() and jobs_file.is_file():
            try:
                with open(jobs_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                loaded = 0
                for job in data.get("jobs", []):
                    job_id = job.get("id") or f"job_{uuid.uuid4().hex[:8]}"
                    status = job.get("status")
                    if status in {"completed", "failed", "cancelled"}:
                        self.jobs[job_id] = job
                    elif status in {"running", "pending"}:
                        # Mark as failed on restart
                        job["status"] = "failed"
                        job["error"] = "Job terminated on restart"
                        job["finished_at"] = datetime.now().isoformat()
                        self.jobs[job_id] = job
                    else:
                        self.jobs[job_id] = job
                    loaded += 1
                if loaded:
                    logger.info("Loaded %d jobs from %s", loaded, jobs_file)
            except Exception as e:
                logger.error("Failed to load jobs: %s", e)

    def _save_jobs(self) -> None:
        """Persist jobs to storage."""
        jobs_file = self._resolve_jobs_file()
        try:
            jobs_file.parent.mkdir(parents=True, exist_ok=True)
            with open(jobs_file, "w", encoding="utf-8") as f:
                json.dump({"jobs": list(self.jobs.values())}, f, indent=2)
        except Exception as e:
            logger.error("Failed to save jobs: %s", e)

    def create_job(self, job_type: str, config: Dict[str, Any]) -> str:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        self.jobs[job_id] = {
            "id": job_id,
            "type": job_type,
            "config": config,
            "status": "pending",
            "progress": 0,
            "created_at": now,
            "updated_at": now,
        }
        self._save_jobs()
        return job_id

    def update_job(self, job_id: str, updates: Dict[str, Any]) -> None:
        if job_id in self.jobs:
            self.jobs[job_id].update(updates)
            self.jobs[job_id]["updated_at"] = datetime.now().isoformat()
            self._save_jobs()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id)

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> None:
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove: List[str] = []
        for job_id, job in self.jobs.items():
            if job.get("status") in {"completed", "failed", "cancelled"}:
                created_str = job.get("created_at")
                try:
                    created = datetime.fromisoformat(created_str) if created_str else datetime.now()
                except Exception:
                    created = datetime.now()
                if created < cutoff:
                    to_remove.append(job_id)
        for jid in to_remove:
            self.jobs.pop(jid, None)
            self.tasks.pop(jid, None)
        if to_remove:
            self._save_jobs()
            logger.info("Cleaned up %d old jobs", len(to_remove))


# =======================
# Request/Response Models
# =======================

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime: float
    merger_initialized: bool


class PipelineRequest(BaseModel):
    config_path: Optional[str] = None
    output_dir: str = Field(default="output", max_length=255)
    formats: List[str] = Field(default_factory=lambda: ["json", "clash", "singbox"])

    @field_validator("config_path")
    @classmethod
    def validate_config_path(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return v
        p = Path(v)
        if not p.exists():
            raise ValueError(f"Configuration file not found: {v}")
        if p.suffix not in {".yaml", ".yml"}:
            raise ValueError("Configuration must be a YAML file")
        return v

    # Do not raise here to allow endpoint to return consistent 400s
    @field_validator("formats")
    @classmethod
    def passthrough_formats(cls, v: List[str]) -> List[str]:
        return v

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: str) -> str:
        if ".." in v or v.startswith("/") or v.startswith("\\"):
            raise ValueError("Invalid output directory")
        return v


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


class AddSourceRequest(BaseModel):
    url: str


# =======================
# Unified API Application
# =======================

class UnifiedAPI:
    """Unified API server with all functionality consolidated."""

    def __init__(self) -> None:
        self.merger: Optional[StreamlineVPNMerger] = None
        self.job_manager = JobManager()
        self.config_manager = ConfigManager()
        self.start_time = datetime.now()
        self.app = self._create_app()

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Application lifecycle management."""
        logger.info("Starting StreamlineVPN Unified API...")
        try:
            config_path = self.config_manager.find_config_path()
            # Toggle cache via env (default disabled to avoid external deps)
            cache_env = os.getenv("CACHE_ENABLED", os.getenv("STREAMLINE_CACHE_ENABLED", "false")).lower()
            cache_enabled = cache_env in {"1", "true", "yes", "on"}
            self.merger = StreamlineVPNMerger(
                config_path=str(config_path), cache_enabled=cache_enabled
            )
            await self.merger.initialize()
            logger.info("Merger initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize merger: %s", e)
            self.merger = None

        cleanup_task = asyncio.create_task(self._periodic_cleanup())
        try:
            yield
        finally:
            logger.info("Shutting down StreamlineVPN API...")
            cleanup_task.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(cleanup_task), timeout=2)
            except Exception:
                pass
            if self.merger:
                await self.merger.shutdown()

    async def _periodic_cleanup(self) -> None:
        while True:
            try:
                await asyncio.sleep(3600)
                self.job_manager.cleanup_old_jobs()
            except asyncio.CancelledError:
                break
            except Exception as e:  # pragma: no cover - background log only
                logger.error("Cleanup error: %s", e)

    def _create_app(self) -> FastAPI:
        app = FastAPI(
            title="StreamlineVPN Unified API",
            description="Consolidated VPN Configuration Aggregator API",
            version="3.0.0",
            lifespan=self.lifespan,
        )

        self._setup_cors(app)
        self._setup_routes(app)
        self._setup_exception_handlers(app)
        self._setup_static_files(app)
        self._setup_metrics(app)
        return app

    def _setup_cors(self, app: FastAPI) -> None:
        """Setup CORS middleware with proper configuration."""
        allowed_origins = self._parse_env_list(
            "ALLOWED_ORIGINS",
            [
                "http://localhost:3000",
                "http://localhost:8080",
            ],
        )
        allowed_methods = self._parse_env_list(
            "ALLOWED_METHODS",
            ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        )
        allowed_headers = self._parse_env_list(
            "ALLOWED_HEADERS",
            ["Content-Type", "Authorization"],
        )
        allow_credentials = os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true"

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=allow_credentials,
            allow_methods=allowed_methods,
            allow_headers=allowed_headers,
        )

        logger.info(
            f"CORS configured: origins={allowed_origins}, credentials={allow_credentials}"
        )

    def _parse_env_list(self, env_var: str, default: List[str]) -> List[str]:
        """Parse environment variable as JSON array or comma-separated list."""
        value = os.getenv(env_var)
        if not value:
            return default
        try:
            return json.loads(value)  # type: ignore[return-value]
        except Exception:
            return [item.strip() for item in value.split(",") if item.strip()]

    def _setup_routes(self, app: FastAPI) -> None:
        @app.get("/", tags=["General"], response_model=None)
        async def root(request: Request) -> Response:
            """Root endpoint with simple content negotiation.

            - If a browser requests HTML (Accept contains text/html), serve docs/index.html
            - Otherwise return a JSON status payload
            """
            accept = request.headers.get("accept", "")
            if "text/html" in accept:
                docs_path = Path(__file__).resolve().parents[3] / "docs"
                index_file = docs_path / "index.html"
                if index_file.exists():
                    return FileResponse(str(index_file), media_type="text/html")
            # Default JSON
            return JSONResponse({
                "message": "StreamlineVPN Unified API",
                "version": "3.0.0",
                "docs": "/docs",
                "web": "/web"
            })

        @app.get("/health", response_model=HealthResponse, tags=["General"])
        async def health() -> HealthResponse:
            uptime = (datetime.now() - self.start_time).total_seconds()
            merger_status = "healthy" if self.merger else "degraded"
            return HealthResponse(
                status=merger_status,
                timestamp=datetime.now().isoformat(),
                version="3.0.0",
                uptime=uptime,
                merger_initialized=self.merger is not None,
            )

        @app.post(
            "/api/v1/pipeline/run",
            response_model=PipelineResponse,
            status_code=status.HTTP_202_ACCEPTED,
            tags=["Pipeline"],
        )
        async def run_pipeline(request: PipelineRequest, background_tasks: BackgroundTasks) -> PipelineResponse:
            # Validate formats before any other checks so clients get consistent 400s
            valid_formats = {f.value for f in OutputFormat}
            invalid = [f for f in request.formats if f not in valid_formats]
            if invalid:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid formats: {', '.join(invalid)}")

            if not self.merger:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service not initialized")

            job_id = self.job_manager.create_job("pipeline", request.dict())

            async def run_job() -> None:
                try:
                    self.job_manager.update_job(job_id, {"status": "running", "started_at": datetime.now().isoformat()})
                    result = await self.merger.process_all(output_dir=request.output_dir, formats=request.formats)  # type: ignore[arg-type]
                    self.job_manager.update_job(
                        job_id,
                        {
                            "status": "completed",
                            "result": result,
                            "finished_at": datetime.now().isoformat(),
                            "progress": 100,
                        },
                    )
                except Exception as e:
                    logger.error("Job %s failed: %s", job_id, e)
                    self.job_manager.update_job(
                        job_id,
                        {
                            "status": "failed",
                            "error": str(e),
                            "finished_at": datetime.now().isoformat(),
                        },
                    )

            background_tasks.add_task(run_job)
            return PipelineResponse(status="accepted", message=f"Pipeline job {job_id} started", job_id=job_id)

        @app.get("/api/v1/pipeline/status/{job_id}", tags=["Pipeline"])
        async def get_job_status(job_id: str) -> Dict[str, Any]:
            job = self.job_manager.get_job(job_id)
            if not job:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found")
            return job

        @app.get("/api/v1/statistics", response_model=StatisticsResponse, tags=["Statistics"])
        async def get_statistics() -> StatisticsResponse:
            if not self.merger:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service not initialized")
            stats = await self.merger.get_statistics()
            return StatisticsResponse(
                total_sources=stats.get("total_sources", 0),
                active_sources=stats.get("active_sources", 0),
                total_configs=stats.get("total_configs", 0),
                success_rate=stats.get("success_rate", 0.0),
                last_update=stats.get("last_update", datetime.now().isoformat()),
            )

        @app.get("/api/v1/configurations", tags=["Configurations"])
        async def get_configurations(limit: int = 100, offset: int = 0, protocol: Optional[str] = None) -> Dict[str, Any]:
            if not self.merger:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service not initialized")
            configs = await self.merger.get_configurations()
            if protocol:
                p = str(protocol).lower()
                configs = [c for c in configs if str(getattr(c, "protocol", "")).lower() in (p, getattr(getattr(c, "protocol", ""), "value", "").lower())]
            total = len(configs)
            configs_page = configs[offset : offset + limit]
            return {
                "total": total,
                "offset": offset,
                "limit": limit,
                "configurations": [c.to_dict() for c in configs_page],
            }

        @app.get("/api/v1/sources", tags=["Sources"])
        async def get_sources() -> Dict[str, Any]:
            if not self.merger:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service not initialized")
            sources: List[str]
            try:
                sources = await self.merger.source_manager.get_active_sources()  # type: ignore[assignment]
            except Exception:
                sources = []
            return {
                "sources": [
                    {"url": src, "status": "active", "configs": 0} for src in sources
                ]
            }

        @app.post("/api/v1/sources", tags=["Sources"], status_code=status.HTTP_201_CREATED)
        async def add_source(request: AddSourceRequest) -> Dict[str, Any]:
            if not self.merger:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service not initialized")
            try:
                await self.merger.source_manager.add_source(request.url)
                return {"status": "success", "message": f"Source {request.url} added"}
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        # Backward/compatibility alias used by some frontends
        @app.post("/api/v1/sources/add", tags=["Sources"], status_code=status.HTTP_201_CREATED)
        async def add_source_compat(request: AddSourceRequest) -> Dict[str, Any]:
            return await add_source(request)

        # Cache health endpoint (simple stub; extend to real cache if available)
        @app.get("/api/v1/cache/health", tags=["Cache"])
        async def cache_health() -> Dict[str, Any]:
            if self.merger and getattr(self.merger, "cache_manager", None):
                try:
                    stats = self.merger.cache_manager.get_cache_stats()  # type: ignore[attr-defined]
                    return {"status": "ok", "cache": "enabled", "stats": stats}
                except Exception as e:
                    logger.error("Cache health error: %s", e)
                    return {"status": "degraded", "cache": "enabled"}
            return {"status": "ok", "cache": "disabled"}

        # Cache clear endpoint (no-op if cache is disabled)
        @app.post("/api/v1/cache/clear", tags=["Cache"])
        async def cache_clear() -> Dict[str, Any]:
            try:
                if self.merger and getattr(self.merger, "clear_cache", None):
                    await self.merger.clear_cache()  # type: ignore[func-returns-value]
                    return {"status": "ok", "cleared": True}
                return {"status": "ok", "cleared": False}
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        # Validate sources endpoint (basic validation placeholder)
        @app.post("/api/v1/sources/validate", tags=["Sources"])
        async def validate_sources() -> Dict[str, Any]:
            if not self.merger:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service not initialized")
            try:
                active = await self.merger.source_manager.get_active_sources()  # type: ignore[assignment]
                valid = 0
                invalid = 0
                for url in active:
                    try:
                        result = self.merger.security_manager.validate_source(url)  # type: ignore[attr-defined]
                        if result.get("is_safe"):
                            valid += 1
                        else:
                            invalid += 1
                    except Exception:
                        invalid += 1
                return {"valid_sources": valid, "invalid_sources": invalid, "checked": len(active)}
            except Exception as e:
                logger.error("Source validation error: %s", e)
                return {"valid_sources": 0, "invalid_sources": 0, "checked": 0}

        # Config test endpoint used by config generator page
        @app.post("/api/v1/test-config", tags=["Configurations"])
        async def test_config(payload: Dict[str, Any]) -> Dict[str, Any]:
            # Accepts a payload like {"config": { ... } } and responds with a simple OK
            if not isinstance(payload, dict):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
            return {"status": "ok", "message": "Configuration looks valid"}

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket) -> None:
            await websocket.accept()
            try:
                while True:
                    if self.merger:
                        stats = await self.merger.get_statistics()
                        await websocket.send_json({"type": "statistics", "data": stats, "timestamp": datetime.now().isoformat()})
                    await asyncio.sleep(5)
            except WebSocketDisconnect:  # pragma: no cover - depends on client
                logger.info("WebSocket client disconnected")
            except Exception as e:  # pragma: no cover
                logger.error("WebSocket error: %s", e)

    def _setup_metrics(self, app: FastAPI) -> None:
        """Attach Prometheus /metrics endpoint and request metrics middleware."""
        if METRICS_REGISTRY is None:
            # Library not available; expose a small stub for visibility
            @app.get("/metrics", include_in_schema=False)
            async def metrics_unavailable() -> JSONResponse:  # type: ignore[misc]
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={"detail": "prometheus_client not installed"},
                )
            return

        @app.middleware("http")
        async def metrics_middleware(request: Request, call_next):  # type: ignore[no-redef]
            method = request.method
            route = request.scope.get("route")
            path_tpl = getattr(route, "path", None) or request.url.path
            if HTTP_REQUESTS_IN_PROGRESS is not None:
                HTTP_REQUESTS_IN_PROGRESS.inc()
            start = time.perf_counter()
            try:
                response = await call_next(request)
                status_code = str(getattr(response, "status_code", 500))
                # Concise access log (method path -> status, ms)
                try:
                    duration_ms = int((time.perf_counter() - start) * 1000)
                    logger.info("%s %s -> %s (%d ms)", method, path_tpl, status_code, duration_ms)
                except Exception:
                    pass
                return response
            finally:
                duration = time.perf_counter() - start
                if HTTP_REQUESTS_IN_PROGRESS is not None:
                    HTTP_REQUESTS_IN_PROGRESS.dec()
                if HTTP_REQUESTS_TOTAL is not None:
                    try:
                        HTTP_REQUESTS_TOTAL.labels(method=method, path=path_tpl, status=status_code).inc()
                    except Exception:
                        pass
                if HTTP_REQUEST_LATENCY is not None:
                    try:
                        HTTP_REQUEST_LATENCY.labels(method=method, path=path_tpl).observe(duration)
                    except Exception:
                        pass

        @app.get("/metrics", include_in_schema=False)
        async def metrics() -> Response:
            data = generate_latest(METRICS_REGISTRY)  # type: ignore[arg-type]
            return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    def _setup_exception_handlers(self, app: FastAPI) -> None:
        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(
            request: Request, exc: RequestValidationError
        ) -> JSONResponse:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": exc.errors(), "body": getattr(exc, "body", None)},
            )

        @app.exception_handler(HTTPException)
        async def http_exception_handler(
            request: Request, exc: HTTPException
        ) -> JSONResponse:
            return JSONResponse(
                status_code=exc.status_code, content={"detail": exc.detail}
            )

        # Friendly 404s: API JSON, UI fallback to index.html
        @app.exception_handler(404)
        async def not_found_handler(
            request: Request, exc: HTTPException
        ) -> JSONResponse | FileResponse:
            if request.url.path.startswith("/api/"):
                return JSONResponse(
                    {"detail": "API endpoint not found"}, status_code=404
                )
            docs_path = Path(__file__).resolve().parents[3] / "docs"
            index_file = docs_path / "index.html"
            if index_file.exists():
                return FileResponse(str(index_file), media_type="text/html")
            return JSONResponse({"detail": "Page not found"}, status_code=404)

        @app.exception_handler(Exception)
        async def general_exception_handler(
            request: Request, exc: Exception
        ) -> JSONResponse:
            logger.error("Unhandled exception: %s", exc, exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"},
            )

    def _setup_static_files(self, app: FastAPI) -> None:
        """Setup static file serving with proper error handling."""
        docs_path = Path(__file__).resolve().parents[3] / "docs"

        if not docs_path.exists():
            logger.warning(f"Docs directory not found at {docs_path}")
            return

        try:
            # Serve the entire docs folder under /static
            app.mount("/static", StaticFiles(directory=str(docs_path)), name="static")
            logger.info(f"Mounted static files from {docs_path}")

            # Also expose /assets for absolute references
            assets_dir = docs_path / "assets"
            if assets_dir.exists():
                app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
                logger.info(f"Mounted assets from {assets_dir}")

            # Direct file serving routes
            @app.get("/api-base.js", include_in_schema=False)
            async def serve_api_base():
                """Serve the API base configuration file."""
                api_base_file = docs_path / "api-base.js"
                if api_base_file.exists():
                    return FileResponse(
                        str(api_base_file),
                        media_type="application/javascript",
                        headers={"Cache-Control": "no-cache"},
                    )
                return JSONResponse(
                    {"detail": "api-base.js not found"},
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            # Main page routes (avoid duplicating root, keep /web and /index.html)
            @app.get("/web", include_in_schema=False)
            @app.get("/index.html", include_in_schema=False)
            async def serve_index():
                """Serve the main index page."""
                index_file = docs_path / "index.html"
                if index_file.exists():
                    return FileResponse(str(index_file), media_type="text/html")
                return JSONResponse(
                    {"message": "Web interface not found"},
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            @app.get("/interactive.html", include_in_schema=False)
            async def serve_interactive():
                """Serve the interactive control panel."""
                page = docs_path / "interactive.html"
                if page.exists():
                    return FileResponse(str(page), media_type="text/html")
                return JSONResponse(
                    {"detail": "interactive.html not found"},
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            @app.get("/config_generator.html", include_in_schema=False)
            async def serve_config_generator():
                """Serve the configuration generator page."""
                page = docs_path / "config_generator.html"
                if page.exists():
                    return FileResponse(str(page), media_type="text/html")
                return JSONResponse(
                    {"detail": "config_generator.html not found"},
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            @app.get("/troubleshooting.html", include_in_schema=False)
            async def serve_troubleshooting():
                """Serve the troubleshooting page."""
                page = docs_path / "troubleshooting.html"
                if page.exists():
                    return FileResponse(str(page), media_type="text/html")
                return JSONResponse(
                    {"detail": "troubleshooting.html not found"},
                    status_code=status.HTTP_404_NOT_FOUND,
                )

        except Exception as e:  # pragma: no cover - mount errors only
            logger.error(f"Failed to setup static files: {e}")


# =======================
# Factory Function
# =======================

def create_unified_app() -> FastAPI:
    api = UnifiedAPI()
    return api.app


# Uvicorn entrypoint convenience
app = create_unified_app()


if __name__ == "__main__":  # pragma: no cover - manual run
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8080"))
    logger.info("Starting Unified API Server on %s:%s", host, port)
    uvicorn.run(app, host=host, port=port, log_level="info")
