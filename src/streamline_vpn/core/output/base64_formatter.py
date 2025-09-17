from __future__ import annotations

import base64
from pathlib import Path
from typing import List

from ...models.configuration import VPNConfiguration
from ...utils.logging import get_logger
from .base_formatter import BaseFormatter

logger = get_logger(__name__)


class Base64Formatter(BaseFormatter):
    """Formatter that writes configurations as a Base64 encoded text file."""

    def __init__(self, output_dir: Path) -> None:
        super().__init__(output_dir)

    def get_file_extension(self) -> str:  # pragma: no cover - trivial
        return ".base64"

    def save_configurations(
        self, configs: List[VPNConfiguration], base_filename: str
    ) -> Path:
        try:
            joined = "\n".join(str(cfg) for cfg in configs)
            encoded = base64.b64encode(joined.encode("utf-8")).decode("utf-8")
            path = self.output_dir / f"{base_filename}{self.get_file_extension()}"
            path.write_text(encoded, encoding="utf-8")
        except Exception as e:
            logger.error("Failed to save Base64 configurations: %s", e)
            raise

        return path
