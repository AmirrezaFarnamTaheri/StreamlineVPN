import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    status,
    WebSocket,
    WebSocketDisconnect,
    UploadFile,
    File,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from ..core.instance import get_merger_instance

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the application's lifespan."""
    app.state.merger = await get_merger_instance()
    yield
    if hasattr(app.state, 'merger') and app.state.merger:
        await app.state.merger.shutdown()
        app.state.merger = None

class UnifiedAPIServer:
    """Unified API server with proper error handling and static file serving."""

    def __init__(self):
        self.app = FastAPI(
            title="StreamlineVPN API",
            description="Unified API for StreamlineVPN configuration management",
            version="2.0.0",
            lifespan=lifespan,
        )
        self.jobs: List[Dict[str, Any]] = []

        self._setup_middleware()
        self._setup_exception_handlers()
        self._setup_static_files()
        self._setup_routes()

    def _setup_middleware(self) -> None:
        """Setup CORS and other middleware."""
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.middleware("http")
        async def add_request_id(request: Request, call_next):
            """Add unique request ID for tracking."""
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

    def _setup_exception_handlers(self) -> None:
        """Setup global exception handlers."""
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            """Handle HTTP exceptions with detailed logging."""
            logger.warning(f"HTTP exception: {exc.detail}")
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            """Handle general exceptions with logging."""
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"},
            )

    def _setup_static_files(self) -> None:
        """Setup static file serving."""
        docs_path = Path(__file__).resolve().parents[3] / "docs"
        if docs_path.exists():
            self.app.mount("/static", StaticFiles(directory=str(docs_path)), name="static")

    def _setup_routes(self) -> None:
        """Setup API routes."""
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy"}

        @self.app.get("/")
        async def root():
            """Root endpoint with service information."""
            return {"service": "StreamlineVPN API", "version": "2.0.0"}

        @self.app.get("/api/v1/sources")
        async def get_sources(request: Request):
            """Return configured source URLs."""
            merger = request.app.state.merger
            sources = list(merger.source_manager.sources.keys())
            return {"sources": sources, "total": len(sources)}

        @self.app.get("/api/v1/configurations")
        async def get_configurations(request: Request, limit: int = 100, offset: int = 0):
            """Process sources and return VPN configurations."""
            merger = request.app.state.merger
            await merger.process_all()
            configs = [cfg.to_dict() for cfg in merger.get_configurations()]
            return {"configurations": configs[offset : offset + limit], "total": len(configs)}

        @self.app.post("/api/v1/pipeline/run")
        async def run_pipeline(request: Request):
            """Run the VPN configuration pipeline and return summary."""
            merger = request.app.state.merger
            result = await merger.process_all()
            return {"status": "completed", "result": result}

        @self.app.get("/api/statistics")
        async def get_statistics(request: Request):
            """Get processing statistics."""
            merger = request.app.state.merger
            return await merger.get_statistics()

    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.app

def create_unified_app() -> FastAPI:
    """Create and configure the unified API application."""
    server = UnifiedAPIServer()
    return server.get_app()

if __name__ == "__main__":
    import uvicorn
    app = create_unified_app()
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)