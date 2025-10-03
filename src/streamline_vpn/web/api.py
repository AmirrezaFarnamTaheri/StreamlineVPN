"""
FastAPI Web API for StreamlineVPN
=================================

This module provides a factory function to create the main FastAPI application.
It sets up the application lifespan, middleware, exception handlers, and API routers.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..core.merger import StreamlineVPNMerger
from ..jobs.pipeline_cleanup import cleanup_processing_jobs_periodically
from ..settings import get_settings
from ..utils.logging import get_logger
from .api.routes import cache, configurations, pipeline, sources, system

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager to handle startup and shutdown events.
    """
    logger.info("API server initializing...")
    # Startup
    try:
        cleanup_task = asyncio.create_task(cleanup_processing_jobs_periodically())
        app.state.cleanup_task = cleanup_task

        merger = StreamlineVPNMerger()
        await merger.initialize()
        app.state.merger = merger
        logger.info("API server initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize merger during startup: {e}", exc_info=True)
        app.state.merger = None

    yield

    # Shutdown
    logger.info("API server shutting down...")
    if app.state.cleanup_task:
        app.state.cleanup_task.cancel()
        try:
            await app.state.cleanup_task
        except asyncio.CancelledError:
            pass  # Expected

    if app.state.merger:
        await app.state.merger.shutdown()
    logger.info("API server shutdown complete.")


def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application instance.
    """
    app = FastAPI(
        title="StreamlineVPN API",
        description="A comprehensive API for managing VPN configurations.",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=settings.allow_credentials,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
    )

    # Custom exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content={"detail": f"Invalid request: {exc.errors()}"},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"An unhandled exception occurred: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred."},
        )

    # Include modular routers
    app.include_router(system.router)
    app.include_router(pipeline.router)
    app.include_router(configurations.router)
    app.include_router(sources.router)
    app.include_router(cache.router)

    return app