#!/usr/bin/env python3
"""
StreamlineVPN Command Line Interface
====================================

Comprehensive CLI for managing StreamlineVPN operations.
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import click
import yaml
from datetime import datetime

# Add src to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.insert(0, str(src_dir))

from streamline_vpn import __version__
from streamline_vpn.utils.logging import setup_logging, get_logger

# Initialize logger
logger = get_logger(__name__)

# Click configuration
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


class StreamlineVPNCLI:
    """Main CLI class for StreamlineVPN operations."""
    
    def __init__(self):
        self.config_path: Optional[Path] = None
        self.output_dir: Optional[Path] = None
        self.verbose = False
        self.dry_run = False
    
    def setup_logging(self, verbose: bool = False):
        """Setup logging configuration."""
        level = "DEBUG" if verbose else "INFO"
        setup_logging(level=level)
    
    async def process_configurations(
        self,
        config_path: Path,
        output_dir: Path,
        formats: List[str],
        max_concurrent: int = 50,
        timeout: int = 60,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Process VPN configurations."""
        try:
            from streamline_vpn.core.merger import StreamlineVPNMerger
            
            # Initialize merger
            merger = StreamlineVPNMerger(
                config_path=str(config_path),
                output_dir=str(output_dir),
                max_concurrent=max_concurrent,
                timeout=timeout
            )
            
            await merger.initialize()
            
            # Process all sources
            result = await merger.process_all(
                output_formats=formats,
                force_refresh=force_refresh
            )
            
            await merger.shutdown()
            return result

        except ImportError as e:
            logger.error(f"Failed to import required modules: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return {"success": False, "error": str(e)}


# CLI instance
cli_instance = StreamlineVPNCLI()


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__, prog_name="StreamlineVPN")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--config", "-c", type=click.Path(exists=True, path_type=Path), 
              default="config/sources.yaml", help="Configuration file path")
@click.option("--output", "-o", type=click.Path(path_type=Path),
              default="output", help="Output directory")
