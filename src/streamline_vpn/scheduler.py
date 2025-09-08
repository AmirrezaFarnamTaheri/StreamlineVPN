# src/streamline_vpn/scheduler.py
"""Background scheduler for periodic processing."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .utils.logging import get_logger
from .core.merger import StreamlineVPNMerger


logger = get_logger(__name__)
scheduler = None


def setup_scheduler():
    """Setup the background scheduler."""
    global scheduler

    if scheduler is not None:
        return scheduler

    scheduler = AsyncIOScheduler()

    # Schedule processing every 8 hours
    scheduler.add_job(
        run_processing,
        'interval',
        hours=8,
        id='process_sources',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started - processing will run every 8 hours")
    return scheduler


async def run_processing():
    """Run the processing pipeline."""
    try:
        logger.info("Starting scheduled processing...")
        merger = StreamlineVPNMerger()
        await merger.initialize()
        result = await merger.process_all()
        logger.info(f"Scheduled processing completed: {result}")
    except Exception as e:
        logger.error(f"Scheduled processing failed: {e}")
