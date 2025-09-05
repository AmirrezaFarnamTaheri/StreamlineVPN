from typing import Optional
from urllib.parse import urlparse

from ....models.configuration import VPNConfiguration, Protocol
from ....utils.logging import get_logger

logger = get_logger(__name__)


def parse_trojan(config_string: str) -> Optional[VPNConfiguration]:
    try:
        parsed = urlparse(config_string)
        if parsed.scheme != "trojan":
            return None
        return VPNConfiguration(
            protocol=Protocol.TROJAN,
            server=parsed.hostname or "",
            port=parsed.port or 443,
            user_id="",
            password=parsed.username or "",
            encryption="",
            network="tcp",
            path="",
            host="",
            tls=True,
            metadata={"fragment": parsed.fragment},
        )
    except Exception as e:
        logger.debug(f"Failed to parse Trojan: {e}")
        return None

