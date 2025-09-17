import re
from typing import List
from ....settings import get_settings


def _defaults() -> List[str]:
    return get_settings().security.suspicious_text_patterns


def find_suspicious_patterns(text: str, patterns: List[str] | None = None) -> List[str]:
    patterns = patterns or _defaults()
    found: List[str] = []
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            found.append(p)
    return found
