from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks, Query
from typing import Dict
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
from fastapi.responses import PlainTextResponse, JSONResponse
import time
from pathlib import Path
import os
import json

_WINDOW_SECONDS = 10.0
_MAX_REQUESTS = 30
_visitors: dict[str, list[float]] = {}
_tenant_visitors: dict[str, list[float]] = {}


app = FastAPI()
api = APIRouter(prefix="/api/v1")


def _tenant_from_token(req: Request) -> str | None:
    # TENANT_TOKENS supports two formats:
    # 1) Mapping: "tenantA:keyA,tenantB:keyB" (token maps to a tenant)
    # 2) Allowlist: "tenantA,tenantB" and client supplies header x-tenant or query param tenant
    import os
    mapping = os.environ.get("TENANT_TOKENS")
    token = req.headers.get("x-api-token") or req.query_params.get("token")
    if not mapping:
        return None
    entries = [p.strip() for p in mapping.split(",") if p.strip()]
    # Mapping form
    if any(":" in e for e in entries):
        if not token:
            return None
        for e in entries:
            if ":" in e:
                tenant, key = e.split(":", 1)
                if key == token:
                    return tenant
        return None
    # Allowlist form
    tenant = req.headers.get("x-tenant") or req.query_params.get("tenant")
    if tenant and tenant in entries:
        return tenant
    return None


def _allow(req: Request) -> bool:
    ip = req.client.host if req.client else "unknown"
    tenant = _tenant_from_token(req) or "__no_tenant__"
    now = time.time()
    hist = _visitors.setdefault(ip, [])
    thist = _tenant_visitors.setdefault(tenant, [])
    # drop old
    cutoff = now - _WINDOW_SECONDS
    while hist and hist[0] < cutoff:
        hist.pop(0)
    while thist and thist[0] < cutoff:
        thist.pop(0)
    if len(hist) >= _MAX_REQUESTS:
        return False
    if len(thist) >= _MAX_REQUESTS:
        return False
    hist.append(now)
    thist.append(now)
    return True

def _check_token(req: Request):
    import os
    token = os.environ.get("API_TOKEN")
    if not token:
        return
    supplied = req.headers.get("x-api-token") or req.query_params.get("token")
    if supplied != token:
        raise HTTPException(status_code=401, detail="Unauthorized")


@api.get("/health")
def health() -> dict:
    return {"status": "ok"}

@api.get("/ready")
def ready() -> dict:
    # Basic readiness: process alive and recent events log writable
    try:
        from vpn_merger.monitoring.event_store import append_event  # type: ignore
        append_event({"type": "ready_probe", "ts": time.time(), "data": {}})
    except Exception:
        return {"ready": False}
    return {"ready": True}


@api.get("/limits")
def limits(req: Request) -> dict:
    allowed = _allow(req)
    return {"allowed": allowed, "window_s": _WINDOW_SECONDS, "max_requests": _MAX_REQUESTS}


def _tenant_output_dir(req: Request | None) -> Path:
    import os
    base = Path(os.environ.get("OUTPUT_DIR") or "output")
    tenant = _tenant_from_token(req) if req is not None else None
    if tenant:
        return base / "tenants" / tenant
    return base


def _read_output(filename: str, base: Path) -> str:
    path = base / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    # guard excessive size
    data = path.read_text(encoding="utf-8", errors="ignore")
    if len(data) > 5_000_000:  # 5MB cap for HTTP response
        return data[:5_000_000]
    return data


@api.get("/sub/base64")
def sub_base64(req: Request, _: None = Depends(_check_token)) -> PlainTextResponse:
    if not _allow(req):
        raise HTTPException(status_code=429, detail="Rate limit")
    base = _tenant_output_dir(req)
    return PlainTextResponse(_read_output("vpn_subscription_base64.txt", base))


@api.get("/sub/raw")
def sub_raw(req: Request, _: None = Depends(_check_token)) -> PlainTextResponse:
    if not _allow(req):
        raise HTTPException(status_code=429, detail="Rate limit")
    base = _tenant_output_dir(req)
    return PlainTextResponse(_read_output("vpn_subscription_raw.txt", base))


