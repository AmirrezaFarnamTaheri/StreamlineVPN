from typing import Optional
import re
import base64

from ....models.configuration import VPNConfiguration, Protocol
from ....utils.logging import get_logger

logger = get_logger(__name__)


def parse_ss(config_string: str) -> Optional[VPNConfiguration]:
    try:
        match = re.match(r"ss://([A-Za-z0-9+/=]+)", config_string)
        if not match:
            return None

        encoded = match.group(1)
        padding = 4 - (len(encoded) % 4)
        if padding != 4:
            encoded += "=" * padding
        decoded = base64.b64decode(encoded).decode("utf-8")

        if "@" in decoded:
            auth_part, server_part = decoded.split("@", 1)
            method, password = auth_part.split(":", 1)
            server, port = server_part.split(":", 1)
        else:
            parts = decoded.split(":")
            if len(parts) >= 4:
                method, password, server, port = parts[:4]
            else:
                return None

        return VPNConfiguration(
            protocol=Protocol.SHADOWSOCKS,
            server=server,
            port=int(port),
            user_id="",
            password=password,
            encryption=method,
            network="tcp",
            path="",
            host="",
            tls=False,
            metadata={"method": method},
        )
    except Exception as e:
        logger.debug(f"Failed to parse Shadowsocks: {e}")
        return None
