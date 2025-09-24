from typing import Optional
import re
from urllib.parse import urlparse, unquote

from ....models.configuration import VPNConfiguration, Protocol
from ....utils.logging import get_logger

logger = get_logger(__name__)


def parse_socks5(config_string: str) -> Optional[VPNConfiguration]:
    """
    Parses a SOCKS5 proxy URL into a VPNConfiguration object.
    Supports formats like:
    socks5://host:port
    socks5://user:pass@host:port
    """
    try:
        if not config_string.startswith("socks5://"):
            return None

        parsed_url = urlparse(config_string)
        if not parsed_url.hostname or not parsed_url.port:
            return None

        username = unquote(parsed_url.username) if parsed_url.username else ""
        password = unquote(parsed_url.password) if parsed_url.password else ""

        return VPNConfiguration(
            protocol=Protocol.SOCKS5,
            server=parsed_url.hostname,
            port=parsed_url.port,
            user_id=username,
            password=password,
            metadata={"raw_url": config_string},
        )
    except Exception as e:
        logger.debug("Failed to parse SOCKS5 proxy: %s", e)
        return None
