"""
Validate command group for configuration validation.
"""

import click
from click import Context

from ..context import CLIContext


@click.group(name="validate")
def validate_group():
    """Validate configuration files and sources"""
    pass


@validate_group.command()
@click.pass_context
def validate(ctx: Context):
    """Validate project configuration and setup."""
    cli_context: CLIContext = ctx.obj
    
    click.echo("🔍 Validating project configuration...")
    
    try:
        # Import validation modules
        from ...core.config_processor import ConfigurationProcessor
        from ...core.source.manager import SourceManager
        
        # Initialize components
        config_processor = ConfigurationProcessor()
        source_manager = SourceManager()
        
        # Validate configuration files
        config_valid = config_processor.validate_configuration()
        if config_valid:
            click.echo("✅ Configuration files are valid")
        else:
            click.echo("❌ Configuration files have issues")
            ctx.exit(1)
        
        # Validate sources
        sources = source_manager.get_all_sources()
        if sources:
            click.echo(f"✅ Found {len(sources)} configured sources")
        else:
            click.echo("⚠️  No sources configured")
        
        # Validate project structure
        from pathlib import Path
        required_files = [
            "src/streamline_vpn/__init__.py",
            "src/streamline_vpn/core/__init__.py",
            "config/sources.yaml",
            ".env.example"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            click.echo(f"❌ Missing required files: {', '.join(missing_files)}")
            ctx.exit(1)
        else:
            click.echo("✅ All required files present")
        
        click.echo("✅ Project validation completed successfully!")
        
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")
        ctx.exit(1)
