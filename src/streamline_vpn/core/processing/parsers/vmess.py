from typing import Optional
import re
import base64
import json

from ....models.configuration import VPNConfiguration, Protocol
from ....utils.logging import get_logger

logger = get_logger(__name__)


def parse_vmess(config_string: str) -> Optional[VPNConfiguration]:
    try:
        match = re.match(r"vmess://([A-Za-z0-9+/=]+)", config_string)
        if not match:
            return None

        encoded_data = match.group(1)
        padding = 4 - (len(encoded_data) % 4)
        if padding != 4:
            encoded_data += "=" * padding

        decoded_data = base64.b64decode(encoded_data).decode("utf-8")
        cfg = json.loads(decoded_data)

        return VPNConfiguration(
            protocol=Protocol.VMESS,
            server=cfg.get("add", ""),
            port=int(cfg.get("port", 0)),
            user_id=cfg.get("id", ""),
            password="",
            encryption=cfg.get("scy", "auto"),
            network=cfg.get("net", "tcp"),
            path=cfg.get("path", ""),
            host=cfg.get("host", ""),
            tls=cfg.get("tls") == "tls",
            metadata=cfg,
        )
    except Exception as e:
        logger.debug(f"Failed to parse VMess: {e}")
        return None
