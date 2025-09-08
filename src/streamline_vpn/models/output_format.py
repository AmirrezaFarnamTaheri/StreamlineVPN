from enum import Enum
from typing import List


class OutputFormat(str, Enum):
    """Supported output formats."""

    JSON = "json"
    CLASH = "clash"
    SINGBOX = "singbox"
    BASE64 = "base64"
    CSV = "csv"
    RAW = "raw"

    @classmethod
    def list(cls) -> List[str]:
        """Return all supported format values."""
        return [fmt.value for fmt in cls]
