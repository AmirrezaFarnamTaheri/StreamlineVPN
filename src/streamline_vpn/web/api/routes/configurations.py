from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends

from streamline_vpn.core.merger import StreamlineVPNMerger
from ..dependencies import get_merger

configurations_router = APIRouter(tags=["Configurations"])


@configurations_router.get("/configurations", response_model=Dict[str, Any])
async def get_all_configurations(
    merger: StreamlineVPNMerger = Depends(get_merger),
) -> Dict[str, Any]:
    """Get all processed VPN configurations from the merger."""
    configs = merger.get_configurations()
    return {
        "count": len(configs),
        "configurations": [
            config.to_dict() if hasattr(config, "to_dict") else config
            for config in configs
        ],
    }


@configurations_router.get("/api/v1/configurations", response_model=Dict[str, Any])
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
    paginated_configs = configs[offset : offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "configurations": [c.to_dict() for c in paginated_configs],
    }