@api.get("/sub/singbox")
def sub_singbox(req: Request, _: None = Depends(_check_token)) -> JSONResponse:
    if not _allow(req):
        raise HTTPException(status_code=429, detail="Rate limit")
    base = _tenant_output_dir(req)
    text = _read_output("vpn_singbox.json", base)
    try:
        obj = json.loads(text)
    except Exception:
        obj = {"raw": text}
    return JSONResponse(content=obj)


@api.get("/sub/report")
def sub_report(req: Request, _: None = Depends(_check_token)) -> JSONResponse:
    if not _allow(req):
        raise HTTPException(status_code=429, detail="Rate limit")
    base = _tenant_output_dir(req)
    text = _read_output("vpn_report.json", base)
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


@api.post("/run/merge")
async def run_merge_endpoint(
    background: BackgroundTasks,
    formats: str | None = Query(default=None, description="Space/comma-separated formats"),
    limit: int | None = Query(default=None),
    req: Request = None,
):
    if req is not None and not _allow(req):
        raise HTTPException(status_code=429, detail="Rate limit")
    """Trigger a background merge run using the core merger."""
    try:
        from vpn_merger.core.merger import Merger  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Core merger unavailable: {e}")

    fmts = None
    if formats:
        parts = [p.strip().lower() for p in formats.replace(",", " ").split() if p.strip()]
        fmts = set(parts)

    async def _run():
        m = Merger()
        # Set per-tenant output dir
        import os as _os
        tenant_dir = _tenant_output_dir(req)
        try:
            from vpn_merger import vpn_merger as _root  # type: ignore
            _root.CONFIG.output_dir = str(tenant_dir)
        except Exception:
            pass
        # Also set OUTPUT_DIR for event/run stores
        _os.environ["OUTPUT_DIR"] = str(tenant_dir)
        if limit:
            try:
                m.sources = m.sources[: int(limit)]
            except Exception:
                pass
        await m.run(formats=fmts)

    background.add_task(_run)
    return {"started": True, "formats": sorted(list(fmts)) if fmts else None, "limit": limit}


@api.get("/discover")
async def discover(limit: int = 100, req: Request | None = None) -> JSONResponse:
    if req is not None and not _allow(req):
        raise HTTPException(status_code=429, detail="Rate limit")
    try:
        from vpn_merger.sources.discovery import discover_all  # type: ignore
        urls = await discover_all(limit=limit)
        return JSONResponse(content={"count": len(urls), "urls": urls})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.post("/validate")
async def validate(payload: Dict, req: Request | None = None) -> JSONResponse:
    if req is not None and not _allow(req):
        raise HTTPException(status_code=429, detail="Rate limit")
    urls = list(payload.get("urls") or [])
    min_score = float(payload.get("min_score") or 0.5)
    try:
        from vpn_merger.core.merger import Merger  # type: ignore
        m = Merger()
        res = await m.validate_sources(urls, min_score=min_score)
        return JSONResponse(content={"results": [[u, s] for (u, s) in res]})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.post("/format")
async def format_configs(payload: Dict, req: Request | None = None) -> PlainTextResponse:
    if req is not None and not _allow(req):
        raise HTTPException(status_code=429, detail="Rate limit")
    t = str(payload.get("type") or "raw").lower()
    lines = [str(x) for x in (payload.get("lines") or [])]
    if t == "base64":
        from vpn_merger.output.formatters.base64 import to_base64
        return PlainTextResponse(to_base64(lines))
    if t == "clash":
        from vpn_merger.output.formatters.clash import to_clash_yaml
        return PlainTextResponse(to_clash_yaml(lines))
    if t == "singbox":
        from vpn_merger.output.formatters.singbox import to_singbox_json
        return PlainTextResponse(to_singbox_json(lines))
    if t == "csv":
        from vpn_merger.output.formatters.csv import to_csv
    return PlainTextResponse(to_csv(lines))
    return PlainTextResponse("\n".join(lines))


