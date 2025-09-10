#!/usr/bin/env python3
"""
Seed development environment with defaults (idempotent).

Creates directories, ensures a default config exists, and copies .env.example
to .env if missing.
"""

from __future__ import annotations

import shutil
from pathlib import Path


def ensure_dirs() -> None:
    for d in ("config", "output", "data", "logs"):
        p = Path(d)
        p.mkdir(parents=True, exist_ok=True)
        print(f" ensured {p}")


def ensure_env() -> None:
    src = Path(".env.example")
    dst = Path(".env")
    if not dst.exists() and src.exists():
        shutil.copyfile(src, dst)
        print(" created .env from .env.example")
    else:
        print(" .env present (or missing template), skipping")


def ensure_config() -> None:
    cfg = Path("config/sources.yaml")
    if cfg.exists():
        print(" config/sources.yaml exists, skipping")
        return
    default = {
        "sources": {
            "free": [
                "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
                "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
            ]
        },
        "processing": {"max_concurrent": 50, "timeout": 30, "retry_count": 3},
        "output": {"formats": ["json", "clash", "singbox", "base64", "raw"]},
    }
    import yaml

    cfg.parent.mkdir(parents=True, exist_ok=True)
    with cfg.open("w", encoding="utf-8") as f:
        yaml.safe_dump(default, f)
    print(f" created {cfg}")

    unified = Path("config/sources.unified.yaml")
    if not unified.exists():
        shutil.copyfile(cfg, unified)
        print(f" created {unified}")


def main() -> None:
    ensure_dirs()
    ensure_env()
    ensure_config()
    print("\nSeed complete. You can now run:\n  python tasks.py serve\n  python tasks.py web\n  or\n  docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d\n")


if __name__ == "__main__":
    main()

