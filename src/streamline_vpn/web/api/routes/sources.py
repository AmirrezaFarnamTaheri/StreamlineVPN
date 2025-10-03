from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from streamline_vpn.core.merger import StreamlineVPNMerger
from ..dependencies import get_merger
from ..models import AddSourceRequest

sources_router = APIRouter(prefix="/api/v1/sources", tags=["Sources"])


@sources_router.get("/", response_model=Dict[str, Any])
async def get_sources(merger: StreamlineVPNMerger = Depends(get_merger)) -> Dict[str, Any]:
    """Return information about configured sources."""
    if not (hasattr(merger, "source_manager") and merger.source_manager):
        return {"sources": []}

    source_infos = []
    for src in merger.source_manager.sources.values():
        last_check = getattr(src, "last_check", None)
        source_infos.append({
            "url": getattr(src, "url", None),
            "status": "active" if getattr(src, "enabled", True) else "disabled",
            "configs": getattr(src, "avg_config_count", 0),
            "last_update": last_check.isoformat() if isinstance(last_check, datetime) else None,
            "success_rate": getattr(src, "reputation_score", 0.0),
        })
    return {"sources": source_infos}


@sources_router.post("/add", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
async def add_source(
    request: AddSourceRequest, merger: StreamlineVPNMerger = Depends(get_merger)
) -> Dict[str, Any]:
    """Add a new source to the manager."""
    try:
        await merger.source_manager.add_source(request.url.strip())
        return {"status": "success", "message": f"Source added: {request.url}"}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add source: {exc}",
        )


@sources_router.post("/{source_url:path}/blacklist", response_model=Dict[str, str])
async def blacklist_source(
    source_url: str, reason: str = "", merger: StreamlineVPNMerger = Depends(get_merger)
) -> Dict[str, str]:
    """Blacklist a source."""
    merger.source_manager.blacklist_source(source_url, reason)
    return {"message": f"Source {source_url} blacklisted"}


@sources_router.post("/{source_url:path}/whitelist", response_model=Dict[str, str])
async def whitelist_source(
    source_url: str, merger: StreamlineVPNMerger = Depends(get_merger)
) -> Dict[str, str]:
    """Remove a source from the blacklist."""
    merger.source_manager.whitelist_source(source_url)
    return {"message": f"Source {source_url} whitelisted"}