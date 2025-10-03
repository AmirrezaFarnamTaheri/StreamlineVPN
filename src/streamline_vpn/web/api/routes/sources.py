from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.web.dependencies import get_merger
from streamline_vpn.web.models import AddSourceRequest

sources_router = APIRouter(prefix="/api/v1/sources", tags=["Sources"])

@sources_router.get("")
async def get_sources(merger: StreamlineVPNMerger = Depends(get_merger)) -> Dict[str, Any]:
    """Return information about configured sources."""
    if not hasattr(merger, "source_manager"):
        raise HTTPException(status_code=503, detail="Source manager not available")
    return merger.source_manager.get_source_statistics()

@sources_router.post("/add", status_code=status.HTTP_201_CREATED)
async def add_source(
    request: AddSourceRequest, merger: StreamlineVPNMerger = Depends(get_merger)
) -> Dict[str, str]:
    """Add a new source to the manager."""
    if not hasattr(merger, "source_manager"):
        raise HTTPException(status_code=503, detail="Source manager not available")
    try:
        await merger.source_manager.add_source(str(request.url))
        return {"message": f"Source {request.url} added successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@sources_router.post("/{source_url:path}/blacklist")
async def blacklist_source(
    source_url: str, reason: str = "", merger: StreamlineVPNMerger = Depends(get_merger)
) -> Dict[str, str]:
    """Blacklist a source."""
    if not hasattr(merger, "source_manager"):
        raise HTTPException(status_code=503, detail="Source manager not available")
    merger.source_manager.blacklist_source(source_url, reason)
    return {"message": f"Source {source_url} blacklisted"}

@sources_router.post("/{source_url:path}/whitelist")
async def whitelist_source(
    source_url: str, merger: StreamlineVPNMerger = Depends(get_merger)
) -> Dict[str, str]:
    """Remove a source from the blacklist."""
    if not hasattr(merger, "source_manager"):
        raise HTTPException(status_code=503, detail="Source manager not available")
    merger.source_manager.whitelist_source(source_url)
    return {"message": f"Source {source_url} whitelisted"}