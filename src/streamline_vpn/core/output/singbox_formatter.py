from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ...models.configuration import VPNConfiguration
from ...utils.logging import get_logger
from .base_formatter import BaseFormatter

logger = get_logger(__name__)


class SingBoxFormatter(BaseFormatter):
    """Formatter for Sing-box JSON output."""

    def __init__(self, output_dir: Path) -> None:
        super().__init__(output_dir)

    def get_file_extension(self) -> str:
        """Return the file extension for Sing-box output."""
        return ".json"

    def save_configurations(
        self, configs: List[VPNConfiguration], base_filename: str
    ) -> Path:
        """Save configurations in a simple Sing-box format."""
        file_path = (
            self.output_dir / f"{base_filename}{self.get_file_extension()}"
        )
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                data = {"outbounds": [self._safe_config_to_dict(cfg) for cfg in configs]}
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("Failed to save SingBox configurations: %s", e)
            raise
        
        return file_path
