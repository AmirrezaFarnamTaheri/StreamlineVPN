"""Per-module coverage gate.

Parses coverage.xml and enforces minimum coverage thresholds for selected
modules so we can ratchet quality over time without requiring 100% project-wide.

Usage:
  python scripts/coverage_gate.py coverage.xml
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional


def _check_threshold(filename: str, line_rate_pct: float, thresholds: Dict[str, float]) -> Optional[str]:
    """Return failure message if file is below its threshold, else None."""
    for partial, min_pct in thresholds.items():
        if partial in filename and line_rate_pct + 1e-9 < min_pct:
            return f"{filename}: {line_rate_pct:.1f}% < required {min_pct:.1f}%"
    return None


def main(xml_path: str) -> int:
    path = Path(xml_path)
    if not path.is_file():
        print(f"ERROR: coverage XML not found: {xml_path}")
        return 2

    tree = ET.parse(path)
    root = tree.getroot()

    # filename -> threshold percent
    # paths are substring matched against the coverage "filename" attribute
    thresholds: Dict[str, float] = {
        # Parsers
        "core/processing/parsers/shadowsocks2022_parser.py": 94.0,
        # Caching layers
        "core/caching/l1_cache.py": 100.0,
        "core/caching/service.py": 88.0,
        "core/caching/l3_sqlite.py": 94.0,
        # Processing engine
        "core/merger_processor.py": 85.0,
        # Scheduler
        "scheduler.py": 95.0,
        # Validator baseline
        "core/config_validator.py": 67.0,
    }

    failures = []
    for pkg in root.findall("packages/package"):
        for cls in pkg.findall("classes/class"):
            filename = cls.get("filename", "")
            line_rate_pct = float(cls.get("line-rate", "0")) * 100.0
            msg = _check_threshold(filename, line_rate_pct, thresholds)
            if msg:
                failures.append(msg)

    if failures:
        print("Per-module coverage gate failures:")
        for f in failures:
            print(f" - {f}")
        return 1
    print("Per-module coverage gate: OK")
    return 0


if __name__ == "__main__":
    xml = sys.argv[1] if len(sys.argv) > 1 else "coverage.xml"
    raise SystemExit(main(xml))
