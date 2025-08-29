from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import os


def _base_output_dir() -> Path:
    p = os.environ.get("OUTPUT_DIR")
    return Path(p) if p else Path("output")


RUN_LOG = _base_output_dir() / "runs.log"


def append_run(entry: Dict[str, Any], max_lines: int = 1000) -> None:
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    try:
        with RUN_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        # Trim if too large (simple heuristic)
        lines = RUN_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
        if len(lines) > max_lines * 2:
            tail = lines[-max_lines:]
            RUN_LOG.write_text("\n".join(tail), encoding="utf-8")
    except Exception:
        pass


def tail_runs(n: int = 50) -> List[Dict[str, Any]]:
    try:
        lines = RUN_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return []
    out: List[Dict[str, Any]] = []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def runs_after(after_ts: float = 0.0, limit: int = 50) -> List[Dict[str, Any]]:
    try:
        lines = RUN_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
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
        out.append(ev)
        if len(out) >= int(limit):
            break
    return out
