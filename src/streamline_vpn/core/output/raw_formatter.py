from __future__ import annotations

from pathlib import Path
from typing import List

from ...models.configuration import VPNConfiguration


class RawFormatter:
    """Formatter that writes configurations as raw strings."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def get_file_extension(self) -> str:
        """Return the file extension for raw output."""
        return ".txt"

    def save_configurations(
        self, configs: List[VPNConfiguration], base_filename: str
    ) -> Path:
        """Save configurations as plain text.

        Each configuration is written on a new line using its string representation.
        """
        file_path = (
            self.output_dir / f"{base_filename}{self.get_file_extension()}"
        )
        f = open(file_path, "w", encoding="utf-8")
        try:
            for config in configs:
                f.write(str(config) + "\n")
        finally:
            f.close()
        return file_path
