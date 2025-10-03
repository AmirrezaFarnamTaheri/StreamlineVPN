from typing import Any, Dict, Optional, List

from fastapi import APIRouter, Depends

from .....core.merger import StreamlineVPNMerger
from ...dependencies import get_merger

configurations_router = APIRouter(prefix="/api/v1/configurations", tags=["Configurations"])

@configurations_router.get("")
async def get_filtered_configurations(
    protocol: Optional[str] = None,
    location: Optional[str] = None,
    min_quality: float = 0.0,
    limit: int = 100,
    offset: int = 0,
    merger: StreamlineVPNMerger = Depends(get_merger),
) -> Dict[str, Any]:
    """Return processed configurations with filtering and pagination."""
    configs = merger.get_configurations()
    if protocol:
        configs = [c for c in configs if c.protocol.value == protocol]
    if location:
        configs = [c for c in configs if c.metadata.get("location") == location]
    if min_quality > 0:
        configs = [c for c in configs if c.quality_score >= min_quality]
    total = len(configs)
    configs = configs[offset : offset + limit]
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "configurations": [c.to_dict() for c in configs],
    }