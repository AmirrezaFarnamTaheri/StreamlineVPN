"""
Version command group for version information.
"""

import click
from click import Context

from ..context import CLIContext


@click.group(name='version')
def version_group():
    """Version and system information."""
    pass


@version_group.command()
def version():
    """Show version information."""
    try:
        # Try to get version from package
        try:
            import pkg_resources
            version = pkg_resources.get_distribution("streamline-vpn").version
        except:
            # Fallback to hardcoded version
            version = "1.0.0"
        
        click.echo("StreamlineVPN - Advanced VPN Configuration Manager")
        click.echo("=" * 55)
        click.echo(f"Version: {version}")
        click.echo("Author: StreamlineVPN Team")
        click.echo("License: MIT")
        click.echo("Repository: https://github.com/streamlinevpn/streamline-vpn")
        click.echo()
        
        # Show Python version
        import sys
        click.echo(f"Python Version: {sys.version}")
        click.echo(f"Python Executable: {sys.executable}")
        click.echo()
        
        # Show installed packages
        click.echo("Key Dependencies:")
        try:
            import pkg_resources
            
            key_packages = [
                'fastapi', 'uvicorn', 'aiohttp', 'pydantic', 'click',
                'redis', 'sqlalchemy', 'structlog', 'prometheus-client'
            ]
            
            for package in key_packages:
                try:
                    dist = pkg_resources.get_distribution(package)
                    click.echo(f"  {package}: {dist.version}")
                except:
                    click.echo(f"  {package}: Not installed")
        except:
            click.echo("  Unable to determine package versions")
        
    except Exception as e:
        click.echo(f"❌ Error getting version information: {e}")
        raise click.Abort()

