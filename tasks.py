#!/usr/bin/env python3
"""
Lightweight task runner for StreamlineVPN.

Usage:
  python tasks.py --help
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List

import click

ROOT = Path(__file__).parent.resolve()
SRC = ROOT / "src"


def _run(cmd: List[str], env: dict | None = None) -> int:
    e = os.environ.copy()
    e.setdefault("PYTHONUNBUFFERED", "1")
    e.setdefault("PYTHONPATH", f"{ROOT};{SRC}")
    if env:
        e.update(env)
    print("$", " ".join(cmd))
    return subprocess.call(cmd, env=e)


@click.group()
def cli() -> None:  # pragma: no cover - thin wrapper
    pass


@cli.command()
def init() -> None:
    """Seed dev environment (dirs, config, .env)."""
    code = _run([sys.executable, "scripts/seed_dev.py"])  # type: ignore[list-item]
    if code != 0:
        sys.exit(code)


@cli.command()
@click.option("--k", "kexpr", help="Pytest -k expression filter", default=None)
def test(kexpr: str | None) -> None:
    """Run test suite."""
    cmd = [sys.executable, "-m", "pytest", "-q"]
    if kexpr:
        cmd.extend(["-k", kexpr])
    sys.exit(_run(cmd))


@cli.command()
def coverage() -> None:
    """Run tests with coverage summary."""
    sys.exit(
        _run([sys.executable, "-m", "pytest", "-q", "--cov=streamline_vpn", "--cov-report=term-missing"])  # type: ignore[list-item]
    )


@cli.command()
def serve() -> None:
    """Start the unified API server (dev)."""
    sys.exit(_run([sys.executable, "run_unified.py"]))


@cli.command()
def web() -> None:
    """Start the web interface (dev)."""
    sys.exit(_run([sys.executable, "run_web.py"]))


@cli.command()
def dev_up() -> None:
    """Compose up with dev overrides and hot reload."""
    sys.exit(_run(["docker-compose", "-f", "docker-compose.yml", "-f", "docker-compose.dev.yml", "up", "-d"]))


@cli.command()
def dev_down() -> None:
    """Compose down all services."""
    sys.exit(_run(["docker-compose", "down"]))


@cli.command()
def fmt() -> None:
    """Run ruff format (if installed)."""
    code = _run(["ruff", "format", "src", "tests"])  # type: ignore[list-item]
    if code != 0:
        print("ruff not installed or format failed; skipping")


@cli.command()
def lint() -> None:
    """Run ruff check (if installed)."""
    code = _run(["ruff", "check", "src", "tests"])  # type: ignore[list-item]
    if code != 0:
        print("ruff not installed or lint issues found")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    try:
        cli()
    except KeyboardInterrupt:
        print("\nAborted.")

