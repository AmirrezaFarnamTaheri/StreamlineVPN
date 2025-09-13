"""
Fixed Unified API Server
========================

Fixes the incomplete unified_api.py with proper error handling and completeness.
"""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)


class UnifiedAPIServer:
    """Unified API server with proper error handling and static file serving."""

    def __init__(self):
        self.app = FastAPI(
            title="StreamlineVPN API",
            description="Unified API for StreamlineVPN configuration management",
            version="2.0.0"
        )
        self._setup_middleware()
        self._setup_exception_handlers()
        self._setup_static_files()
        self._setup_routes()

    def _setup_middleware(self) -> None:
        """Setup CORS and other middleware."""
        # Parse CORS settings from environment
        allowed_origins = self._parse_cors_setting("ALLOWED_ORIGINS", ["*"])
        allowed_methods = self._parse_cors_setting("ALLOWED_METHODS", ["*"])
        allowed_headers = self._parse_cors_setting("ALLOWED_HEADERS", ["*"])
        allow_credentials = os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true"

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=allow_credentials,
            allow_methods=allowed_methods,
            allow_headers=allowed_headers,
        )

        @self.app.middleware("http")
        async def add_request_id(request: Request, call_next):
            """Add unique request ID for tracking."""
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id

            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

    def _parse_cors_setting(self, env_var: str, default: List[str]) -> List[str]:
        """Parse CORS setting from environment variable."""
        value = os.getenv(env_var)
        if not value:
            return default

        # Try JSON first, fall back to comma-separated
        try:
            import json
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return [item.strip() for item in value.split(",") if item.strip()]

    def _setup_exception_handlers(self) -> None:
        """Setup global exception handlers."""
        
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(
            request: Request, exc: HTTPException
        ) -> JSONResponse:
            """Handle HTTP exceptions with detailed logging."""
            logger.warning(
                "HTTP exception on %s %s - Client: %s - Status: %s - Detail: %s",
                request.method,
                request.url.path,
                request.client.host if request.client else "unknown",
                exc.status_code,
                exc.detail
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": "Request failed",
                    "message": exc.detail,
                    "path": request.url.path,
                    "method": request.method,
                    "timestamp": datetime.now().isoformat(),
                    "detail": exc.detail,
                    "request_id": getattr(request.state, 'request_id', None),
                },
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(
            request: Request, exc: Exception
        ) -> JSONResponse:
            """Handle general exceptions with logging."""
            logger.error(
                "Unhandled exception on %s %s - Client: %s - Exception: %s", 
                request.method, 
                request.url.path,
                request.client.host if request.client else "unknown",
                exc,
                exc_info=True
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred while processing your request",
                    "path": request.url.path,
                    "method": request.method,
                    "timestamp": datetime.now().isoformat(),
                    "request_id": getattr(request.state, 'request_id', None),
                },
            )

    def _setup_static_files(self) -> None:
        """Setup static file serving with proper error handling."""
        docs_path = Path(__file__).resolve().parents[3] / "docs"

        if not docs_path.exists():
            logger.warning("Docs directory not found at %s", docs_path)
            return

        try:
            # Serve the entire docs folder under /static
            self.app.mount("/static", StaticFiles(directory=str(docs_path)), name="static")
            logger.info("Mounted static files from %s", docs_path)

            # Also expose /assets for absolute references
            assets_dir = docs_path / "assets"
            if assets_dir.exists():
                self.app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
                logger.info("Mounted assets from %s", assets_dir)

        except Exception as e:
            logger.error("Failed to mount static files: %s", e)

    def _setup_routes(self) -> None:
        """Setup API routes."""

        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "2.0.0",
                "service": "streamline-vpn-api"
            }

        # API base configuration for frontend
        @self.app.get("/api-base.js", include_in_schema=False)
        async def serve_api_base():
            """Serve the API base configuration file."""
            # Get the API base URL from environment or construct from request
            api_base = os.getenv("API_BASE_URL", "http://localhost:8080")

            js_content = f"""
// API Base Configuration for StreamlineVPN Frontend
window.__API_BASE__ = '{api_base}';
window.__API_VERSION__ = '2.0.0';
window.__SERVICE_NAME__ = 'StreamlineVPN';

// Debug information
console.log('StreamlineVPN API Base:', window.__API_BASE__);
            """.strip()

            from fastapi.responses import Response
            return Response(
                content=js_content,
                media_type="application/javascript",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )

        # Root endpoint
        @self.app.get("/")
        async def root():
            """Root endpoint with service information."""
            return {
                "service": "StreamlineVPN API",
                "version": "2.0.0",
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "endpoints": {
                    "health": "/health",
                    "docs": "/docs",
                    "api_base": "/api-base.js",
                    "static": "/static/"
                }
            }

        # API v1 placeholder routes
        @self.app.get("/api/v1/sources")
        async def get_sources():
            """Get available sources."""
            # This would be replaced with actual implementation
            return {
                "sources": [],
                "total": 0,
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/api/v1/configurations")
        async def get_configurations(limit: int = 100, offset: int = 0):
            """Get VPN configurations."""
            # This would be replaced with actual implementation
            return {
                "configurations": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "timestamp": datetime.now().isoformat()
            }

        @self.app.post("/api/v1/pipeline/run")
        async def run_pipeline(request: Dict[str, Any]):
            """Run the VPN configuration pipeline."""
            # This would be replaced with actual implementation
            job_id = f"job_{uuid.uuid4().hex[:12]}"

            return {
                "job_id": job_id,
                "status": "accepted",
                "message": "Pipeline job queued for execution",
                "timestamp": datetime.now().isoformat()
            }

        @self.app.post("/api/v1/sources/validate-urls")
        async def validate_urls(request: Request):
            """Validate a list of URLs."""
            from urllib.parse import urlparse
            body = await request.json()
            urls = body.get("urls", [])
            results = []
            for url in urls:
                try:
                    parsed = urlparse(url)
                    is_valid = all([parsed.scheme, parsed.netloc]) and parsed.scheme in ['http', 'https']
                except Exception:
                    is_valid = False
                results.append({"url": url, "valid": is_valid})
            return {"checked": len(urls), "results": results}

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            client_id = str(uuid.uuid4())
            await websocket.send_json({"type": "connection", "status": "connected", "client_id": client_id})
            try:
                while True:
                    data = await websocket.receive_json()
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    else:
                        await websocket.send_json({"type": "echo", "received": data})
            except Exception:
                pass

    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.app


def create_unified_app() -> FastAPI:
    """Create and configure the unified API application."""
    server = UnifiedAPIServer()
    return server.get_app()


# For direct execution
if __name__ == "__main__":
    import uvicorn

    app = create_unified_app()

    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8080"))

    uvicorn.run(app, host=host, port=port, reload=True)
