"""
Main CLI entry point and base functionality.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import click
from click import Context

from . import context as cli_context
from .commands import process, validate, server, sources, health, version


def _help_callback(ctx: Context, param: click.Option, value: bool) -> None:
    if not value:
        return
    # Trigger context initialization so help still surfaces initialization errors
    _ = cli_context.CLIContext()
    click.echo(ctx.get_help())
    ctx.exit()


@click.group()
@click.version_option(version="1.0.0", prog_name="StreamlineVPN")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option(
    "--config", "-c", type=click.Path(exists=True), help="Configuration file path"
)
@click.option("--output", "-o", type=click.Path(), help="Output directory path")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without making changes"
)
@click.option(
    "--help",
    is_flag=True,
    help="Show this message and exit",
    is_eager=True,
    expose_value=False,
    callback=_help_callback,
)
@click.pass_context
def main(
    ctx: Context,
    verbose: bool,
    config: Optional[Path],
    output: Optional[Path],
    dry_run: bool,
):
    """
    StreamlineVPN - Advanced VPN Configuration Manager

    A comprehensive tool for managing, merging, and optimizing VPN configurations
    from multiple sources with advanced filtering, deduplication, and validation.
    """
    try:
        # Ensure context object exists
        if ctx.obj is None:
            ctx.obj = cli_context.CLIContext()

        # Set context properties
        ctx.obj.verbose = verbose
        ctx.obj.config_path = config
        ctx.obj.output_path = output
        ctx.obj.dry_run = dry_run

        # Ensure output directory exists if provided
        try:
            if output is not None:
                Path(output).mkdir(parents=True, exist_ok=True)
        except Exception:
            # Defer failure to commands that actually need output
            pass

        # Setup logging
        ctx.obj.setup_logging(verbose)

        if dry_run:
            click.echo("🔍 DRY RUN MODE - No changes will be made")
    except Exception as e:
        # Convert unexpected initialization errors into non-zero exit
        raise click.ClickException(str(e))


# Add all command groups
main.add_command(process)
main.add_command(validate.validate_group)
main.add_command(server.server_group)
main.add_command(sources.sources_group)
main.add_command(health)
main.add_command(version)


if __name__ == "__main__":
    main()
