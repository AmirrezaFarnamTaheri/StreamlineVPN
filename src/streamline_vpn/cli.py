#!/usr/bin/env python3
"""
StreamlineVPN CLI
=================

A convenient command-line interface for common StreamlineVPN tasks:
- Process sources and generate outputs
- Validate configuration files
- Start API and Web servers
- Inspect and manage source lists
- Perform basic health checks

This CLI complements the existing entrypoint in `streamline_vpn.__main__`.
It reuses project modules and avoids duplicating logic.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import yaml

# Local imports
from .utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


# Shared helper ---------------------------------------------------------------
def _ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


# Root group -----------------------------------------------------------------
@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("--verbose", "verbose", is_flag=True, help="Enable verbose logs")
def main(verbose: bool) -> None:
    """StreamlineVPN CLI utilities."""
    setup_logging(level=("DEBUG" if verbose else "INFO"))


# Process --------------------------------------------------------------------
@main.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=Path("config/sources.yaml"),
    show_default=True,
    help="Path to sources.yaml",
)
@click.option(
    "--output",
    "output_dir",
    type=click.Path(path_type=Path),
    default=Path("output"),
    show_default=True,
)
@click.option(
    "--formats",
    default="json,clash",
    help="Comma-separated output formats (e.g. json,clash,singbox,base64)",
)
@click.option("--max-concurrent", default=50, show_default=True, type=int)
@click.option("--timeout", default=60, show_default=True, type=int)
@click.option("--force-refresh", is_flag=True, help="Bypass caches where possible")
def process(
    config_path: Path,
    output_dir: Path,
    formats: str,
    max_concurrent: int,
    timeout: int,
    force_refresh: bool,
) -> None:
    """Process VPN configurations from all sources and generate outputs."""

    async def _run() -> Dict[str, Any]:
        from .core.merger import StreamlineVPNMerger

        merger = StreamlineVPNMerger(
            config_path=str(config_path),
        )
        await merger.initialize()
        try:
            result = await merger.process_all(
                output_dir=str(output_dir),
                formats=[p.strip() for p in formats.split(",") if p.strip()],
                max_concurrent=max_concurrent,
                timeout=timeout,
                force_refresh=force_refresh,
            )
        finally:
            await merger.shutdown()
        return result

    _ensure_output_dir(output_dir)
    click.echo("Starting processing...\n")
    try:
        result = asyncio.run(_run())
        click.echo(json.dumps({k: v for k, v in result.items() if k != "details"}, indent=2))
        if not result.get("success", False):
            sys.exit(1)
    except KeyboardInterrupt:
        click.echo("Interrupted by user")
        sys.exit(130)
    except Exception as exc:  # pragma: no cover
        logger.error("Processing failed: %s", exc, exc_info=True)
        sys.exit(1)


# Validate -------------------------------------------------------------------
@main.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=Path("config/sources.yaml"),
    show_default=True,
)
def validate(config_path: Path) -> None:
    """Validate the YAML configuration and print a brief summary."""
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        click.echo(f"YAML error in {config_path}: {e}")
        sys.exit(1)

    required = ["sources", "global_settings"]
    missing = [k for k in required if k not in data]
    if missing:
        click.echo(f"Missing keys: {', '.join(missing)}")

    total_sources = 0
    for tier_name, tier in (data.get("sources", {}) or {}).items():
        items = len((tier or {}).get("sources", []) or [])
        total_sources += items
        click.echo(f"- {tier_name}: {items} sources")

    click.echo(f"\nTotal sources: {total_sources}")
    click.echo("Validation complete")


# Server ---------------------------------------------------------------------
@main.group()
def server() -> None:
    """Server management commands."""


@server.command("api")
@click.option("--host", default="0.0.0.0", show_default=True)
@click.option("--port", default=8080, show_default=True, type=int)
@click.option("--workers", default=1, show_default=True, type=int)
def server_api(host: str, port: int, workers: int) -> None:
    """Start the FastAPI unified API server."""
    try:
        import uvicorn
        from .web.unified_api import create_unified_app
    except Exception as exc:  # pragma: no cover
        click.echo(f"Failed to import server modules: {exc}")
        sys.exit(1)

    app = create_unified_app()
    click.echo(f"Unified API on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, workers=workers, log_level="info")


@server.command("web")
@click.option("--host", default="0.0.0.0", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
@click.option("--api-url", default="http://localhost:8080", show_default=True)
def server_web(host: str, port: int, api_url: str) -> None:
    """Start the static control panel server with API proxying."""
    try:
        import uvicorn
        from .web.settings import Settings
        from .web.static_server import StaticControlServer
    except Exception as exc:  # pragma: no cover
        click.echo(f"Failed to import web server modules: {exc}")
        sys.exit(1)

    # Export API base for the server (middleware also injects header)
    os.environ.setdefault("API_BASE_URL", api_url)

    settings = Settings()
    server = StaticControlServer(settings=settings)
    server.app.state.api_base = api_url
    click.echo(f"Web UI on http://{host}:{port} (API {api_url})")
    uvicorn.run(server.app, host=host, port=port, log_level="info")


# Sources --------------------------------------------------------------------
@main.group()
def sources() -> None:
    """Source list utilities."""


@sources.command("list")
@click.option("--config", type=click.Path(exists=True, path_type=Path), default=Path("config/sources.yaml"))
@click.option("--tier", default=None, help="Filter by tier substring (e.g. premium)")
@click.option("--format", "fmt", type=click.Choice(["table", "json", "yaml"]), default="table")
def sources_list(config: Path, tier: Optional[str], fmt: str) -> None:
    """List configured sources with optional tier filter."""
    data = yaml.safe_load(config.read_text(encoding="utf-8"))
    rows: List[Dict[str, Any]] = []
    for tier_name, section in (data.get("sources", {}) or {}).items():
        if tier and tier.lower() not in tier_name.lower():
            continue
        for src in (section or {}).get("sources", []) or []:
            rows.append(
                {
                    "tier": tier_name,
                    "name": src.get("name", "Unknown"),
                    "url": src.get("url", ""),
                    "protocols": ", ".join(src.get("protocols", []) or []),
                    "reliability": src.get("reliability", "N/A"),
                }
            )

    if fmt == "json":
        click.echo(json.dumps(rows, indent=2))
        return
    if fmt == "yaml":
        click.echo(yaml.dump(rows, sort_keys=False, allow_unicode=True))
        return

    # table
    click.echo(f"{'Tier':<22} {'Name':<30} {'Protocols':<22} {'Reliability':<10}")
    click.echo("-" * 90)
    for r in rows:
        click.echo(f"{r['tier']:<22} {r['name']:<30} {r['protocols']:<22} {str(r['reliability']):<10}")
    click.echo(f"\nTotal: {len(rows)}")


@sources.command("add")
@click.argument("url")
@click.option("--config", type=click.Path(exists=True, path_type=Path), default=Path("config/sources.yaml"))
@click.option("--tier", default="tier_2_standard", show_default=True)
@click.option("--name", default=None)
def sources_add(url: str, config: Path, tier: str, name: Optional[str]) -> None:
    """Add a new source to the configuration file."""
    data = yaml.safe_load(config.read_text(encoding="utf-8"))
    data.setdefault("sources", {})
    if tier not in data["sources"]:
        click.echo(f"Tier '{tier}' not found in config")
        sys.exit(1)

    entry = {
        "url": url,
        "name": name or f"Custom Source",
        "protocols": ["vmess", "vless", "trojan", "shadowsocks"],
        "update_frequency": "daily",
        "reliability": 0.75,
    }
    data["sources"][tier].setdefault("sources", []).append(entry)
    config.write_text(yaml.dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    click.echo(f"Added source to {tier}: {url}")


# Health ---------------------------------------------------------------------
@main.command()
@click.option("--api-base", default="http://localhost:8080", show_default=True)
def health(api_base: str) -> None:
    """Check basic API health and statistics (best-effort)."""
    try:
        import httpx
    except Exception as exc:  # pragma: no cover
        click.echo(f"httpx not available: {exc}")
        sys.exit(1)

    with httpx.Client(timeout=5.0) as client:
        try:
            h = client.get(f"{api_base}/health").json()
            click.echo(f"API: {h.get('status', 'unknown')} - v{h.get('version', 'n/a')}")
        except Exception as exc:
            click.echo(f"Health check failed: {exc}")
            return

        try:
            s = client.get(f"{api_base}/api/v1/statistics").json()
            total = s.get("total_configurations") or s.get("total_configs") or 0
            click.echo(f"Sources: {s.get('total_sources', 0)} | Configs: {total}")
        except Exception:
            pass


@main.command()
def version() -> None:
    """Show version information."""
    try:
        from . import __version__
    except Exception:
        __version__ = "unknown"
    click.echo(f"StreamlineVPN v{__version__}")


if __name__ == "__main__":
    main()

