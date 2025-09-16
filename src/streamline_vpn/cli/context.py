"""
Shared CLI context utilities.
"""

import logging
from pathlib import Path
from typing import Optional

import click
import inspect

# Expose these for tests to patch at module level
from ..core.merger import StreamlineVPNMerger  # type: ignore
from ..core.source.manager import SourceManager  # type: ignore


class CLIContext:
    """CLI context for sharing state between commands."""

    def __init__(self):
        self.verbose: bool = False
        self.config_path: Optional[Path] = None
        self.output_path: Optional[Path] = None
        self.dry_run: bool = False

    def setup_logging(self, verbose: bool = False) -> None:
        """Setup logging configuration."""
        self.verbose = verbose
        level = logging.DEBUG if verbose else logging.INFO

        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('streamline_vpn.log')
            ]
        )

    async def process_configurations(
        self,
        formats: str = "all",
        max_concurrent: int = 5,
        timeout: int = 30,
        force_refresh: bool = False,
    ) -> bool:
        """Process VPN configurations."""
        try:
            source_manager = SourceManager()
            merger = StreamlineVPNMerger()

            sources_result = source_manager.get_all_sources()
            sources = await sources_result if inspect.isawaitable(sources_result) else sources_result
            if not sources:
                click.echo("❌ No sources found. Add sources first.")
                return False

            process_result = merger.process_sources(
                sources=sources,
                formats=formats.split(','),
                max_concurrent=max_concurrent,
                timeout=timeout,
                force_refresh=force_refresh,
            )
            results = await process_result if inspect.isawaitable(process_result) else process_result

            click.echo(f"✅ Processed {len(results)} configurations")
            return True

        except Exception as e:
            click.echo(f"❌ Error processing configurations: {e}")
            return False


