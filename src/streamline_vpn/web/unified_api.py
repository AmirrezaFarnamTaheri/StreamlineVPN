"""
Unified FastAPI Application Factory
===================================

This module provides a factory function to create the main unified FastAPI application.
It combines the API, static file serving, and other components into a single server.
"""

from fastapi import FastAPI
from .api.routes import (
    cache_router,
    configurations_router,
    pipeline_router,
    sources_router,
    system_router,
    websocket_router,
)
from .lifespan import lifespan_manager
from .middleware import setup_middleware
from .static_config import mount_static_files


def create_unified_app() -> FastAPI:
    """
    Creates and configures the unified FastAPI application.

    This factory assembles the API routers, middleware, static file serving,
    and lifespan management into a single, cohesive application.
    """
    app = FastAPI(
        title="StreamlineVPN Unified API",
        description="A unified server for the StreamlineVPN API and frontend.",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan_manager,
    )

    # Configure middleware (CORS, Request ID, etc.)
    setup_middleware(app)

    # Include all API routers
    app.include_router(system_router, prefix="/api", tags=["System"])
    app.include_router(pipeline_router, prefix="/api", tags=["Pipeline"])
    app.include_router(configurations_router, prefix="/api", tags=["Configurations"])
    app.include_router(sources_router, prefix="/api", tags=["Sources"])
    app.include_router(cache_router, prefix="/api", tags=["Cache"])
    app.include_router(websocket_router, tags=["WebSocket"])

    # Mount static files for the frontend (must be last)
    mount_static_files(app)

    return app