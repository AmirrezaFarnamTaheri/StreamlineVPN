from typing import Optional
import re
import base64

from ....models.configuration import VPNConfiguration, Protocol
from ....utils.logging import get_logger

logger = get_logger(__name__)


def parse_ssr(config_string: str) -> Optional[VPNConfiguration]:
    try:
        match = re.match(r"ssr://([A-Za-z0-9+/=]+)", config_string)
        if not match:
            return None

        encoded = match.group(1)
        pad = 4 - (len(encoded) % 4)
        if pad != 4:
            encoded += "=" * pad
        decoded = base64.b64decode(encoded).decode("utf-8")

        parts = decoded.split("/")
        if len(parts) < 1:
            return None
        main = parts[0]
        main_parts = main.split(":")
        if len(main_parts) < 6:
            return None
        server, port, protocol, method, obfs, password_b64 = main_parts[:6]

        pwd_pad = 4 - (len(password_b64) % 4)
        if pwd_pad != 4:
            password_b64 += "=" * pwd_pad
        password = base64.b64decode(password_b64).decode("utf-8")

        return VPNConfiguration(
            protocol=Protocol.SHADOWSOCKSR,
            server=server,
            port=int(port),
            user_id="",
            password=password,
            encryption=method,
            network=protocol,
            path="",
            host="",
            tls=False,
            metadata={"protocol": protocol, "obfs": obfs},
        )
    except Exception as e:
        logger.debug("Failed to parse SSR: %s", e)
        return None
