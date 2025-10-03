import asyncio
import click
from typing import Optional

from .core.instance import get_merger_instance

@click.group()
def cli():
    """Streamline-VPN command-line interface."""
    pass

@cli.command()
@click.option('--output-dir', default='output', help='Directory to save output files.')
@click.option('--formats', help='Comma-separated list of output formats (e.g., json,clash).')
def process(output_dir: str, formats: Optional[str]):
    """Process all sources and generate configurations."""
    async def main():
        merger = await get_merger_instance()
        format_list = formats.split(',') if formats else None
        result = await merger.process_all(output_dir=output_dir, formats=format_list)
        click.echo(f"Processing complete: {result}")
    asyncio.run(main())

@cli.command()
def list_sources():
    """List all configured sources."""
    async def main():
        merger = await get_merger_instance()
        sources = merger.source_manager.get_all_sources()
        for tier, source_list in sources.items():
            click.echo(f"Tier: {tier}")
            for source in source_list:
                click.echo(f"  - {source}")
    asyncio.run(main())

@cli.command()
def run_server():
    """Run the FastAPI web server."""
    try:
        import uvicorn
        from .app import create_unified_app
    except ImportError as e:
        click.echo(f"Error: {e}. Please install the required dependencies with 'pip install -r requirements.txt'")
        return

    app = create_unified_app()
    uvicorn.run(app, host="0.0.0.0", port=8080)

if __name__ == '__main__':
    cli()