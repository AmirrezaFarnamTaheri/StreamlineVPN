"""
StreamlineVPN Command Line Interface
===================================

Main entry point for the StreamlineVPN application.
"""

import asyncio
import logging
import sys
from typing import List, Optional

import click

from .core.merger import StreamlineVPNMerger
from .settings import get_settings
from .utils.logging import setup_logging

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--config", default="config/sources.yaml", help="Path to sources config"
)
@click.option("--output", default="output", help="Output directory")
@click.option(
    "--format",
    "formats",
    multiple=True,
    help="Output format(s). Can be repeated.",
)
def cli(config: str, output: str, formats: Optional[tuple[str, ...]] = None):
    """StreamlineVPN runner"""
    formats_list = list(formats) if formats else None
    # Always create and use a fresh event loop for CLI execution
    return asyncio.run(main(config, output, formats_list))


async def main(
    config: str, output: str, formats: Optional[List[str]] = None
) -> int:
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
        await merger.initialize()

        # Process configurations and save results (handled inside process_all)
        logger.info("Starting StreamlineVPN processing...")
        await merger.process_all(output_dir=output, formats=formats)

        logger.info(
            f"Processing completed successfully. Results saved to {output}"
        )
        return 0

    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        return 1
    except Exception as e:
        logger.error("Processing failed: %s", e, exc_info=True)
        return 1


def cli_main() -> int:
    """CLI entry point that handles async execution."""
    try:
        # Run click command without auto SystemExit to capture exit code
        # type: ignore[attr-defined]
        exit_code = cli.main(standalone_mode=False)
        return int(exit_code) if isinstance(exit_code, int) else 0
    except SystemExit as e:
        # Click may raise SystemExit with code
        return int(e.code) if hasattr(e, "code") else 1
    except KeyboardInterrupt:
        return 1
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(cli_main())
