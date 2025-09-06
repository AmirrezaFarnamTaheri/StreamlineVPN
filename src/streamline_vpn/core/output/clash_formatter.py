from __future__ import annotations

from pathlib import Path
from typing import List

from ...models.configuration import VPNConfiguration


class ClashFormatter:
    """Formatter that outputs configurations in a simple YAML structure for Clash."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def get_file_extension(self) -> str:
        """Return the file extension for Clash YAML output."""
        return ".yaml"

    def save_configurations(self, configs: List[VPNConfiguration], base_filename: str) -> Path:
        """Save configurations in a basic YAML-like format.

        This implementation intentionally avoids external YAML dependencies.
        """
        file_path = self.output_dir / f"{base_filename}{self.get_file_extension()}"
        f = open(file_path, "w", encoding="utf-8")
        try:
            f.write("proxies:\n")
            for cfg in configs:
                f.write(f"  - {cfg.to_dict()}\n")
        finally:
            f.close()
        return file_path
