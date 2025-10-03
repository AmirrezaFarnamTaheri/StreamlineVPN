import asyncio
from contextlib import asynccontextmanager
import aiohttp
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
    session = aiohttp.ClientSession()
    app.state.http_session = session

    try:
        cleanup_task = asyncio.create_task(cleanup_processing_jobs_periodically())
        app.state.cleanup_task = cleanup_task

        merger = StreamlineVPNMerger(session=session)
        await merger.initialize()
        app.state.merger = merger
        logger.info("API server initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize merger during startup: {e}", exc_info=True)
        app.state.merger = None
        if not session.closed:
            await session.close()

    yield

    logger.info("API server shutting down...")
    if hasattr(app.state, "cleanup_task") and app.state.cleanup_task:
        app.state.cleanup_task.cancel()
        try:
            await app.state.cleanup_task
        except asyncio.CancelledError:
            pass

    if hasattr(app.state, "merger") and app.state.merger:
        await app.state.merger.shutdown()

    if not session.closed:
        await session.close()

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

    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=settings.allow_credentials,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            field = ".".join(map(str, error.get("loc", [])))
            message = error.get("msg", "invalid input")
            errors.append(f"{field}: {message}")
        detail = "; ".join(errors)
        if len(detail) > 512:
            detail = detail[:509] + "..."
        return JSONResponse(
            status_code=400,
            content={"detail": f"Invalid request: {detail}"},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"An unhandled exception occurred: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred."},
        )

    app.include_router(system.router)
    app.include_router(pipeline.router)
    app.include_router(configurations.router)
    app.include_router(sources.router)
    app.include_router(cache.router)

    return app