@api.post("/filter")
async def filter_configs(payload: Dict, req: Request | None = None) -> PlainTextResponse:
    if req is not None and not _allow(req):
        raise HTTPException(status_code=429, detail="Rate limit")
    include = set([str(x).lower() for x in (payload.get("include") or [])]) if payload.get("include") else None
    exclude = set([str(x).lower() for x in (payload.get("exclude") or [])]) if payload.get("exclude") else set()
    lines = [str(x) for x in (payload.get("lines") or [])]
    out = []
    for l in lines:
        proto = l.split("://", 1)[0].lower()
        if include is not None and proto not in include:
            continue
        if proto in exclude:
            continue
        out.append(l)
    return PlainTextResponse("\n".join(out))


@api.post("/score")
async def score_configs(payload: Dict, req: Request | None = None) -> PlainTextResponse:
    if req is not None and not _allow(req):
        raise HTTPException(status_code=429, detail="Rate limit")
    top = int(payload.get("top") or 100)
    lines = [str(x) for x in (payload.get("lines") or [])]
    try:
        from vpn_merger.core.merger import Merger  # type: ignore
        m = Merger()
        sorted_lines = m.score_and_sort(lines)
    except Exception:
        sorted_lines = lines
    if top > 0:
        sorted_lines = sorted_lines[:top]
    return PlainTextResponse("\n".join(sorted_lines))


@api.post("/export")
async def export(payload: Dict, req: Request | None = None) -> JSONResponse:
    if req is not None and not _allow(req):
        raise HTTPException(status_code=429, detail="Rate limit")
    # Resolve output directory securely under a configured base directory
    base_out = Path(os.environ.get("OUTPUT_DIR") or "output")
    try:
        from vpn_merger.security.security_manager import SecurityManager  # type: ignore
        outdir = SecurityManager.secure_path(base_out, str(payload.get("output_dir") or "."))
    except Exception:
        outdir = base_out.resolve()
    formats = [str(x).lower() for x in (payload.get("formats") or [])]
    lines = [str(x) for x in (payload.get("lines") or [])]
    outdir.mkdir(parents=True, exist_ok=True)
    written = []
    from vpn_merger.output.writer import atomic_write_async
    if "raw" in formats:
        p = outdir / "vpn_subscription_raw.txt"
        await atomic_write_async(p, "\n".join(lines))
        written.append(str(p))
    if "base64" in formats:
        from vpn_merger.output.formatters.base64 import to_base64
        p = outdir / "vpn_subscription_base64.txt"
        await atomic_write_async(p, to_base64(lines))
        written.append(str(p))
    if "csv" in formats:
        from vpn_merger.output.formatters.csv import to_csv
        p = outdir / "vpn_detailed.csv"
        await atomic_write_async(p, to_csv(lines))
        written.append(str(p))
    if "singbox" in formats:
        from vpn_merger.output.formatters.singbox import to_singbox_json
        p = outdir / "vpn_singbox.json"
        await atomic_write_async(p, to_singbox_json(lines))
        written.append(str(p))
    if "clash" in formats:
        from vpn_merger.output.formatters.clash import to_clash_yaml
        p = outdir / "clash.yaml"
        await atomic_write_async(p, to_clash_yaml(lines))
        written.append(str(p))
    return JSONResponse(content={"written": written})


