"""
Sources command group for managing VPN sources.
"""

from typing import Optional

import click
from click import Context

from ..context import CLIContext


@click.group()
def sources_group():
    """Manage VPN configuration sources."""
    pass


@sources_group.command()
def sources():
    """Show information about configured sources."""
    click.echo("📋 VPN Configuration Sources")
    click.echo("=" * 40)
    
    try:
        from ...core.source.manager import SourceManager
        
        source_manager = SourceManager()
        sources = source_manager.get_all_sources()
        
        if not sources:
            click.echo("No sources configured.")
            click.echo("Use 'streamline-vpn sources add' to add sources.")
            return
        
        for i, source in enumerate(sources, 1):
            click.echo(f"{i}. {source.get('name', 'Unnamed')}")
            click.echo(f"   URL: {source.get('url', 'N/A')}")
            click.echo(f"   Type: {source.get('type', 'N/A')}")
            click.echo(f"   Status: {source.get('status', 'Unknown')}")
            click.echo()
    
    except Exception as e:
        click.echo(f"❌ Error retrieving sources: {e}")


@sources_group.command()
@click.option('--tier', help='Filter by tier (free, premium, etc.)')
@click.option('--status', help='Filter by status (active, inactive, etc.)')
@click.option('--output-format', default='table', help='Output format (table, json, csv)')
@click.pass_context
def list(ctx: Context, tier: Optional[str], status: Optional[str], output_format: str):
    """List all configured sources with optional filtering."""
    cli_context: CLIContext = ctx.obj
    
    click.echo("📋 Listing VPN Sources")
    click.echo("=" * 30)
    
    try:
        from ...core.source.manager import SourceManager
        
        source_manager = SourceManager()
        sources = source_manager.get_all_sources()
        
        # Apply filters
        if tier:
            sources = [s for s in sources if s.get('tier') == tier]
        if status:
            sources = [s for s in sources if s.get('status') == status]
        
        if not sources:
            click.echo("No sources found matching criteria.")
            return
        
        # Output in requested format
        if output_format == 'json':
            import json
            click.echo(json.dumps(sources, indent=2))
        elif output_format == 'csv':
            import csv
            import io
            output = io.StringIO()
            if sources:
                writer = csv.DictWriter(output, fieldnames=sources[0].keys())
                writer.writeheader()
                writer.writerows(sources)
            click.echo(output.getvalue())
        else:  # table format
            for i, source in enumerate(sources, 1):
                click.echo(f"{i:2d}. {source.get('name', 'Unnamed')}")
                click.echo(f"    URL: {source.get('url', 'N/A')}")
                click.echo(f"    Type: {source.get('type', 'N/A')}")
                click.echo(f"    Tier: {source.get('tier', 'N/A')}")
                click.echo(f"    Status: {source.get('status', 'Unknown')}")
                click.echo()
    
    except Exception as e:
        click.echo(f"❌ Error listing sources: {e}")


@sources_group.command()
@click.option('--url', required=True, help='Source URL')
@click.option('--tier', default='free', help='Source tier (free, premium, etc.)')
@click.option('--name', help='Custom name for the source')
@click.pass_context
def add(ctx: Context, url: str, tier: str, name: Optional[str]):
    """Add a new VPN configuration source."""
    cli_context: CLIContext = ctx.obj
    
    if not name:
        # Generate name from URL
        from urllib.parse import urlparse
        parsed = urlparse(url)
        name = parsed.netloc or parsed.path.split('/')[-1] or 'Unknown Source'
    
    click.echo(f"➕ Adding source: {name}")
    click.echo(f"   URL: {url}")
    click.echo(f"   Tier: {tier}")
    
    try:
        from ...core.source.manager import SourceManager
        
        source_manager = SourceManager()
        
        # Create source configuration
        source_config = {
            'name': name,
            'url': url,
            'type': 'http',
            'tier': tier,
            'enabled': True,
            'priority': 1,
            'refresh_interval': 3600,
            'timeout': 30,
            'retry_attempts': 3
        }
        
        # Add source
        success = source_manager.add_source(source_config)
        
        if success:
            click.echo("✅ Source added successfully!")
        else:
            click.echo("❌ Failed to add source")
            ctx.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Error adding source: {e}")
        ctx.exit(1)
