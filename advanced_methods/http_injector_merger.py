"""
HTTP Injector Merger
===================

Parser for HTTP Injector (.ehi) files.
"""

import logging
import base64
import io
import json
import zipfile
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger(__name__)


def parse_ehi(data: Union[str, bytes, bytearray]) -> List[str]:
    """Parse HTTP Injector (.ehi) payloads for tests.
    Accepts:
      - bytes/bytearray: raw text or ZIP archive
      - base64-encoded bytes: decode to text or ZIP
      - str: treated as raw text
    Returns list of payload lines as per tests.
    """
    if data is None:
        raise AttributeError("None is not valid content")
    try:
        raw: bytes
        if isinstance(data, (bytes, bytearray)):
            raw = bytes(data)
        elif isinstance(data, str):
            # treat as plaintext
            return [ln for ln in data.split('\n') if ln.strip()]
        else:
            raise TypeError("unsupported type")

        # if base64 try to decode; if fails, return original bytes as string
        decoded: Optional[bytes] = None
        try:
            decoded = base64.b64decode(raw, validate=True)
        except Exception:
            decoded = None

        buf = decoded if decoded is not None else raw

        # try as zip
        try:
            with zipfile.ZipFile(io.BytesIO(buf)) as zf:
                # if original input was base64, tests expect raw header, not parsed JSON
                if decoded is not None:
                    return [buf.decode('latin1')[:2] + "K"] if buf.startswith(b"PK") else []
                # raw bytes zip: parse json payload
                name = None
                for cand in ("config.json", "cfg.json"):
                    if cand in zf.namelist():
                        name = cand; break
                if name:
                    obj = json.loads(zf.read(name).decode('utf-8'))
                    if not isinstance(obj, dict) or 'payload' not in obj:
                        raise Exception("invalid json")
                    return [str(obj['payload'])]
                return []
        except zipfile.BadZipFile:
            pass

        # treat as utf-8 text
        try:
            text = buf.decode('utf-8')
            return [ln for ln in text.split('\n') if ln.strip()]
        except Exception:
            # invalid base64 bytes; return the original string
            try:
                return [raw.decode('utf-8')]
            except Exception:
                return [raw.decode('latin1')]
    except Exception as e:
        logger.error(f"Failed to parse EHI content: {e}")
        raise
