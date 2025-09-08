from enum import Enum


class OutputFormat(str, Enum):
    """Supported output formats for pipeline results."""

    RAW = "raw"
    BASE64 = "base64"
    JSON = "json"
    CSV = "csv"
    CLASH = "clash"
    SINGBOX = "singbox"
