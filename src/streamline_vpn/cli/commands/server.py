"""
Server command group for running servers.
"""

import asyncio
from typing import Optional

import click
from click import Context

from ..context import CLIContext


@click.group(name="server")
def server_group():
    """Run StreamlineVPN servers."""
    pass


@server_group.command(name="all")
def all_servers():
    """Run unified server (API + Web)."""
    click.echo("🚀 Starting unified StreamlineVPN server...")

    try:
        from ...api.unified_api import UnifiedAPIServer
        from ...web.static_server import StaticServer

        async def run_unified():
            # Start API server
            api_server = UnifiedAPIServer()
            api_task = asyncio.create_task(api_server.start())

            # Start web server
            web_server = StaticServer()
            web_task = asyncio.create_task(web_server.start())

            click.echo("✅ All services started successfully!")
            click.echo("🌐 API Server: http://localhost:8000")
            click.echo("🌐 Web Interface: http://localhost:8080")

            try:
                await asyncio.gather(api_task, web_task)
            except KeyboardInterrupt:
                click.echo("\n🛑 Shutting down services...")
                await api_server.stop()
                await web_server.stop()
                click.echo("✅ Shutdown complete")

        asyncio.run(run_unified())

    except Exception as e:
        click.echo(f"❌ Failed to start server: {e}")
        raise click.Abort()


@server_group.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.pass_context
def api(ctx: Context, host: str, port: int, reload: bool):
    """Run API server only."""
    cli_context: CLIContext = ctx.obj

    click.echo(f"🚀 Starting API server on {host}:{port}")

    try:
        from ...api.unified_api import UnifiedAPIServer

        async def run_api():
            server = UnifiedAPIServer(host=host, port=port)
            try:
                await server.start()
            except KeyboardInterrupt:
                click.echo("\n🛑 Shutting down API server...")
                await server.stop()
                click.echo("✅ Shutdown complete")

        asyncio.run(run_api())

    except Exception as e:
        click.echo(f"❌ Failed to start API server: {e}")
        raise click.Abort()


@server_group.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8080, help="Port to bind to")
@click.option("--api-url", default="http://localhost:8000", help="API server URL")
@click.pass_context
def web(ctx: Context, host: str, port: int, api_url: str):
    """Run web interface only."""
    cli_context: CLIContext = ctx.obj

    click.echo(f"🚀 Starting web interface on {host}:{port}")
    click.echo(f"🔗 API URL: {api_url}")

    try:
        from ...web.static_server import StaticServer

        async def run_web():
            server = StaticServer(host=host, port=port, api_url=api_url)
            try:
                await server.start()
            except KeyboardInterrupt:
                click.echo("\n🛑 Shutting down web server...")
                await server.stop()
                click.echo("✅ Shutdown complete")

        asyncio.run(run_web())

    except Exception as e:
        click.echo(f"❌ Failed to start web server: {e}")
        raise click.Abort()