@click.option("--dry-run", is_flag=True, help="Show what would be done without executing")
@click.pass_context
def main(ctx, verbose: bool, config: Path, output: Path, dry_run: bool):
    """
    StreamlineVPN - Advanced VPN Configuration Aggregator
    
    \b
    Examples:
        streamline-vpn process --formats json,clash
        streamline-vpn validate --config config/sources.yaml
        streamline-vpn server --port 8080
        streamline-vpn sources list --tier premium
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Store global options
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config
    ctx.obj['output'] = output
    ctx.obj['dry_run'] = dry_run
    
    # Setup CLI instance
    cli_instance.verbose = verbose
    cli_instance.config_path = config
    cli_instance.output_dir = output
    cli_instance.dry_run = dry_run
    cli_instance.setup_logging(verbose)
    
    if verbose:
        click.echo(f"🔧 StreamlineVPN CLI v{__version__}")
        click.echo(f"📁 Config: {config}")
        click.echo(f"📂 Output: {output}")
        if dry_run:
            click.echo("🔍 Dry run mode enabled")


@main.command()
@click.option("--formats", "-f", default="json,clash", 
              help="Output formats (comma-separated)")
@click.option("--max-concurrent", "-j", default=50, 
              help="Maximum concurrent connections")
@click.option("--timeout", "-t", default=60, 
              help="Request timeout in seconds")
@click.option("--force-refresh", is_flag=True, 
              help="Force refresh ignoring cache")
@click.pass_context
def process(ctx, formats: str, max_concurrent: int, timeout: int, force_refresh: bool):
    """Process VPN configurations from all sources."""
    config_path = ctx.obj['config']
    output_dir = ctx.obj['output']
    dry_run = ctx.obj['dry_run']
    
    # Parse formats
    format_list = [f.strip() for f in formats.split(",")]
    
    click.echo("🚀 Starting VPN configuration processing...")
    click.echo(f"📋 Formats: {', '.join(format_list)}")
    click.echo(f"⚡ Max concurrent: {max_concurrent}")
    click.echo(f"⏱️  Timeout: {timeout}s")
    
    if dry_run:
        click.echo("🔍 Dry run - would process configurations")
        return
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run processing
    try:
        result = asyncio.run(cli_instance.process_configurations(
            config_path=config_path,
            output_dir=output_dir,
            formats=format_list,
            max_concurrent=max_concurrent,
            timeout=timeout,
            force_refresh=force_refresh
        ))
        
        if result.get("success"):
            click.echo("✅ Processing completed successfully!")
            stats = result.get("statistics", {})
            click.echo(f"📊 Sources processed: {stats.get('sources_processed', 'N/A')}")
            click.echo(f"📊 Configurations found: {stats.get('total_configurations', 'N/A')}")
            click.echo(f"📊 Processing time: {stats.get('processing_time', 'N/A')}s")
        else:
            click.echo(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        click.echo("\n⚠️ Processing interrupted by user")
        sys.exit(130)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.pass_context
def validate(ctx):
    """Validate configuration files and sources."""
    config_path = ctx.obj['config']
    
    click.echo("🔍 Validating configuration...")
    
    if not config_path.exists():
        click.echo(f"❌ Configuration file not found: {config_path}")
        sys.exit(1)
    
    try:
        # Validate YAML syntax
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        click.echo("✅ Configuration file syntax is valid")
        
        # Basic structure validation
        required_keys = ['sources', 'global_settings']
        missing_keys = [key for key in required_keys if key not in config_data]
        
        if missing_keys:
            click.echo(f"⚠️  Missing required keys: {', '.join(missing_keys)}")
        
        # Count sources
        total_sources = 0
        for tier_name, tier_data in config_data.get('sources', {}).items():
            if isinstance(tier_data, dict) and 'sources' in tier_data:
                tier_sources = len(tier_data['sources'])
                total_sources += tier_sources
                click.echo(f"📊 {tier_name}: {tier_sources} sources")
        
        click.echo(f"📊 Total sources configured: {total_sources}")
        
        if total_sources == 0:
            click.echo("⚠️  No sources configured")
        
        click.echo("✅ Configuration validation completed")
        
    except yaml.YAMLError as e:
        click.echo(f"❌ YAML syntax error: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Validation error: {e}")
        sys.exit(1)


@main.group()
def server():
    """Server management commands."""
    pass


@server.command()
@click.option("--host", default="0.0.0.0", help="Server host")
@click.option("--port", default=8080, help="Server port")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
@click.pass_context
def api(ctx, host: str, port: int, reload: bool):
    """Start the API server."""
    click.echo(f"🚀 Starting StreamlineVPN API server...")
    click.echo(f"🌐 Host: {host}")
    click.echo(f"🔌 Port: {port}")
    
    if ctx.obj['dry_run']:
        click.echo("🔍 Dry run - would start API server")
        return
    
    try:
        import uvicorn
        from streamline_vpn.web.unified_api import create_unified_app
        
        app = create_unified_app()
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            access_log=True,
            log_level="info" if not ctx.obj['verbose'] else "debug"
        )
        
    except ImportError as e:
        click.echo(f"❌ Failed to import required modules: {e}")
        click.echo("💡 Install with: pip install 'streamline-vpn[prod]'")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Server startup failed: {e}")
        sys.exit(1)


@server.command()
@click.option("--host", default="0.0.0.0", help="Server host")
@click.option("--port", default=8000, help="Server port")
@click.option("--api-url", default="http://localhost:8080", help="API server URL")
@click.pass_context
def web(ctx, host: str, port: int, api_url: str):
    """Start the web interface server."""
    click.echo(f"🌐 Starting StreamlineVPN web interface...")
    click.echo(f"🌐 Host: {host}")
    click.echo(f"🔌 Port: {port}")
    click.echo(f"🔗 API URL: {api_url}")
    
    if ctx.obj['dry_run']:
        click.echo("🔍 Dry run - would start web server")
        return
    
    # Set environment variables
    os.environ['WEB_HOST'] = host
    os.environ['WEB_PORT'] = str(port)
    os.environ['API_BASE_URL'] = api_url
    
    try:
        # Import and run the web server
        from streamline_vpn.web.server import main as web_main
        web_main()
        
    except ImportError as e:
        click.echo(f"❌ Failed to import web server: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Web server startup failed: {e}")
        sys.exit(1)


@main.group()
def sources():
    """Source management commands."""
    pass


@sources.command()
@click.option("--tier", help="Filter by tier (premium, standard, backup)")
@click.option("--status", help="Filter by status (active, inactive)")
@click.option("--format", "output_format", default="table", 
              type=click.Choice(['table', 'json', 'yaml']),
              help="Output format")
@click.pass_context
def list(ctx, tier: Optional[str], status: Optional[str], output_format: str):
    """List configured sources."""
    config_path = ctx.obj['config']
    
    if not config_path.exists():
        click.echo(f"❌ Configuration file not found: {config_path}")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        sources_data = []
        
        for tier_name, tier_data in config_data.get('sources', {}).items():
            if tier and tier not in tier_name.lower():
                continue
                
            if isinstance(tier_data, dict) and 'sources' in tier_data:
                for source in tier_data['sources']:
                    source_info = {
                        'tier': tier_name,
                        'name': source.get('name', 'Unknown'),
                        'url': source.get('url', ''),
                        'protocols': ', '.join(source.get('protocols', [])),
                        'reliability': source.get('reliability', 'N/A'),
                        'update_frequency': source.get('update_frequency', 'N/A')
                    }
                    sources_data.append(source_info)
        
        if not sources_data:
            click.echo("No sources found matching criteria")
        return

        if output_format == 'json':
            click.echo(json.dumps(sources_data, indent=2))
        elif output_format == 'yaml':
            click.echo(yaml.dump(sources_data, default_flow_style=False))
        else:
            # Table format
            click.echo(f"{'Tier':<20} {'Name':<30} {'Protocols':<20} {'Reliability':<12}")
            click.echo("-" * 85)
            for source in sources_data:
                click.echo(f"{source['tier']:<20} {source['name']:<30} "
                          f"{source['protocols']:<20} {source['reliability']:<12}")
        
        click.echo(f"\n📊 Total sources: {len(sources_data)}")
        
    except Exception as e:
        click.echo(f"❌ Failed to list sources: {e}")
        sys.exit(1)


@sources.command()
@click.argument('url')
@click.option("--tier", default="standard", help="Source tier")
@click.option("--name", help="Source name")
@click.pass_context
def add(ctx, url: str, tier: str, name: Optional[str]):
    """Add a new source to configuration."""
    config_path = ctx.obj['config']
    
    if not config_path.exists():
        click.echo(f"❌ Configuration file not found: {config_path}")
        sys.exit(1)
    
    if ctx.obj['dry_run']:
        click.echo(f"🔍 Dry run - would add source: {url}")
        return
    
    try:
        # Load current configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Find appropriate tier
        tier_key = f"tier_{tier}" if not tier.startswith('tier_') else tier
        
        if tier_key not in config_data.get('sources', {}):
            click.echo(f"❌ Tier '{tier}' not found in configuration")
            sys.exit(1)
        
        # Create new source entry
        new_source = {
            'url': url,
            'name': name or f"Custom Source {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'protocols': ['vmess', 'vless', 'trojan', 'shadowsocks'],
            'update_frequency': 'daily',
            'reliability': 0.75
        }
        
        # Add to configuration
        if 'sources' not in config_data['sources'][tier_key]:
            config_data['sources'][tier_key]['sources'] = []
        
        config_data['sources'][tier_key]['sources'].append(new_source)
        
        # Save configuration
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
        
        click.echo(f"✅ Source added successfully to tier '{tier}'")
        click.echo(f"📋 Name: {new_source['name']}")
        click.echo(f"🔗 URL: {url}")
        
    except Exception as e:
        click.echo(f"❌ Failed to add source: {e}")
        sys.exit(1)


@main.command()
@click.option("--check-api", is_flag=True, help="Check API server health")
@click.option("--check-sources", is_flag=True, help="Check source accessibility") 
@click.option("--check-cache", is_flag=True, help="Check cache status")
@click.pass_context
def health(ctx, check_api: bool, check_sources: bool, check_cache: bool):
    """Check system health and status."""
    click.echo("🏥 StreamlineVPN Health Check")
    click.echo("=" * 40)
    
    all_checks = not any([check_api, check_sources, check_cache])
    
    if all_checks or check_api:
        click.echo("🔍 Checking API server...")
        try:
            import requests
            response = requests.get("http://localhost:8080/health", timeout=10)
            if response.status_code == 200:
                click.echo("✅ API server is healthy")
                health_data = response.json()
                click.echo(f"📊 Version: {health_data.get('version', 'Unknown')}")
                click.echo(f"📊 Uptime: {health_data.get('uptime', 'Unknown')}s")
            else:
                click.echo(f"⚠️ API server returned status {response.status_code}")
        except requests.exceptions.ConnectionError:
            click.echo("❌ API server is not running")
        except Exception as e:
            click.echo(f"❌ API health check failed: {e}")
    
    if all_checks or check_sources:
        click.echo("\n🔍 Checking source accessibility...")
        config_path = ctx.obj['config']
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                total_sources = 0
                accessible_sources = 0
                
                for tier_name, tier_data in config_data.get('sources', {}).items():
                    if isinstance(tier_data, dict) and 'sources' in tier_data:
                        for source in tier_data['sources']:
                            total_sources += 1
                            url = source.get('url', '')
                            try:
                                import requests
                                response = requests.head(url, timeout=10)
                                if response.status_code < 400:
                                    accessible_sources += 1
                                else:
                                    click.echo(f"⚠️ {source.get('name', 'Unknown')}: HTTP {response.status_code}")
                            except Exception:
                                click.echo(f"❌ {source.get('name', 'Unknown')}: Not accessible")
                
                click.echo(f"📊 Sources accessible: {accessible_sources}/{total_sources}")
                
            except Exception as e:
                click.echo(f"❌ Source check failed: {e}")
        else:
            click.echo("❌ Configuration file not found")
    
    if all_checks or check_cache:
        click.echo("\n🔍 Checking cache status...")
        try:
            import requests
            response = requests.get("http://localhost:8080/api/v1/cache/health", timeout=10)
            if response.status_code == 200:
                cache_data = response.json()
                click.echo("✅ Cache is healthy")
                cache_info = cache_data.get('cache', {})
                for cache_type, status in cache_info.items():
                    if isinstance(status, dict):
                        cache_status = status.get('status', 'unknown')
                        click.echo(f"📊 {cache_type}: {cache_status}")
            else:
                click.echo("⚠️ Cache health check returned error")
        except Exception as e:
            click.echo(f"❌ Cache check failed: {e}")
    
    click.echo("\n✅ Health check completed")


@main.command()
def version():
    """Show version information."""
    click.echo(f"StreamlineVPN CLI v{__version__}")
    click.echo("Advanced VPN Configuration Aggregator")
    click.echo("https://github.com/streamlinevpn/streamlinevpn")


if __name__ == "__main__":
    main()