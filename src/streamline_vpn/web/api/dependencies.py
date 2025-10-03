from fastapi import Request, HTTPException, status
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.merger import StreamlineVPNMerger


def get_merger(request: Request) -> "StreamlineVPNMerger":
    """
    Dependency to get the merger instance from the application state.
    This is called for each request that needs access to the merger.
    """
    if not hasattr(request.app.state, "merger") or request.app.state.merger is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Merger service is not available or has not been initialized.",
        )
    return request.app.state.merger