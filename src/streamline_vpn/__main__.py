"""
StreamlineVPN Command Line Interface
===================================

Main entry point for the StreamlineVPN application.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, List

import click

from .core.merger import StreamlineVPNMerger
from .utils.logging import setup_logging
from .settings import get_settings

logger = logging.getLogger(__name__)


@click.command()
@click.option("--config", default="config/sources.yaml", help="Path to sources config")
@click.option("--output", default="output", help="Output directory")
@click.option("--format", "formats", multiple=True, help="Output format(s). Can be repeated.")
def cli(config: str, output: str, formats: Optional[List[str]] = None):
    """StreamlineVPN runner"""
    asyncio.run(main(config, output, formats))


async def main(config: str, output: str, formats: Optional[List[str]] = None) -> int:
    """Main entry point for StreamlineVPN.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Setup logging
        setup_logging()

        # Load settings
        get_settings()

        # Create merger instance
        merger = StreamlineVPNMerger(config_path=config)
        
        # Process configurations
        logger.info("Starting StreamlineVPN processing...")
        results = await merger.process_all()
        
        # Save results
        output_dir = Path(output)
        output_dir.mkdir(exist_ok=True)
        await merger.save_results(str(output_dir), formats)
        
        logger.info(f"Processing completed successfully. Results saved to {output_dir}")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        return 1


def cli_main() -> int:
    """CLI entry point that handles async execution."""
    try:
        cli()
        return 0
    except KeyboardInterrupt:
        return 1
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(cli_main())
