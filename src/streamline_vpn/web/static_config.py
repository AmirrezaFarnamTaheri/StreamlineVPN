from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from ..utils.logging import get_logger

logger = get_logger(__name__)

def mount_static_files(app: FastAPI):
    """
    Mounts the static files directories to the FastAPI application.
    This should be called *after* all API routes have been registered.
    """
    project_root = Path(__file__).resolve().parents[3]
    static_dir = project_root / "docs"

    if not static_dir.is_dir():
        logger.warning(f"Static files directory not found at: {static_dir}")
        return

    try:
        # Mount the 'assets' directory first at its specific path
        assets_path = static_dir / "assets"
        if assets_path.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
            logger.info(f"Mounted /assets from {assets_path}")

        # Mount the root static directory to serve index.html and other root files
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static_root")
        logger.info(f"Mounted static root / from {static_dir}")

    except Exception as e:
        logger.error(f"Failed to mount static files: {e}", exc_info=True)