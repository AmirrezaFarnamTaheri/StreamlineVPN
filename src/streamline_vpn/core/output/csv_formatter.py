from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from ...models.configuration import VPNConfiguration
from ...utils.logging import get_logger
from .base_formatter import BaseFormatter

logger = get_logger(__name__)


class CSVFormatter(BaseFormatter):
    """Formatter that writes configurations to a simple CSV file."""

    def __init__(self, output_dir: Path) -> None:
        super().__init__(output_dir)

    def get_file_extension(self) -> str:  # pragma: no cover - trivial
        return ".csv"

    def save_configurations(
        self, configs: List[VPNConfiguration], base_filename: str
    ) -> Path:
        path = self.output_dir / f"{base_filename}{self.get_file_extension()}"
        
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["protocol", "server", "port", "user_id", "password", "encryption", "network", "path", "host", "tls", "quality_score"])
                for cfg in configs:
                    config_dict = self._safe_config_to_dict(cfg)
                    writer.writerow([
                        config_dict.get("protocol", ""),
                        config_dict.get("server", ""),
                        config_dict.get("port", 0),
                        config_dict.get("user_id", ""),
                        config_dict.get("password", ""),
                        config_dict.get("encryption", ""),
                        config_dict.get("network", ""),
                        config_dict.get("path", ""),
                        config_dict.get("host", ""),
                        config_dict.get("tls", False),
                        config_dict.get("quality_score", 0.0)
                    ])
        except Exception as e:
            logger.error(f"Failed to save CSV configurations: {e}")
            raise
        
        return path
