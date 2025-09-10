#!/usr/bin/env python3
"""
cli.py
======

Command-line interface for StreamlineVPN utilities.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List

import click
import httpx

# Ensure local src is importable without installation
ROOT = Path(__file__).parent.resolve()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
@click.option("--debug/--no-debug", default=False, help="Enable debug logs")
def cli(debug: bool) -> None:
    if debug:
        import logging

        logging.basicConfig(level=logging.DEBUG)


@cli.command()
@click.option("--config", "config_path", type=click.Path(exists=True), help="Configuration file path")
@click.option("--output", type=click.Path(), default="output", help="Output directory")
@click.option("--format", "formats", multiple=True, default=["json", "clash"], help="Output formats")
def process(config_path: str | None, output: str, formats: List[str]):
    """Process VPN configurations via merger."""

    async def run() -> None:
        merger = StreamlineVPNMerger(config_path=config_path) if config_path else StreamlineVPNMerger()
        await merger.initialize()
        result = await merger.process_all(output_dir=output, formats=list(formats))  # type: ignore[arg-type]
        if result.get("success"):
            click.echo(json.dumps({k: v for k, v in result.items() if k != "details"}, indent=2))
        else:
            click.echo(f"Processing failed: {result.get('error', 'unknown error')}")

    asyncio.run(run())


@cli.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8080, type=int)
@click.option("--workers", default=1, type=int)
def serve(host: str, port: int, workers: int) -> None:
    """Start the unified API server."""
    import uvicorn
    from streamline_vpn.web.unified_api import create_unified_app

    app = create_unified_app()
    uvicorn.run(app, host=host, port=port, workers=workers)


@cli.command()
def status() -> None:
    """Check API status and basic statistics."""
    base = "http://localhost:8080"
    try:
        with httpx.Client(timeout=5.0) as client:
            h = client.get(f"{base}/health").json()
            click.echo(f"API: {h.get('status', 'unknown')} - v{h.get('version')}")
            try:
                s = client.get(f"{base}/api/v1/statistics").json()
                click.echo(f"Sources: {s.get('total_sources', 0)} | Configs: {s.get('total_configs', 0)} | Success: {int((s.get('success_rate', 0.0))*100)}%")
            except Exception:
                pass
    except Exception as exc:
        click.echo(f"API not available: {exc}")


if __name__ == "__main__":
    cli()
