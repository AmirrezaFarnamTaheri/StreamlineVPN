from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ...models.configuration import VPNConfiguration


class JSONFormatter:
    """Formatter that outputs configurations in JSON format."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def get_file_extension(self) -> str:
        """Return the file extension for JSON output."""
        return ".json"

    def save_configurations(self, configs: List[VPNConfiguration], base_filename: str) -> Path:
        """Serialize configurations to a JSON file."""
        file_path = self.output_dir / f"{base_filename}{self.get_file_extension()}"
        f = open(file_path, "w", encoding="utf-8")
        try:
            json.dump([cfg.to_dict() for cfg in configs], f, indent=2)
        finally:
            f.close()
        return file_path
