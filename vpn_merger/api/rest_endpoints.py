from fastapi import FastAPI, Request
from fastapi.routing import APIRouter
import time

_WINDOW_SECONDS = 10.0
_MAX_REQUESTS = 30
_visitors: dict[str, list[float]] = {}


app = FastAPI()
api = APIRouter(prefix="/api/v1")


def _allow(req: Request) -> bool:
    ip = req.client.host if req.client else "unknown"
    now = time.time()
    hist = _visitors.setdefault(ip, [])
    # drop old
    cutoff = now - _WINDOW_SECONDS
    while hist and hist[0] < cutoff:
        hist.pop(0)
    if len(hist) >= _MAX_REQUESTS:
        return False
    hist.append(now)
    return True


@api.get("/health")
def health() -> dict:
    return {"status": "ok"}


@api.get("/limits")
def limits(req: Request) -> dict:
    allowed = _allow(req)
    return {"allowed": allowed, "window_s": _WINDOW_SECONDS, "max_requests": _MAX_REQUESTS}


app.include_router(api)


