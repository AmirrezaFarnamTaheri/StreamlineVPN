from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ...models.configuration import VPNConfiguration


class SingBoxFormatter:
    """Formatter that outputs configurations in a minimal Sing-box JSON structure."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def get_file_extension(self) -> str:
        """Return the file extension for Sing-box output."""
        return ".json"

    def save_configurations(self, configs: List[VPNConfiguration], base_filename: str) -> Path:
        """Save configurations in a simple Sing-box format."""
        file_path = self.output_dir / f"{base_filename}{self.get_file_extension()}"
        f = open(file_path, "w", encoding="utf-8")
        try:
            data = {
                "outbounds": [cfg.to_dict() for cfg in configs]
            }
            json.dump(data, f, indent=2)
        finally:
            f.close()
        return file_path
