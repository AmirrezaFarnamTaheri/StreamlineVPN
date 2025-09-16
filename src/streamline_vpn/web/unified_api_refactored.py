"""
StreamlineVPN Unified API (Refactored)
======================================

Refactored unified API server using modular route structure.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import (
    health_router,
    sources_router,
    configurations_router,
    diagnostics_router,
    websocket_router
)
from .api.middleware import setup_middleware, setup_exception_handlers
from .api.static import setup_static_files


class UnifiedAPIServer:
    """Unified API server with modular architecture."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.app = None
        self.server = None
    
    def _create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Application lifespan manager."""
            # Startup
            print("🚀 Starting StreamlineVPN API Server...")
            yield
            # Shutdown
            print("🛑 Shutting down StreamlineVPN API Server...")
        
        app = FastAPI(
            title="StreamlineVPN API",
            description="Advanced VPN Configuration Manager API",
            version="1.0.0",
            lifespan=lifespan
        )
        
        # Setup middleware
        setup_middleware(app)
        setup_exception_handlers(app)
        
        # Setup static files
        setup_static_files(app)
        
        # Include routers
        app.include_router(health_router, tags=["health"])
        app.include_router(sources_router, prefix="/sources", tags=["sources"])
        app.include_router(configurations_router, prefix="/configurations", tags=["configurations"])
        app.include_router(diagnostics_router, prefix="/diagnostics", tags=["diagnostics"])
        app.include_router(websocket_router, tags=["websocket"])
        
        return app
    
    async def start(self):
        """Start the API server."""
        self.app = self._create_app()
        
        import uvicorn
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        
        self.server = uvicorn.Server(config)
        await self.server.serve()
    
    async def stop(self):
        """Stop the API server."""
        if self.server:
            self.server.should_exit = True
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        if not self.app:
            self.app = self._create_app()
        return self.app


def create_unified_app() -> FastAPI:
    """Create a unified FastAPI application."""
    server = UnifiedAPIServer()
    return server.get_app()


async def main():
    """Main entry point for running the server."""
    server = UnifiedAPIServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())

