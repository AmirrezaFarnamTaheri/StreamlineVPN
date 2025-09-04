"""
Utilities for SourceManager: URL validation and extraction helpers.
"""

from __future__ import annotations

import logging
from typing import Any, List

logger = logging.getLogger(__name__)


def is_valid_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if not url:
        return False
    return any(url.startswith(s) for s in ("http://", "https://"))


def extract_urls_from_dict(data: dict, depth: int = 0) -> List[str]:
    if depth > 5:
        logger.warning("Maximum recursion depth reached while extracting URLs")
        return []
    urls: List[str] = []
    for key, value in data.items():
        if key == "urls" and isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    if is_valid_url(item):
                        urls.append(item)
                elif isinstance(item, dict) and "url" in item:
                    u = item["url"]
                    if is_valid_url(u):
                        urls.append(u)
        elif isinstance(value, dict):
            urls.extend(extract_urls_from_dict(value, depth + 1))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str) and is_valid_url(item):
                    urls.append(item)
    return urls


def extract_urls_from_category(category_data: Any) -> List[str]:
    urls: List[str] = []
    if isinstance(category_data, dict) and "urls" in category_data:
        for url_data in category_data["urls"]:
            if isinstance(url_data, dict) and "url" in url_data:
                u = url_data["url"]
                if is_valid_url(u):
                    urls.append(u)
    elif isinstance(category_data, list):
        urls.extend([u for u in category_data if is_valid_url(u)])
    elif isinstance(category_data, dict):
        for _, value in category_data.items():
            if isinstance(value, dict) and "urls" in value:
                for url_data in value["urls"]:
                    if isinstance(url_data, dict) and "url" in url_data:
                        u = url_data["url"]
                        if is_valid_url(u):
                            urls.append(u)
    return urls


def get_minimal_fallback_sources() -> dict[str, list[str]]:
    logger.warning("Using minimal fallback sources - please configure sources.unified.yaml")
    return {
        "emergency_fallback": [
            "https://httpbin.org/json",
            "https://example.org/",
        ]
    }

