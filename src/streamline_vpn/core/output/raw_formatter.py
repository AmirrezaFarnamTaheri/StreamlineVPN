from __future__ import annotations

from pathlib import Path
from typing import List

from ...models.configuration import VPNConfiguration
from ...utils.logging import get_logger
from .base_formatter import BaseFormatter

logger = get_logger(__name__)


class RawFormatter(BaseFormatter):
    """Formatter that writes configurations as raw strings."""

    def __init__(self, output_dir: Path) -> None:
        super().__init__(output_dir)

    def get_file_extension(self) -> str:
        """Return the file extension for raw output."""
        return ".txt"

    def save_configurations(
        self, configs: List[VPNConfiguration], base_filename: str
    ) -> Path:
        """Save configurations as plain text."""
        file_path = (
            self.output_dir / f"{base_filename}{self.get_file_extension()}"
        )
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for config in configs:
                    f.write(str(config) + "\n")
        except Exception as e:
            logger.error(f"Failed to save raw configurations: {e}")
            raise
        
        return file_path
