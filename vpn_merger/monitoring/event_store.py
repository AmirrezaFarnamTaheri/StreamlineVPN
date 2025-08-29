from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio


import os


def _base_output_dir() -> Path:
    p = os.environ.get("OUTPUT_DIR")
    return Path(p) if p else Path("output")


EVENT_LOG = _base_output_dir() / "events.log"


_listeners: List[asyncio.Queue] = []
_last_event_id: Dict[str, float] = {}


def register_listener(maxsize: int = 1000) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
    _listeners.append(q)
    return q


def unregister_listener(q: asyncio.Queue) -> None:
    try:
        _listeners.remove(q)
    except ValueError:
        pass


def append_event(event: Dict[str, Any]) -> None:
    EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    # Optional sampling for high-frequency events
    try:
        import random
        rate = float(os.environ.get("EVENT_SAMPLE_RATE", "1"))
        et = str(event.get("type", ""))
        if et == "fetch_progress" and rate < 1.0:
            if random.random() > rate:
                # Still broadcast to listeners at lower frequency
                for q in list(_listeners):
                    try:
                        if not q.full():
                            q.put_nowait(event)
                    except Exception:
                        try:
                            _listeners.remove(q)
                        except Exception:
                            pass
                return
    except Exception:
        pass
    try:
        with EVENT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # broadcast non-blocking
    for q in list(_listeners):
        try:
            if not q.full():
                q.put_nowait(event)
        except Exception:
            try:
                _listeners.remove(q)
            except Exception:
                pass


def set_last_event_id(client_id: str, last_id: float) -> None:
    _last_event_id[str(client_id)] = float(last_id)


def get_last_event_id(client_id: str) -> Optional[float]:
    v = _last_event_id.get(str(client_id))
    return float(v) if v is not None else None


def tail_events(n: int = 100) -> List[Dict[str, Any]]:
    try:
        lines = EVENT_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return []
    out: List[Dict[str, Any]] = []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def events_after(after_ts: float = 0.0, limit: int = 100, type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        lines = EVENT_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return []
    out: List[Dict[str, Any]] = []
    for line in lines:
        try:
            ev = json.loads(line)
        except Exception:
            continue
        ts = float(ev.get("ts", 0.0))
        if ts <= float(after_ts):
            continue
        if type_filter and str(ev.get("type", "")) != type_filter:
            continue
        out.append(ev)
        if len(out) >= int(limit):
            break
    return out
