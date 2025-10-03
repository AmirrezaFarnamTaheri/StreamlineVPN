from typing import Any, Dict, Optional, List

from fastapi import APIRouter, Depends

from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.web.dependencies import get_merger

configurations_router = APIRouter(prefix="/api/v1/configurations", tags=["Configurations"])

from fastapi import APIRouter, Depends, Query

@configurations_router.get("")
async def get_filtered_configurations(
    protocol: Optional[str] = None,
    location: Optional[str] = None,
    min_quality: float = 0.0,
    limit: int = Query(100, ge=0, le=1000),
    offset: int = Query(0, ge=0),
    merger: StreamlineVPNMerger = Depends(get_merger),
) -> Dict[str, Any]:
    """Return processed configurations with filtering and pagination."""
    configs = merger.get_configurations(
        protocol=protocol, location=location, min_quality=min_quality
    )
    total = len(configs)
    paginated_configs = configs[offset : offset + limit]

    def _to_dict(c: Any) -> Dict[str, Any]:
        if hasattr(c, "to_dict"):
            return c.to_dict()  # type: ignore[no-any-return]
        if isinstance(c, dict):
            # Normalize protocol enum if present
            p = c.get("protocol")
            if hasattr(p, "value"):
                c = dict(c)
                c["protocol"] = p.value
            return c
        # Fallback best-effort
        d = getattr(c, "__dict__", {}) or {}
        if "protocol" in d and hasattr(d["protocol"], "value"):
            d = dict(d)
            d["protocol"] = d["protocol"].value
        return d

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "configurations": [_to_dict(c) for c in paginated_configs],
    }