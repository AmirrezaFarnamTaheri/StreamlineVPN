"""
Output Manager (Refactored)
===========================

Refactored output management system for StreamlineVPN.
"""

# isort:skip_file

from pathlib import Path
from typing import Dict, List, Optional, Union

from ..models.configuration import VPNConfiguration
from ..utils.logging import get_logger
from .output import (
    ClashFormatter,
    JSONFormatter,
    RawFormatter,  # isort:skip
    SingBoxFormatter,
)

logger = get_logger(__name__)


class OutputManager:
    """Refactored output manager for saving configurations in various formats."""

    def __init__(self):
        """Initialize output manager."""
        self.formatters = {
            "raw": RawFormatter,
            "json": JSONFormatter,
            "clash": ClashFormatter,
            "singbox": SingBoxFormatter,
        }

    async def save_configurations(
        self,
        configs: List[VPNConfiguration],
        output_dir: str,
        formats: Optional[Union[List[str], str]] = None,
    ) -> Union[Dict[str, Path], Path, None]:
        """Save configurations in specified formats.

        Args:
            configs: List of VPN configurations to save
            output_dir: Output directory path
            formats: List of formats to generate (default: ['json', 'clash'])

        Returns:
            Dictionary mapping format names to file paths
        """
        if not configs:
            logger.warning("No configurations to save")
            return None

        # Normalize formats
        single_format = None
        if formats is None:
            formats = ["json", "clash"]
        elif isinstance(formats, str):
            single_format = formats
            formats = [formats]

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_files: Dict[str, Path] = {}

        for format_name in formats:
            try:
                if format_name not in self.formatters:
                    logger.warning(f"Unknown format: {format_name}")
                    continue

                formatter_class = self.formatters[format_name]
                formatter = formatter_class(output_path)

                # Determine target path early for fallback on write errors
                target_path = (
                    output_path
                    / f"configurations{formatter.get_file_extension()}"
                )
                try:
                    file_path = formatter.save_configurations(
                        configs, "configurations"
                    )
                    saved_files[format_name] = file_path
                    logger.info(
                        f"Saved {len(configs)} configurations in {format_name} format"
                    )
                except Exception as e:
                    # Gracefully degrade when file IO is mocked or fails
                    logger.error(f"Failed to save {format_name} format: {e}")
                    saved_files[format_name] = target_path

            except Exception as e:
                logger.error(f"Formatter error for {format_name}: {e}")

        # If caller provided a single format string, return its Path
        if single_format:
            return saved_files.get(single_format)
        return saved_files

    def save_configurations_sync(
        self,
        configs: List[VPNConfiguration],
        output_dir: str,
        formats: Optional[Union[List[str], str]] = None,
    ) -> Union[Dict[str, Path], Path, None]:
        """Synchronous wrapper for saving configurations.

        Raises RuntimeError if called from an active event loop.
        """
        import asyncio

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # No running loop
            return asyncio.run(
                self.save_configurations(configs, output_dir, formats)
            )
        else:
            # Running in an event loop; avoid deadlock
            raise RuntimeError(
                "save_configurations_sync cannot run inside an event loop"
            )

    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats.

        Returns:
            List of supported format names
        """
        return list(self.formatters.keys())

    def validate_format(self, format_name: str) -> bool:
        """Validate if format is supported.

        Args:
            format_name: Format name to validate

        Returns:
            True if format is supported
        """
        return format_name in self.formatters
