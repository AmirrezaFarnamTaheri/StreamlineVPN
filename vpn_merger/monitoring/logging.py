from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: Dict[str, Any] = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        # Merge extra dict if present
        extras = getattr(record, "_extra", None)
        if isinstance(extras, dict):
            payload.update(extras)
        return json.dumps(payload, ensure_ascii=False)


_configured = False


def get_logger(name: str = "vpn_merger", level: int = logging.INFO) -> logging.Logger:
    global _configured
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not _configured:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)
        root.setLevel(level)
        _configured = True
    return logger


def log_json(level: int, message: str, **extra: Any) -> None:
    logger = get_logger()
    record = logger.makeRecord(logger.name, level, fn="", lno=0, msg=message, args=(), exc_info=None)
    setattr(record, "_extra", extra or {})
    logger.handle(record)

