from typing import Optional
from urllib.parse import urlparse, parse_qs, unquote

from ....models.configuration import VPNConfiguration, Protocol
from ....utils.logging import get_logger

logger = get_logger(__name__)


def parse_tuic(config_string: str) -> Optional[VPNConfiguration]:
    """
    Parses a TUIC URL into a VPNConfiguration object.
    Example: tuic://uuid:password@host:port?congestion_control=bbr&...
    """
    try:
        if not config_string.startswith("tuic://"):
            return None

        parsed_url = urlparse(config_string)
        if not parsed_url.hostname or not parsed_url.port:
            return None

        uuid = parsed_url.username or ""
        password = parsed_url.password or ""

        # Extract parameters from the query string
        params = parse_qs(parsed_url.query)
        metadata = {k: v[0] for k, v in params.items()}
        metadata["raw_url"] = config_string

        return VPNConfiguration(
            protocol=Protocol.TUIC,
            server=parsed_url.hostname,
            port=parsed_url.port,
            uuid=uuid,
            password=password,
            metadata=metadata,
        )
    except Exception as e:
        logger.debug("Failed to parse TUIC: %s", e)
        return None
