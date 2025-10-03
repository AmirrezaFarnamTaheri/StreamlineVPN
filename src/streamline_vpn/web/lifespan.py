import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from ..core.merger import StreamlineVPNMerger
from ..jobs.pipeline_cleanup import cleanup_processing_jobs_periodically
from ..utils.logging import get_logger

logger = get_logger(__name__)

import aiohttp

@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    """
    Manages the application's lifespan, handling startup and shutdown events.
    This includes creating and closing the shared aiohttp ClientSession.
    """
    logger.info("Server starting up...")

    # Create a single, shared aiohttp session for the application's lifespan
    async with aiohttp.ClientSession() as session:
        app.state.http_session = session
        logger.info("Aiohttp session created.")

        # Start background tasks
        cleanup_task = asyncio.create_task(cleanup_processing_jobs_periodically())
        app.state.cleanup_task = cleanup_task
        logger.info("Background cleanup task started.")

        # Initialize the core merger service with the shared session
        try:
            merger = StreamlineVPNMerger(session=session)
            await merger.initialize()
            app.state.merger = merger
            logger.info("StreamlineVPNMerger initialized successfully.")
        except Exception as e:
            logger.critical(f"Fatal error during merger initialization: {e}", exc_info=True)
            app.state.merger = None

        yield

    # Shutdown
    logger.info("Server shutting down...")
    if hasattr(app.state, 'cleanup_task') and app.state.cleanup_task:
        app.state.cleanup_task.cancel()
        try:
            await app.state.cleanup_task
        except asyncio.CancelledError:
            logger.info("Background cleanup task cancelled.")

    if hasattr(app.state, 'merger') and app.state.merger:
        await app.state.merger.shutdown()
        logger.info("StreamlineVPNMerger shut down successfully.")

    logger.info("Aiohttp session closed.")
    logger.info("Shutdown complete.")