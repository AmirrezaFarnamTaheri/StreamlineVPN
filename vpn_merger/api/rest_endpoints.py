from fastapi import FastAPI, Request, HTTPException
from fastapi.routing import APIRouter
from fastapi.responses import PlainTextResponse, JSONResponse
import time
from pathlib import Path
import json

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


def _read_output(filename: str) -> str:
    base = Path("output")
    path = base / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    # guard excessive size
    data = path.read_text(encoding="utf-8", errors="ignore")
    if len(data) > 5_000_000:  # 5MB cap for HTTP response
        return data[:5_000_000]
    return data


@api.get("/sub/base64")
def sub_base64() -> PlainTextResponse:
    return PlainTextResponse(_read_output("vpn_subscription_base64.txt"))


@api.get("/sub/raw")
def sub_raw() -> PlainTextResponse:
    return PlainTextResponse(_read_output("vpn_subscription_raw.txt"))


@api.get("/sub/singbox")
def sub_singbox() -> JSONResponse:
    text = _read_output("vpn_singbox.json")
    try:
        obj = json.loads(text)
    except Exception:
        obj = {"raw": text}
    return JSONResponse(content=obj)


@api.get("/sub/report")
def sub_report() -> JSONResponse:
    text = _read_output("vpn_report.json")
    try:
        obj = json.loads(text)
    except Exception:
        obj = {"raw": text}
    return JSONResponse(content=obj)


@api.get("/stats/latest")
def latest_stats() -> JSONResponse:
    """Return a compact summary of the latest run statistics.

    Combines `vpn_report.json` (if present) and DB quarantine count.
    """
    out = {
        "timestamp": None,
        "processing_time_seconds": None,
        "total_configs": 0,
        "reachable_configs": 0,
        "total_sources": 0,
        "quarantined_sources": 0,
    }
    # Try reading JSON report
    try:
        text = _read_output("vpn_report.json")
        rep = json.loads(text)
        gi = rep.get("generation_info", {})
        st = rep.get("statistics", {})
        out.update({
            "timestamp": gi.get("timestamp_utc"),
            "processing_time_seconds": gi.get("processing_time_seconds"),
            "total_configs": st.get("total_configs", 0),
            "reachable_configs": st.get("reachable_configs", 0),
            "total_sources": rep.get("source_categories", {}).get("total_unique_sources", 0),
        })
    except Exception:
        pass
    # Count quarantined from DB
    try:
        from vpn_merger.storage.database import VPNDatabase  # type: ignore
        db = VPNDatabase()
        out["quarantined_sources"] = len(db.get_quarantined_sources())
    except Exception:
        pass
    return JSONResponse(content=out)


app.include_router(api)


