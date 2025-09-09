#!/usr/bin/env python3
"""
cli.py
======

Command-line interface for StreamlineVPN with all features.
"""

import click
import asyncio
import json
import yaml
from pathlib import Path
from typing import List, Optional

from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.utils.logging import get_logger
from streamline_vpn.web.unified_api import JobManager

logger = get_logger(__name__)


@click.group()
@click.option('--debug/--no-debug', default=False, help='Enable debug mode')
@click.pass_context
def cli(ctx, debug):
    """StreamlineVPN Command Line Interface."""
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug
    
    if debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--output', '-o', type=click.Path(), default='output', help='Output directory')
@click.option('--formats', '-f', multiple=True, default=['json', 'clash'], help='Output formats')
@click.option('--async/--sync', default=True, help='Run asynchronously')
@click.pass_context
def process(ctx, config, output, formats, async_run):
    """Process VPN configurations."""
    click.echo(f"Processing configurations...")
    
    async def run():
        merger = StreamlineVPNMerger(config_path=config)
        await merger.initialize()
        
        result = await merger.process_all(
            output_dir=output,
            formats=list(formats)
        )
        
        if result.get('success'):
            click.echo(f"✅ Successfully processed {result.get('sources_processed', 0)} sources")
            click.echo(f"   Found {result.get('configurations_found', 0)} configurations")
        else:
            click.echo(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
    
    if async_run:
        asyncio.run(run())
    else:
        # Sync version would go here
        click.echo("Synchronous processing not implemented")


@cli.command()
@click.option('--host', '-h', default='0.0.0.0', help='API host')
@click.option('--port', '-p', default=8080, help='API port')
@click.option('--workers', '-w', default=4, help='Number of workers')
def serve(host, port, workers):
    """Start the API server."""
    click.echo(f"Starting API server on {host}:{port}")
    
    import uvicorn
    from streamline_vpn.web.unified_api import create_unified_app
    
    app = create_unified_app()
    uvicorn.run(app, host=host, port=port, workers=workers)


@cli.command()
@click.option('--port', '-p', default=8000, help='Web interface port')
def web(port):
    """Start the web interface."""
    click.echo(f"Starting web interface on port {port}")
    
    import subprocess
    import sys
    
    subprocess.run([sys.executable, "run_web.py"], env={"WEB_PORT": str(port)})


@cli.command()
def status():
    """Check system status."""
    import requests
    
    click.echo("Checking system status...")
    
    # Check API
    try:
        response = requests.get("http://localhost:8080/health")
        if response.status_code == 200:
            data = response.json()
            click.echo(f"✅ API: {data['status']}")
        else:
            click.echo(f"❌ API: Not responding")
    except:
        click.echo(f"❌ API: Not running")
    
    # Check Redis
    try:
        import redis
        r = redis.Redis()
        r.ping()
        click.echo(f"✅ Redis: Connected")
    except:
        click.echo(f"❌ Redis: Not connected")
    
    # Check statistics
    try:
        response = requests.get("http://localhost:8080/api/v1/statistics")
        if response.status_code == 200:
            stats = response.json()
            click.echo(f"\n📊 Statistics:")
            click.echo(f"   Sources: {stats.get('total_sources', 0)}")
            click.echo(f"   Configs: {stats.get('total_configs', 0)}")
            click.echo(f"   Success Rate: {stats.get('success_rate', 0)*100:.1f}%")
    except:
        pass


@cli.command()
@click.argument('url')
def add_source(url):
    """Add a new source URL."""
    import requests
    
    click.echo(f"Adding source: {url}")
    
    try:
        response = requests.post(
            "http://localhost:8080/api/v1/sources",
            json={"url": url}
        )
        
        if response.status_code == 200:
            click.echo(f"✅ Source added successfully")
        else:
            click.echo(f"❌ Failed to add source: {response.text}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.command()
def validate():
    """Validate configuration."""
    click.echo("Validating configuration...")
    
    config_path = Path("config/sources.yaml")
    
    if not config_path.exists():
        click.echo(f"❌ Configuration file not found: {config_path}")
        return
    
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Check structure
        if 'sources' not in config:
            click.echo(f"❌ Missing 'sources' section")
            return
        
        # Count sources
        total = 0
        for tier, urls in config['sources'].items():
            if isinstance(urls, list):
                total += len(urls)
                click.echo(f"   {tier}: {len(urls)} sources")
        
        click.echo(f"✅ Configuration valid ({total} total sources)")
        
    except Exception as e:
        click.echo(f"❌ Invalid configuration: {e}")


@cli.command()
@click.option('--days', '-d', default=7, help='Days to keep')
def cleanup(days):
    """Clean up old files."""
    click.echo(f"Cleaning up files older than {days} days...")
    
    import time
    from datetime import datetime, timedelta
    
    cutoff = datetime.now() - timedelta(days=days)
    
    # Clean output directory
    output_dir = Path("output")
    if output_dir.exists():
        count = 0
        for file in output_dir.glob("*"):
            if file.is_file():
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if mtime < cutoff:
                    file.unlink()
                    count += 1
        
        click.echo(f"   Removed {count} output files")
    
    # Clean logs
    log_dir = Path("logs")
    if log_dir.exists():
        count = 0
        for file in log_dir.glob("*.log*"):
            if file.is_file():
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if mtime < cutoff:
                    file.unlink()
                    count += 1
        
        click.echo(f"   Removed {count} log files")
    
    click.echo(f"✅ Cleanup completed")


if __name__ == '__main__':
    cli()
