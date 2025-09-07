from __future__ import annotations

import base64
from pathlib import Path
from typing import List

from ...models.configuration import VPNConfiguration


class Base64Formatter:
    """Formatter that writes configurations as a Base64 encoded text file."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def get_file_extension(self) -> str:  # pragma: no cover - trivial
        return ".base64"

    def save_configurations(
        self, configs: List[VPNConfiguration], base_filename: str
    ) -> Path:
        joined = "\n".join(str(cfg) for cfg in configs)
        encoded = base64.b64encode(joined.encode("utf-8")).decode("utf-8")
        path = self.output_dir / f"{base_filename}{self.get_file_extension()}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded, encoding="utf-8")
        return path
