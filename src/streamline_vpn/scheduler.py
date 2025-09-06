from apscheduler.schedulers.asyncio import AsyncIOScheduler
from streamline_vpn.__main__ import main as run_pipeline_main
import asyncio


def setup_scheduler():
    """
    Initializes and starts the scheduler.
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_pipeline_job, "interval", hours=12)
    scheduler.start()
    print("Scheduler started, pipeline will run every 12 hours.")


async def run_pipeline_job():
    """
    A wrapper for the run_pipeline function to be used with the scheduler.
    """
    print("Running scheduled VPN data update...")
    try:
        # Call the main function from __main__.py with default arguments
        await run_pipeline_main("config/sources.yaml", "output", None)
        print("VPN data update completed successfully.")
    except Exception as e:
        print(f"An error occurred during the scheduled VPN data update: {e}")


if __name__ == "__main__":
    setup_scheduler()
    # Keep the script running
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
