from typing import Optional
from urllib.parse import urlparse, parse_qs

from ....models.configuration import VPNConfiguration, Protocol
from ....utils.logging import get_logger

logger = get_logger(__name__)


def parse_vless(config_string: str) -> Optional[VPNConfiguration]:
    try:
        parsed = urlparse(config_string)
        if parsed.scheme != "vless":
            return None

        q = parse_qs(parsed.query)
        return VPNConfiguration(
            protocol=Protocol.VLESS,
            server=parsed.hostname or "",
            port=parsed.port or 443,
            user_id=parsed.username or "",
            password="",
            encryption="none",
            network=q.get("type", ["tcp"])[0],
            path=q.get("path", [""])[0],
            host=q.get("host", [""])[0],
            tls=q.get("security", [""])[0] == "tls",
            metadata={"query": q},
        )
    except Exception as e:
        logger.debug("Failed to parse VLESS: %s", e)
        return None
