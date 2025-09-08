from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ...models.configuration import VPNConfiguration
from ...utils.logging import get_logger
from .base_formatter import BaseFormatter

logger = get_logger(__name__)


class ClashFormatter(BaseFormatter):
    """Formatter for Clash YAML output."""

    def __init__(self, output_dir: Path) -> None:
        super().__init__(output_dir)

    def get_file_extension(self) -> str:
        """Return the file extension for Clash YAML output."""
        return ".yaml"

    def save_configurations(
        self, configs: List[VPNConfiguration], base_filename: str
    ) -> Path:
        """Save configurations in a basic YAML-like format.

        This implementation intentionally avoids external YAML dependencies.
        """
        file_path = (
            self.output_dir / f"{base_filename}{self.get_file_extension()}"
        )
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("proxies:\n")
                for cfg in configs:
                    config_dict = self._safe_config_to_dict(cfg)
                    f.write(f"  - {json.dumps(config_dict, ensure_ascii=False)}\n")
        except Exception as e:
            logger.error(f"Failed to save Clash configurations: {e}")
            raise
        
        return file_path
