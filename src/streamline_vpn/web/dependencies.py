from fastapi import Request, HTTPException, status
from ..core.merger import StreamlineVPNMerger

def get_merger(request: Request) -> StreamlineVPNMerger:
    """Get merger instance from application state."""
    if not hasattr(request.app.state, "merger") or not request.app.state.merger:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Merger not initialized",
        )
    return request.app.state.merger