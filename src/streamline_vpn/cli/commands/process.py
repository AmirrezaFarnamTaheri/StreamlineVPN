"""
Process command group for configuration processing.
"""

import asyncio
from typing import Optional

import click
from click import Context

from ..context import CLIContext


@click.command(name="process")
@click.option("--formats", default="all", help="Output formats (comma-separated)")
@click.option(
    "--max-concurrent", default=5, help="Maximum concurrent source processing"
)
@click.option("--timeout", default=30, help="Timeout for each source (seconds)")
@click.option("--force-refresh", is_flag=True, help="Force refresh of cached data")
@click.pass_context
def process(
    ctx: Context, formats: str, max_concurrent: int, timeout: int, force_refresh: bool
):
    """Process VPN configurations from all sources."""
    cli_context: CLIContext = ctx.obj

    click.echo("🔄 Processing VPN configurations...")

    # Run async processing
    result = asyncio.run(
        cli_context.process_configurations(
            formats=formats,
            max_concurrent=max_concurrent,
            timeout=timeout,
            force_refresh=force_refresh,
        )
    )

    if result:
        click.echo("✅ Configuration processing completed successfully!")
    else:
        click.echo("❌ Configuration processing failed!")
        ctx.exit(1)
