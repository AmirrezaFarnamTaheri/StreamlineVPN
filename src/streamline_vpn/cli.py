#!/usr/bin/env python3
"""
StreamlineVPN CLI - Command Line Interface
"""

import click
import asyncio
from pathlib import Path

@click.group()
def cli():
    """StreamlineVPN Command Line Interface"""
    pass

@cli.command()
def version():
    """Show version information"""
    click.echo("StreamlineVPN CLI v2.0.0")

if __name__ == "__main__":
    cli()
