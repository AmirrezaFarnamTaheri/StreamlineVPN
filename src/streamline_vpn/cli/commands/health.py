"""
Health command group for system health checks.
"""

import asyncio
from typing import Optional

import click
from click import Context

from ..context import CLIContext


@click.group()
def health_group():
    """System health and diagnostics."""
    pass


@health_group.command()
@click.option('--check-api', is_flag=True, help='Check API server health')
@click.option('--check-sources', is_flag=True, help='Check source connectivity')
@click.option('--check-cache', is_flag=True, help='Check cache status')
@click.pass_context
def health(ctx: Context, check_api: bool, check_sources: bool, check_cache: bool):
    """Check system health and diagnostics."""
    cli_context: CLIContext = ctx.obj
    
    click.echo("🏥 StreamlineVPN Health Check")
    click.echo("=" * 35)
    
    all_checks_passed = True
    
    # Check API server
    if check_api:
        click.echo("🔍 Checking API server...")
        try:
            import httpx
            with httpx.Client() as client:
                response = client.get("http://localhost:8000/health", timeout=5.0)
                if response.status_code == 200:
                    click.echo("✅ API server is healthy")
                else:
                    click.echo(f"❌ API server returned status {response.status_code}")
                    all_checks_passed = False
        except Exception as e:
            click.echo(f"❌ API server check failed: {e}")
            all_checks_passed = False
    
    # Check sources
    if check_sources:
        click.echo("🔍 Checking source connectivity...")
        try:
            from ...core.source.manager import SourceManager
            
            source_manager = SourceManager()
            sources = source_manager.get_all_sources()
            
            if not sources:
                click.echo("⚠️  No sources configured")
            else:
                healthy_sources = 0
                for source in sources:
                    try:
                        # Simple connectivity check
                        import httpx
                        with httpx.Client() as client:
                            response = client.head(source.get('url', ''), timeout=10.0)
                            if response.status_code < 400:
                                healthy_sources += 1
                    except Exception:
                        pass
                
                click.echo(f"✅ {healthy_sources}/{len(sources)} sources are reachable")
                if healthy_sources == 0:
                    all_checks_passed = False
        except Exception as e:
            click.echo(f"❌ Source check failed: {e}")
            all_checks_passed = False
    
    # Check cache
    if check_cache:
        click.echo("🔍 Checking cache status...")
        try:
            from ...caching.l1_cache import L1ApplicationCache
            
            cache = L1ApplicationCache()
            stats = cache.get_stats()
            
            click.echo(f"✅ Cache is operational")
            click.echo(f"   Hits: {stats.get('hits', 0)}")
            click.echo(f"   Misses: {stats.get('misses', 0)}")
            click.echo(f"   Size: {stats.get('size', 0)} items")
        except Exception as e:
            click.echo(f"❌ Cache check failed: {e}")
            all_checks_passed = False
    
    # Overall status
    click.echo("\n" + "=" * 35)
    if all_checks_passed:
        click.echo("✅ All health checks passed!")
    else:
        click.echo("❌ Some health checks failed!")
        ctx.exit(1)
