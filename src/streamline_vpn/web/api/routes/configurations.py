from typing import Any, Dict, Optional, List

from fastapi import APIRouter, Depends

from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.web.dependencies import get_merger

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
    configs = merger.get_configurations(
        protocol=protocol, location=location, min_quality=min_quality
    )
    total = len(configs)
    paginated_configs = configs[offset : offset + limit]
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "configurations": [c.to_dict() for c in paginated_configs],
    }