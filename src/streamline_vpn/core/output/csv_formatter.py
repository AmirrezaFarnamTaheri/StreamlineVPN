from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from ...models.configuration import VPNConfiguration


class CSVFormatter:
    """Formatter that writes configurations to a simple CSV file."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def get_file_extension(self) -> str:  # pragma: no cover - trivial
        return ".csv"

    def save_configurations(
        self, configs: List[VPNConfiguration], base_filename: str
    ) -> Path:
        path = self.output_dir / f"{base_filename}{self.get_file_extension()}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["protocol", "server", "port"])
            for cfg in configs:
                writer.writerow([cfg.protocol.value, cfg.server, cfg.port])
        return path
