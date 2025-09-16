"""
Source management routes.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException

sources_router = APIRouter()


class SourceRoutes:
    @staticmethod
    def _get_merger():
        try:
            from ...unified_api import get_merger  # type: ignore
            return get_merger()  # may be overridden in tests
        except Exception:
            return None


@sources_router.get("/sources")
async def get_sources():
    """Get all configured sources."""
    try:
        from ...core.source.manager import SourceManager
        
        source_manager = SourceManager()
        sources = source_manager.get_all_sources()
        
        return {
            "sources": sources,
            "count": len(sources),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sources: {str(e)}")


@sources_router.post("/sources")
async def add_source(source_data: Dict[str, Any]):
    """Add a new source."""
    try:
        from ...core.source.manager import SourceManager
        
        source_manager = SourceManager()
        success = source_manager.add_source(source_data)
        
        if success:
            return {"status": "success", "message": "Source added successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add source")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add source: {str(e)}")


@sources_router.put("/sources/{source_id}")
async def update_source(source_id: str, source_data: Dict[str, Any]):
    """Update an existing source."""
    try:
        from ...core.source.manager import SourceManager
        
        source_manager = SourceManager()
        success = source_manager.update_source(source_id, source_data)
        
        if success:
            return {"status": "success", "message": "Source updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Source not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update source: {str(e)}")


@sources_router.delete("/sources/{source_id}")
async def delete_source(source_id: str):
    """Delete a source."""
    try:
        from ...core.source.manager import SourceManager
        
        source_manager = SourceManager()
        success = source_manager.delete_source(source_id)
        
        if success:
            return {"status": "success", "message": "Source deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Source not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete source: {str(e)}")


@sources_router.post("/sources/{source_id}/refresh")
async def refresh_source(source_id: str):
    """Refresh a specific source."""
    try:
        from ...core.source.manager import SourceManager
        
        source_manager = SourceManager()
        success = source_manager.refresh_source(source_id)
        
        if success:
            return {"status": "success", "message": "Source refreshed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Source not found or refresh failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh source: {str(e)}")


@sources_router.get("/sources/{source_id}/status")
async def get_source_status(source_id: str):
    """Get source status and health."""
    try:
        from ...core.source.manager import SourceManager
        
        source_manager = SourceManager()
        status = source_manager.get_source_status(source_id)
        
        if status:
            return {"status": "success", "data": status}
        else:
            raise HTTPException(status_code=404, detail="Source not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get source status: {str(e)}")
