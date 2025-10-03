from fastapi import APIRouter, Depends

from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.web.dependencies import get_merger

cache_router = APIRouter(prefix="/api/v1/cache", tags=["Cache"])

@cache_router.post("/clear")
async def clear_cache(merger: StreamlineVPNMerger = Depends(get_merger)):
    """Clear all caches."""
    await merger.clear_cache()
    return {"message": "Cache cleared successfully"}