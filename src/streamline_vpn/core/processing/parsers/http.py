from typing import Optional
import re
from urllib.parse import urlparse, unquote

from ....models.configuration import VPNConfiguration, Protocol
from ....utils.logging import get_logger

logger = get_logger(__name__)


def parse_http(config_string: str) -> Optional[VPNConfiguration]:
    """
    Parses an HTTP proxy URL into a VPNConfiguration object.
    Supports formats like:
    http://host:port
    http://user:pass@host:port
    """
    try:
        if not config_string.startswith("http://"):
            return None

        parsed_url = urlparse(config_string)
        if not parsed_url.hostname or not parsed_url.port:
            return None

        username = unquote(parsed_url.username) if parsed_url.username else ""
        password = unquote(parsed_url.password) if parsed_url.password else ""

        return VPNConfiguration(
            protocol=Protocol.HTTP,
            server=parsed_url.hostname,
            port=parsed_url.port,
            user_id=username,
            password=password,
            metadata={"raw_url": config_string},
        )
    except Exception as e:
        logger.debug("Failed to parse HTTP proxy: %s", e)
        return None
