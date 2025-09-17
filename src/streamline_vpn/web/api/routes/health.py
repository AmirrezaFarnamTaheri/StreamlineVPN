"""
Health check routes.
"""

from fastapi import APIRouter

health_router = APIRouter()


class HealthRoutes:
    @staticmethod
    def _get_merger():
        try:
            from ...unified_api import get_merger  # type: ignore

            return get_merger()
        except Exception:
            return None


@health_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "StreamlineVPN",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z",
    }


@health_router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component status."""
    try:
        # Check core components
        from ...core.source.manager import SourceManager
        from ...core.merger import StreamlineVPNMerger

        source_manager = SourceManager()
        merger = StreamlineVPNMerger()

        # Get basic stats
        sources = source_manager.get_all_sources()

        return {
            "status": "healthy",
            "service": "StreamlineVPN",
            "version": "1.0.0",
            "components": {
                "source_manager": "healthy",
                "merger": "healthy",
                "api": "healthy",
            },
            "statistics": {"sources_count": len(sources), "uptime": "unknown"},
            "timestamp": "2024-01-01T00:00:00Z",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "StreamlineVPN",
            "version": "1.0.0",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z",
        }