@api.get("/runs")
def runs(limit: int = 50, req: Request | None = None) -> JSONResponse:
    if req is not None and not _allow(req):
        raise HTTPException(status_code=429, detail="Rate limit")
    try:
        from vpn_merger.monitoring.run_store import tail_runs  # type: ignore
        return JSONResponse(content={"runs": tail_runs(limit)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(api)

# Events endpoints for live dashboards
@app.get("/api/v1/events")
def get_events(limit: int = 100, req: Request | None = None) -> JSONResponse:
    if req is not None and not _allow(req):
        raise HTTPException(status_code=429, detail="Rate limit")
    try:
        from vpn_merger.monitoring.event_store import tail_events  # type: ignore
        return JSONResponse(content={"events": tail_events(limit)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
def metrics_endpoint() -> Response:
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/dashboard/events")
def dashboard_events() -> HTMLResponse:
    html = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>VPN Merger Events</title>
    <style>
      body { font-family: system-ui, sans-serif; margin: 20px; }
      #log { white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; border: 1px solid #ccc; padding: 10px; height: 60vh; overflow: auto; }
      #charts { display: flex; gap: 20px; }
      canvas { background: #fafafa; border: 1px solid #ddd; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  </head>
  <body>
    <h2>Real-time Events</h2>
    <div>
      <label>Types (comma): <input id="types" value="fetch_progress,output_written"/></label>
      <label>Run ID: <input id="runid"/></label>
      <button onclick="start()">Start</button>
    </div>
    <div id="charts">
      <div>
        <h4>Fetch Progress</h4>
        <canvas id="progressChart" width="400" height="200"></canvas>
      </div>
      <div>
        <h4>Run Counters</h4>
        <canvas id="runsChart" width="400" height="200"></canvas>
      </div>
      <div>
        <h4>System Metrics</h4>
        <canvas id="cpuChart" width="400" height="200"></canvas>
        <canvas id="memChart" width="400" height="200"></canvas>
      </div>
    </div>
    <div id="log"></div>
    <script>
      let es;
      let progChart, runsChart, cpuChart, memChart;
      const progData = { labels: [], datasets: [{label: 'Done', data: [], borderColor: '#36a2eb'},{label:'Total', data: [], borderColor:'#ff6384'}] };
      const runData = { labels: [], datasets: [{label: 'Configs', data: [], borderColor:'#4bc0c0'},{label:'Reachable', data: [], borderColor:'#9966ff'}] };
      const cpuData = { labels: [], datasets: [{label: 'CPU %', data: [], borderColor:'#ff9f40'}] };
      const memData = { labels: [], datasets: [{label: 'RSS Bytes', data: [], borderColor:'#ffcd56'}] };
      function initCharts(){
        const pc = document.getElementById('progressChart').getContext('2d');
        const rc = document.getElementById('runsChart').getContext('2d');
        const cc = document.getElementById('cpuChart').getContext('2d');
        const mc = document.getElementById('memChart').getContext('2d');
        progChart = new Chart(pc, {type:'line', data:progData, options:{animation:false, scales:{x:{display:false}}}});
        runsChart = new Chart(rc, {type:'line', data:runData, options:{animation:false, scales:{x:{display:false}}}});
        cpuChart = new Chart(cc, {type:'line', data:cpuData, options:{animation:false, scales:{x:{display:false}, y:{min:0, max:100}}}});
        memChart = new Chart(mc, {type:'line', data:memData, options:{animation:false, scales:{x:{display:false}}}});
      }
      function start(){
        if (es) es.close();
        if (!progChart) initCharts();
        const t = document.getElementById('types').value;
        const r = document.getElementById('runid').value;
        const qs = new URLSearchParams();
        if (t) qs.set('types', t);
        if (r) qs.set('run_id', r);
        es = new EventSource('/api/v1/events/stream?' + qs.toString());
        const log = document.getElementById('log');
        es.onmessage = (ev) => {
          const data = JSON.parse(ev.data);
          const pre = document.createElement('div');
          pre.textContent = new Date(data.ts*1000).toISOString() + ' ' + data.type + ' ' + JSON.stringify(data.data);
          log.appendChild(pre);
          log.scrollTop = log.scrollHeight;
          if (data.type === 'fetch_progress'){
            const d = data.data||{};
            progData.labels.push('');
            progData.datasets[0].data.push(d.done||0);
            progData.datasets[1].data.push(d.total||0);
            progChart.update('none');
          }
          if (data.type === 'run_done'){
            const d = data.data||{};
            runData.labels.push('');
            runData.datasets[0].data.push(d.total||d.total_configs||0);
            runData.datasets[1].data.push(d.reachable||0);
            runsChart.update('none');
          }
        };
        es.onerror = (e) => {
          const pre = document.createElement('div');
          pre.textContent = 'SSE error, retrying...';
          log.appendChild(pre);
        };
      }
      async function pollMetrics(){
        try{
          const res = await fetch('/metrics');
          const text = await res.text();
          const cpuLine = text.split('\n').find(l => l.startsWith('vpn_merger_cpu_usage_percent')) || '';
          const memLine = text.split('\n').find(l => l.startsWith('vpn_merger_memory_usage_bytes')) || '';
          const cpu = parseFloat((cpuLine.match(/ (\d+\.?\d*)$/)||[])[1]||'0');
          const mem = parseFloat((memLine.match(/ (\d+\.?\d*)$/)||[])[1]||'0');
          cpuData.labels.push(''); cpuData.datasets[0].data.push(cpu); cpuChart.update('none');
          memData.labels.push(''); memData.datasets[0].data.push(mem); memChart.update('none');
        }catch(e){/* ignore */}
      }
      setInterval(pollMetrics, 5000);
    </script>
  </body>
</html>
"""
    return HTMLResponse(html)


@app.get("/api/v1/events/stream")
async def stream_events(types: str | None = Query(default=None), run_id: str | None = Query(default=None), token: str | None = Query(default=None), request: Request = None):
    import json
    import asyncio
    from vpn_merger.monitoring.event_store import register_listener, unregister_listener, get_last_event_id, set_last_event_id, tail_events  # type: ignore
    import os

    expected = os.environ.get("API_TOKEN")
    if expected and token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    q = register_listener()

    filter_types = set([t.strip() for t in types.replace(",", " ").split()]) if types else None
    wanted_run = run_id

    async def event_gen():
        try:
            # initial backlog if Last-Event-ID provided
            last_id = None
            try:
                hdr = request.headers.get("last-event-id") if request else None
                if hdr:
                    last_id = float(hdr)
            except Exception:
                last_id = None
            client_id = request.headers.get("x-client-id") if request else None
            if last_id is None and client_id:
                try:
                    stored = get_last_event_id(client_id)
                    if stored is not None:
                        last_id = float(stored)
                except Exception:
                    pass
            if last_id is not None:
                try:
                    import json as _json
                    for ev in tail_events(500):
                        ts = float(ev.get("ts", 0.0))
                        if ts > last_id:
                            if filter_types and str(ev.get("type", "")) not in filter_types:
                                continue
                            if wanted_run is not None:
                                data = ev.get("data") or {}
                                if str(data.get("run_id")) != wanted_run:
                                    continue
                            yield "retry: 3000\n"
                            yield f"id: {ts}\n"
                            yield f"data: {_json.dumps(ev, ensure_ascii=False)}\n\n"
                except Exception:
                    pass
            while True:
                try:
                    ev = await asyncio.wait_for(q.get(), timeout=10.0)
                    et = str(ev.get("type", ""))
                    if filter_types and et not in filter_types:
                        continue
                    if wanted_run is not None:
                        data = ev.get("data") or {}
                        if str(data.get("run_id")) != wanted_run:
                            continue
                    ts = float(ev.get("ts", 0.0))
                    if client_id:
                        try:
                            set_last_event_id(client_id, ts)
                        except Exception:
                            pass
                    yield "retry: 3000\n"
                    yield f"id: {ts}\n"
                    yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    # heartbeat
                    yield "retry: 3000\n"
                    yield ": keepalive\n\n"
        finally:
            unregister_listener(q)
    headers = {
        "Cache-Control": "no-cache, no-transform",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    }
    return StreamingResponse(event_gen(), media_type="text/event-stream", headers=headers)


@app.websocket("/api/v1/events/ws")
async def ws_events(ws: WebSocket):
    await ws.accept()
    from vpn_merger.monitoring.event_store import register_listener, unregister_listener  # type: ignore
    import json
    # Simple token auth via query param
    try:
        import os
        expected = os.environ.get("API_TOKEN")
        if expected:
            supplied = ws.query_params.get("token")
            if supplied != expected:
                await ws.close(code=4401)
                return
    except Exception:
        pass
    # Optional filters
    types_param = ws.query_params.get("types")
    filter_types = set([t.strip() for t in types_param.replace(",", " ").split()]) if types_param else None
    run_id_filter = ws.query_params.get("run_id")
    q = register_listener()
    try:
        while True:
            ev = await q.get()
            et = str(ev.get("type", ""))
            if filter_types and et not in filter_types:
                continue
            if run_id_filter is not None:
                data = ev.get("data") or {}
                if str(data.get("run_id")) != run_id_filter:
                    continue
            await ws.send_text(json.dumps(ev, ensure_ascii=False))
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await ws.close()
        except Exception:
            pass
    finally:
        unregister_listener(q)


