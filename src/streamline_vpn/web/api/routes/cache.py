from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status

from streamline_vpn.core.merger import StreamlineVPNMerger
from ..dependencies import get_merger

cache_router = APIRouter(prefix="/cache", tags=["Cache"])


@cache_router.post("/clear", response_model=Dict[str, str])
async def clear_cache(merger: StreamlineVPNMerger = Depends(get_merger)) -> Dict[str, str]:
    """Clear all caches (L1, L2, L3)."""
    try:
        await merger.clear_cache()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {e}",
        )